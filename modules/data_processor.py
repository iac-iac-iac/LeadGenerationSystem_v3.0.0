import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from modules.bitrix_mapper import BitrixMapper
from modules.phone_validator import PhoneValidator


class DataProcessor:
    """Основной процессор для обработки CSV файлов"""

    def __init__(self):
        self.stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'duplicates_removed': 0,
            'invalid_phones': 0,
            'files_processed': 0
        }

    def read_csv(self, file_path):
        """
        Чтение CSV с автоопределением разделителя
        Args:
            file_path: Путь к CSV файлу
        Returns:
            pandas DataFrame
        """
        # Список разделителей для проверки
        separators = [('\t', 'TAB'), (',', 'запятая'),
                      (';', 'точка с запятой'), ('|', 'вертикальная черта')]

        for sep, sep_name in separators:
            try:
                # ИЗМЕНЕНО: Читаем без dtype, затем обработаем
                df = pd.read_csv(
                    file_path,
                    sep=sep,
                    encoding='utf-8',
                    on_bad_lines='skip',
                    engine='python'
                )

                # Проверяем что файл прочитан правильно
                if len(df.columns) > 1:
                    print(f"✅ Файл прочитан с разделителем: {sep_name}")
                    print(f"📊 Найдено колонок: {len(df.columns)}")

                    # НОВОЕ: Конвертируем phone колонки в строки с обработкой float
                    phone_cols = [
                        col for col in df.columns if 'phone' in col.lower()]
                    for col in phone_cols:
                        # Конвертируем float в строку без научной нотации
                        df[col] = df[col].apply(lambda x: f"{x:.0f}" if pd.notna(x) and isinstance(
                            x, (int, float)) else str(x) if pd.notna(x) else None)

                    return df
            except Exception as e:
                continue

        # Если ни один разделитель не сработал, пробуем с автоопределением
        try:
            df = pd.read_csv(
                file_path,
                sep=None,
                encoding='utf-8',
                on_bad_lines='skip',
                engine='python'
            )

            if len(df.columns) > 1:
                print(f"✅ Файл прочитан с автоопределением разделителя")
                print(f"📊 Найдено колонок: {len(df.columns)}")

                # Конвертируем phone колонки
                phone_cols = [
                    col for col in df.columns if 'phone' in col.lower()]
                for col in phone_cols:
                    df[col] = df[col].apply(lambda x: f"{x:.0f}" if pd.notna(x) and isinstance(
                        x, (int, float)) else str(x) if pd.notna(x) else None)

                return df
        except Exception as e:
            pass

        # Последняя попытка
        try:
            df = pd.read_csv(
                file_path,
                encoding='utf-8-sig',
                on_bad_lines='skip',
                engine='python'
            )
            print(f"⚠️ Файл прочитан, но может быть неправильная структура")
            print(f"📊 Найдено колонок: {len(df.columns)}")

            # Конвертируем phone колонки
            phone_cols = [col for col in df.columns if 'phone' in col.lower()]
            for col in phone_cols:
                df[col] = df[col].apply(lambda x: f"{x:.0f}" if pd.notna(x) and isinstance(
                    x, (int, float)) else str(x) if pd.notna(x) else None)

            return df
        except Exception as e:
            print(f"❌ Ошибка чтения файла {file_path}: {e}")
            return None

    def extract_phone_columns(self, df):
        """
        Извлечение телефонов из всех колонок phone_* в две основные: phone_1 и phone_2
        Args:
            df: pandas DataFrame
        Returns:
            pandas DataFrame с колонками phone_1 и phone_2
        """
        # ДИАГНОСТИКА: Проверяем структуру файла
        print(f"\n🔍 Всего колонок в файле: {len(df.columns)}")

        # Если всего одна колонка - файл прочитан неправильно!
        if len(df.columns) == 1:
            print("❌ ОШИБКА: Файл прочитан как одна колонка!")
            print(f"   Название колонки: {df.columns[0][:100]}...")
            print("   Это означает что разделитель определен неправильно.")
            df['phone_1'] = None
            df['phone_2'] = None
            return df

        # Показываем первые 10 колонок для проверки
        print(f"📋 Первые колонки: {', '.join(df.columns[:10].tolist())}")
        if len(df.columns) > 10:
            print(f"   ... и еще {len(df.columns) - 10} колонок")

        # Находим все колонки, начинающиеся с 'phone' (без учета регистра)
        phone_columns = [
            col for col in df.columns if 'phone' in col.lower() or 'телефон' in col.lower()]

        if not phone_columns:
            print("⚠️ Не найдено колонок с телефонами")
            df['phone_1'] = None
            df['phone_2'] = None
            return df

        print(f"\n📞 Найдено {len(phone_columns)} колонок с телефонами")
        if len(phone_columns) <= 10:
            for col in phone_columns:
                print(f"   • {col}")
        else:
            for col in phone_columns[:10]:
                print(f"   • {col}")
            print(f"   ... и еще {len(phone_columns) - 10} колонок")

        def extract_phones_from_row(row):
            """Извлечение всех валидных телефонов из строки"""
            phones = []

            for col in phone_columns:
                value = row[col]

                # Пропускаем пустые значения
                if pd.isna(value) or value == '' or str(value) == 'nan':
                    continue

                # Конвертируем в строку
                value_str = str(value)

                # Разбиваем по запятой (если несколько телефонов в одной ячейке)
                parts = value_str.split(',')

                for part in parts:
                    part = part.strip()

                    # Валидируем и очищаем телефон
                    cleaned = PhoneValidator.clean_phone(part)

                    if cleaned and cleaned not in phones:
                        phones.append(cleaned)

            return phones

        # Извлекаем все телефоны для каждой строки
        all_phones = df.apply(extract_phones_from_row, axis=1)

        # ИСПРАВЛЕНО: Сначала удаляем старые phone_* колонки
        df = df.drop(columns=phone_columns, errors='ignore')

        # ЗАТЕМ создаем новые phone_1 и phone_2
        df['phone_1'] = all_phones.apply(
            lambda x: x[0] if len(x) > 0 else None)
        df['phone_2'] = all_phones.apply(
            lambda x: x[1] if len(x) > 1 else None)

        valid_phone1 = df['phone_1'].notna().sum()
        valid_phone2 = df['phone_2'].notna().sum()

        print(f"✅ Извлечено: phone_1={valid_phone1}, phone_2={valid_phone2}")

        return df

    def remove_unnecessary_columns(self, df):
        """
        Удаление ненужных колонок и переименование для совместимости
        Args:
            df: pandas DataFrame
        Returns:
            pandas DataFrame с нужными колонками
        """
        # СНАЧАЛА переименовываем колонки (если есть)
        rename_map = {
            'title': 'Название',
            'address': 'Адрес'
        }

        # Переименовываем только существующие колонки
        existing_renames = {k: v for k,
                            v in rename_map.items() if k in df.columns}
        if existing_renames:
            df = df.rename(columns=existing_renames)
            print(f"✏️ Переименованы колонки: {list(existing_renames.keys())}")

        # Колонки, которые нужно оставить
        keep_columns = [
            'Название',      # Переименованная из title
            'Адрес',         # Переименованная из address
            'phone_1',
            'phone_2',
            'Category 0',    # Категория бизнеса
            'companyUrl',    # Сайт
            'telegram',      # Telegram
            'vkontakte',     # ВКонтакте
            'whatsapp',      # WhatsApp
            'viber',         # Viber
            'rating',        # Рейтинг
            'ratingCount'    # Количество отзывов
        ]

        # Фильтрация: оставляем только существующие колонки
        existing_columns = [col for col in keep_columns if col in df.columns]

        print(
            f"📋 Сохранено колонок: {len(existing_columns)} из {len(keep_columns)} возможных")

        return df[existing_columns]

    def process_single_file(self, file_path):
        """
        Обработка одного CSV файла
        Args:
            file_path: Путь к файлу
        Returns:
            pandas DataFrame с обработанными данными
        """
        # Чтение файла
        df = self.read_csv(file_path)
        if df is None:
            return None

        initial_rows = len(df)
        self.stats['total_rows'] += initial_rows

        print(f"\n📄 Обработка файла: {Path(file_path).name}")
        print(f"📊 Загружено строк: {initial_rows}")

        # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Извлекаем телефоны из всех phone_* колонок
        df = self.extract_phone_columns(df)

        # Удаление ненужных колонок
        df = self.remove_unnecessary_columns(df)

        # Удаляем строки где оба телефона пустые
        df = df[~(df['phone_1'].isna() & df['phone_2'].isna())]

        invalid_count = initial_rows - len(df)
        self.stats['invalid_phones'] += invalid_count

        if invalid_count > 0:
            print(f"⚠️ Удалено строк без валидных телефонов: {invalid_count}")

        self.stats['files_processed'] += 1

        return df

    def merge_files(self, file_paths):
        """
        Объединение нескольких CSV файлов
        Args:
            file_paths: Список путей к файлам
        Returns:
            pandas DataFrame с объединёнными данными
        """
        all_dataframes = []

        for file_path in file_paths:
            df = self.process_single_file(file_path)
            if df is not None:
                # Добавление колонки "Источник телефона" (название файла)
                filename = Path(file_path).name
                df['source_file'] = filename
                all_dataframes.append(df)

        if not all_dataframes:
            return None

        # Объединение всех DataFrame
        merged_df = pd.concat(all_dataframes, ignore_index=True)

        # Удаление дубликатов по phone_1
        initial_count = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=['phone_1'], keep='first')

        self.stats['duplicates_removed'] = initial_count - len(merged_df)
        self.stats['valid_rows'] = len(merged_df)

        if self.stats['duplicates_removed'] > 0:
            print(
                f"\n🔄 Удалено дубликатов: {self.stats['duplicates_removed']}")

        return merged_df

    def export_for_bitrix(self, df, managers_list, output_path):
        """
        Экспорт данных в формате Битрикс
        Args:
            df: pandas DataFrame с обработанными данными
            managers_list: Список менеджеров
            output_path: Путь для сохранения CSV
        """
        # Группировка по исходным файлам и маппинг для каждого
        bitrix_dataframes = []

        for source_file in df['source_file'].unique():
            file_df = df[df['source_file'] == source_file].copy()
            bitrix_df = BitrixMapper.map_to_bitrix(
                file_df, managers_list, source_file)
            bitrix_dataframes.append(bitrix_df)

        # Объединение всех обработанных файлов
        final_df = pd.concat(bitrix_dataframes, ignore_index=True)

        # ИСПРАВЛЕНО: Экспорт в CSV с точкой с запятой для Битрикс
        final_df.to_csv(
            output_path,
            index=False,
            encoding='utf-8-sig',  # BOM для правильного отображения в Excel/Битрикс
            sep=';',               # ← КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: точка с запятой!
            quoting=1              # Оборачивать все значения в кавычки
        )

        print(f"\n✅ Файл сохранён: {output_path}")
        print(f"📊 Формат: CSV с разделителем ';' (точка с запятой)")
        print(f"\n📊 Итоговая статистика:")
        print(f"   • Всего строк загружено: {self.stats['total_rows']}")
        print(f"   • Валидных строк: {self.stats['valid_rows']}")
        print(f"   • Удалено дубликатов: {self.stats['duplicates_removed']}")
        print(f"   • Невалидных телефонов: {self.stats['invalid_phones']}")
        print(f"   • Обработано файлов: {self.stats['files_processed']}")

    def get_statistics(self):
        """Получение статистики обработки"""
        return self.stats
