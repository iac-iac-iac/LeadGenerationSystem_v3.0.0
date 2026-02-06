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

        # Получаем название компании (используем разные варианты)
        company_name = df.get('Название', '')
        if company_name is None or (isinstance(company_name, pd.Series) and company_name.isna().all()):
            company_name = df.get('title', '')

        # Маппинг колонок
        bitrix_df['Название лида'] = df.apply(
            lambda row: f"{row.get('Category 0', 'Компания')} - {row.get('Название', row.get('title', 'Без названия'))}",
            axis=1
        )

        bitrix_df['Адрес'] = df.get('Адрес', df.get('address', ''))
        bitrix_df['Рабочий телефон'] = df['phone_1']
        bitrix_df['Мобильный телефон'] = df.get('phone_2', '')

        # Очистка URL от UTM
        bitrix_df['Корпоративный сайт'] = df.get(
            'companyUrl', '').apply(URLCleaner.clean_url)

        # Извлечение username из соцсетей
        bitrix_df['Контакт Telegram'] = df.get('telegram', '').apply(
            lambda x: URLCleaner.extract_social_username(x, 'telegram')
        )

        bitrix_df['Контакт ВКонтакте'] = df.get('vkontakte', '').apply(
            lambda x: URLCleaner.extract_social_username(x, 'vkontakte')
        )

        bitrix_df['Контакт Viber'] = df.get('viber', df.get('whatsapp', ''))
        bitrix_df['Название компании'] = df.get(
            'Название', df.get('title', ''))

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
