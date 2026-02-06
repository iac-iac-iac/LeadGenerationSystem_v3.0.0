import pandas as pd
from collections import Counter


class Analytics:
    """Анализ результатов из Битрикс24"""

    def __init__(self):
        self.lead_df = None
        self.deal_df = None
        self.metrics = {}

    def load_bitrix_exports(self, lead_csv_path, deal_csv_path):
        """Загрузка экспортов из Битрикс"""
        try:
            for sep in [',', ';', '\t']:
                try:
                    self.lead_df = pd.read_csv(
                        lead_csv_path, sep=sep, encoding='utf-8', low_memory=False)
                    if len(self.lead_df.columns) > 5:
                        break
                except:
                    continue

            if self.lead_df is None or len(self.lead_df.columns) <= 1:
                self.lead_df = pd.read_csv(
                    lead_csv_path, encoding='utf-8-sig', low_memory=False)

            print(
                f"✅ LEAD загружен: {len(self.lead_df)} строк, {len(self.lead_df.columns)} колонок")
            print(f"📋 ВСЕ колонки LEAD:")
            for idx, col in enumerate(self.lead_df.columns, 1):
                print(f"   {idx}. {col}")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки LEAD: {e}")
            self.lead_df = pd.DataFrame()

        try:
            for sep in [',', ';', '\t']:
                try:
                    self.deal_df = pd.read_csv(
                        deal_csv_path, sep=sep, encoding='utf-8', low_memory=False)
                    if len(self.deal_df.columns) > 5:
                        break
                except:
                    continue

            if self.deal_df is None or len(self.deal_df.columns) <= 1:
                self.deal_df = pd.read_csv(
                    deal_csv_path, encoding='utf-8-sig', low_memory=False)

            print(
                f"\n✅ DEAL загружен: {len(self.deal_df)} строк, {len(self.deal_df.columns)} колонок")
            print(f"📋 ВСЕ колонки DEAL:")
            for idx, col in enumerate(self.deal_df.columns, 1):
                print(f"   {idx}. {col}")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки DEAL: {e}")
            self.deal_df = pd.DataFrame()

    def filter_my_leads(self):
        """Фильтрация только 'моих' лидов по колонке 'Источник телефона'"""

        # Ищем колонку точно по имени
        source_col_lead = None
        source_col_deal = None

        # Проверка всех возможных вариантов названия
        possible_names = [
            'Источник телефона',
            'Источник телефона (Лид)',
            'Phone Source',
            'Lead Source File',
            'Source File'
        ]

        # Поиск в LEAD
        for col in self.lead_df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                source_col_lead = col
                break

        # Поиск в DEAL
        for col in self.deal_df.columns:
            if any(name.lower() in col.lower() for name in possible_names):
                source_col_deal = col
                break

        print(f"\n🔍 Поиск колонки 'Источник телефона':")
        print(
            f"   LEAD: {source_col_lead if source_col_lead else '❌ НЕ НАЙДЕНА'}")
        print(
            f"   DEAL: {source_col_deal if source_col_deal else '❌ НЕ НАЙДЕНА'}")

        initial_lead = len(self.lead_df)
        initial_deal = len(self.deal_df)

        # Фильтрация LEAD
        if source_col_lead:
            # Показываем примеры значений
            print(f"\n   Примеры значений в '{source_col_lead}' (LEAD):")
            sample_values = self.lead_df[source_col_lead].dropna().unique()[:5]
            for val in sample_values:
                print(f"      - {val}")

            # Фильтруем по .csv
            self.lead_df = self.lead_df[
                self.lead_df[source_col_lead].astype(
                    str).str.contains('.csv', case=False, na=False)
            ]
            print(f"\n   ✅ LEAD: {initial_lead} → {len(self.lead_df)}")
        else:
            print(f"\n   ⚠️  РЕШЕНИЕ: Анализируем ВСЕ лиды в LEAD (колонка не найдена)")
            # Не фильтруем, анализируем все

        # Фильтрация DEAL
        if source_col_deal:
            print(f"\n   Примеры значений в '{source_col_deal}' (DEAL):")
            sample_values = self.deal_df[source_col_deal].dropna().unique()[:5]
            for val in sample_values:
                print(f"      - {val}")

            self.deal_df = self.deal_df[
                self.deal_df[source_col_deal].astype(
                    str).str.contains('.csv', case=False, na=False)
            ]
            print(f"\n   ✅ DEAL: {initial_deal} → {len(self.deal_df)}")
        else:
            print(f"\n   ⚠️  РЕШЕНИЕ: Анализируем ВСЕ сделки в DEAL (колонка не найдена)")

    def calculate_metrics(self):
        """Подсчёт всех метрик"""

        # 1. Всего загружено лидов
        total_leads = len(self.lead_df) + len(self.deal_df)
        self.metrics['total_leads'] = total_leads

        print(f"\n📊 ПОДСЧЁТ МЕТРИК:")
        print(
            f"   Всего записей: {total_leads} (LEAD: {len(self.lead_df)}, DEAL: {len(self.deal_df)})")

        # 2. Отказы (ищем любую колонку с "отказ" или "причина")
        rejection_col = None
        for col in self.lead_df.columns:
            if 'отказ' in col.lower() or 'причина' in col.lower() or 'reason' in col.lower():
                rejection_col = col
                break

        if not self.lead_df.empty and rejection_col:
            rejection_reasons = self.lead_df[rejection_col].dropna()
            rejection_reasons = rejection_reasons[rejection_reasons != '']

            reason_counts = Counter(rejection_reasons)
            self.metrics['rejection_reasons'] = dict(reason_counts)
            self.metrics['total_rejections'] = len(rejection_reasons)

            print(
                f"   ✅ Причины отказа: найдена колонка '{rejection_col}' ({len(rejection_reasons)} записей)")
        else:
            self.metrics['rejection_reasons'] = {}
            self.metrics['total_rejections'] = 0
            print(f"   ⚠️  Причины отказа: колонка не найдена")

        # 3. В работе (DEAL) - ищем колонку со "стадия"
        deal_stage_col = None
        for col in self.deal_df.columns:
            if 'стадия' in col.lower() or 'stage' in col.lower():
                deal_stage_col = col
                break

        if not self.deal_df.empty and deal_stage_col:
            stage_counts = self.deal_df[deal_stage_col].value_counts(
            ).to_dict()
            self.metrics['deal_stages'] = stage_counts
            self.metrics['total_deals'] = len(self.deal_df)

            print(
                f"   ✅ Стадии сделок: найдена колонка '{deal_stage_col}' ({len(self.deal_df)} записей)")
            print(f"      Стадии: {list(stage_counts.keys())[:3]}...")
        else:
            self.metrics['deal_stages'] = {}
            self.metrics['total_deals'] = 0
            print(f"   ⚠️  Стадии сделок: колонка не найдена")

        # 4. Успешные продажи
        successful_deals = 0
        if not self.deal_df.empty and deal_stage_col:
            success_keywords = ['успешно', 'реализовано',
                                'выигран', 'won', 'success', 'closed']
            for keyword in success_keywords:
                count = len(self.deal_df[
                    self.deal_df[deal_stage_col].astype(
                        str).str.contains(keyword, case=False, na=False)
                ])
                if count > 0:
                    successful_deals += count
                    print(f"      - Найдено '{keyword}': {count} сделок")

        self.metrics['successful_deals'] = successful_deals
        print(f"   ✅ Успешных продаж: {successful_deals}")

        # 5. Конверсия
        if total_leads > 0:
            conversion = (
                (self.metrics['total_deals'] + successful_deals) / total_leads) * 100
            self.metrics['conversion'] = round(conversion, 2)
        else:
            self.metrics['conversion'] = 0.0

        print(f"   ✅ Конверсия: {self.metrics['conversion']}%")

        # 6. Топ-менеджеры
        manager_col = None
        for col in self.deal_df.columns:
            if 'ответственный' in col.lower() or 'responsible' in col.lower() or 'manager' in col.lower():
                manager_col = col
                break

        if not self.deal_df.empty and manager_col:
            manager_counts = self.deal_df[manager_col].value_counts().head(
                3).to_dict()
            self.metrics['top_managers'] = manager_counts
            print(f"   ✅ Менеджеры: найдена колонка '{manager_col}'")
            print(f"      Топ-3: {list(manager_counts.keys())}")
        else:
            self.metrics['top_managers'] = {}
            print(f"   ⚠️  Менеджеры: колонка не найдена")

        return self.metrics

    def get_report_summary(self):
        """Получение текстовой сводки для отчёта"""
        summary = f"""
=== ОТЧЁТ ПО ЛИДОГЕНЕРАЦИИ ===

1. ОБЩАЯ СТАТИСТИКА
   - Всего записей: {self.metrics.get('total_leads', 0)}
   - В работе (DEAL): {self.metrics.get('total_deals', 0)} сделок
   - Отказы (LEAD): {self.metrics.get('total_rejections', 0)} лидов
   - Успешные продажи: {self.metrics.get('successful_deals', 0)} сделок
   - Конверсия: {self.metrics.get('conversion', 0)}%

2. ПРИЧИНЫ ОТКАЗА
"""

        rejection_reasons = self.metrics.get('rejection_reasons', {})
        if rejection_reasons:
            total_rejections = self.metrics.get('total_rejections', 1)
            for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_rejections) * 100
                summary += f"   - {reason}: {count} ({percentage:.1f}%)\n"
        else:
            summary += "   - Нет данных\n"

        summary += "\n3. ТОП-МЕНЕДЖЕРЫ\n"

        top_managers = self.metrics.get('top_managers', {})
        if top_managers:
            for idx, (manager, count) in enumerate(top_managers.items(), 1):
                summary += f"   {idx}. {manager}: {count} сделок\n"
        else:
            summary += "   - Нет данных\n"

        return summary
