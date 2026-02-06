import pandas as pd
from utils.url_cleaner import URLCleaner


class BitrixMapper:
    """Маппинг данных для импорта в Битрикс24"""

    # Все 64 колонки Битрикс (используем только нужные)
    BITRIX_COLUMNS = [
        'Название лида', 'Адрес', 'Рабочий телефон', 'Мобильный телефон',
        'Корпоративный сайт', 'Контакт Telegram', 'Контакт ВКонтакте',
        'Контакт Viber', 'Название компании', 'Комментарий', 'Стадия',
        'Источник', 'Ответственный', 'Тип услуги', 'Источник телефона',
    ]

    # Статичные значения
    STATIC_VALUES = {
        'Стадия': 'Новая заявка',
        'Источник': 'Холодный звонок',
        'Тип услуги': 'ГЦК',
        'Комментарий': ''  # Пусто в MVP
    }

    @staticmethod
    def map_to_bitrix(df, managers_list, source_filename):
        """
        Преобразование данных в формат Битрикс
        Args:
            df: pandas DataFrame с очищенными данными
            managers_list: Список менеджеров для round-robin
            source_filename: Название исходного файла для колонки "Источник телефона"
        Returns:
            pandas DataFrame: Данные в формате Битрикс
        """
        bitrix_df = pd.DataFrame()

        # Функция-помощник для безопасного получения значений
        def safe_get(column_name, default=''):
            """Безопасное получение колонки из DataFrame"""
            if column_name in df.columns:
                col = df[column_name]
                # Если это Series - возвращаем как есть
                if isinstance(col, pd.Series):
                    return col
                # Если это скалярное значение - создаем Series
                else:
                    return pd.Series([col] * len(df))
            else:
                return pd.Series([default] * len(df))

        # Маппинг колонок
        bitrix_df['Название лида'] = df.apply(
            lambda row: f"{row.get('Category 0', 'Компания')} - {row.get('Название', row.get('title', 'Без названия'))}",
            axis=1
        )

        bitrix_df['Адрес'] = safe_get('Адрес')
        if bitrix_df['Адрес'].isna().all() or (bitrix_df['Адрес'] == '').all():
            bitrix_df['Адрес'] = safe_get('address')

        bitrix_df['Рабочий телефон'] = safe_get('phone_1')
        bitrix_df['Мобильный телефон'] = safe_get('phone_2')

        # Очистка URL от UTM
        company_url = safe_get('companyUrl')
        if isinstance(company_url, pd.Series):
            bitrix_df['Корпоративный сайт'] = company_url.apply(
                URLCleaner.clean_url)
        else:
            bitrix_df['Корпоративный сайт'] = ''

        # Извлечение username из соцсетей
        telegram = safe_get('telegram')
        if isinstance(telegram, pd.Series):
            bitrix_df['Контакт Telegram'] = telegram.apply(
                lambda x: URLCleaner.extract_social_username(x, 'telegram')
            )
        else:
            bitrix_df['Контакт Telegram'] = ''

        vkontakte = safe_get('vkontakte')
        if isinstance(vkontakte, pd.Series):
            bitrix_df['Контакт ВКонтакте'] = vkontakte.apply(
                lambda x: URLCleaner.extract_social_username(x, 'vkontakte')
            )
        else:
            bitrix_df['Контакт ВКонтакте'] = ''

        # Viber/WhatsApp
        viber = safe_get('viber')
        if viber.isna().all() or (viber == '').all():
            viber = safe_get('whatsapp')
        bitrix_df['Контакт Viber'] = viber

        bitrix_df['Название компании'] = safe_get('Название')
        if bitrix_df['Название компании'].isna().all() or (bitrix_df['Название компании'] == '').all():
            bitrix_df['Название компании'] = safe_get('title')

        # Статичные значения
        for key, value in BitrixMapper.STATIC_VALUES.items():
            bitrix_df[key] = value

        # Источник телефона (критично для аналитики)
        bitrix_df['Источник телефона'] = source_filename

        # Round-robin распределение менеджеров
        if managers_list and len(managers_list) > 0:
            bitrix_df['Ответственный'] = [
                managers_list[i % len(managers_list)]
                for i in range(len(bitrix_df))
            ]
        else:
            bitrix_df['Ответственный'] = 'Не назначен'

        # Упорядочивание колонок
        bitrix_df = bitrix_df[BitrixMapper.BITRIX_COLUMNS]

        return bitrix_df
