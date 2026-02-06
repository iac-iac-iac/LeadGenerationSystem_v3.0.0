import re
import pandas as pd


class PhoneValidator:
    """Валидация и очистка номеров телефонов"""

    @staticmethod
    def clean_phone(phone):
        """
        Очистка номера телефона от лишних символов
        Args:
            phone: Исходный номер (может быть в научной нотации, float, со спецсимволами)
        Returns:
            str: Очищенный номер (11 цифр) или None если невалидный
        """
        if pd.isna(phone) or phone == '' or str(phone).lower() in ['nan', 'none', '']:
            return None

        # Конвертация в строку
        phone_str = str(phone).strip()

        if not phone_str or phone_str.lower() in ['nan', 'none', '']:
            return None

        # НОВОЕ: Удаляем .0 в конце (если есть)
        if phone_str.endswith('.0'):
            phone_str = phone_str[:-2]

        # НОВОЕ: Обработка научной нотации (7.8005001695e+10 → 78005001695)
        # Проверяем наличие экспоненты
        if 'e+' in phone_str.lower() or 'e-' in phone_str.lower():
            try:
                # Конвертируем через float в int
                phone_float = float(phone_str)

                # Проверяем что число не слишком большое/маленькое
                if phone_float < 1e9 or phone_float > 9e11:
                    return None

                # Округляем и конвертируем в строку
                phone_str = str(int(round(phone_float)))

                print(
                    f"🔄 Конвертирован из научной нотации: {phone} → {phone_str}")

            except (ValueError, OverflowError) as e:
                print(f"⚠️ Ошибка конвертации научной нотации: {phone} - {e}")
                return None

        # Удаление всех символов кроме цифр
        digits_only = re.sub(r'\D', '', phone_str)

        # Валидация длины
        if len(digits_only) < 10:
            return None

        # Обрезаем лишние нули в начале (если есть)
        digits_only = digits_only.lstrip('0')

        # Нормализация: если 10 цифр → добавляем 7
        if len(digits_only) == 10:
            digits_only = '7' + digits_only

        # Проверка: должно быть 11 цифр
        if len(digits_only) != 11:
            return None

        # Замена первой цифры 8 на 7
        if digits_only[0] == '8':
            digits_only = '7' + digits_only[1:]

        # Проверка: должен начинаться с 7
        if not digits_only.startswith('7'):
            return None

        return digits_only

    @staticmethod
    def validate_phones_in_dataframe(df):
        """
        Валидация phone_1 и phone_2 в DataFrame
        Args:
            df: pandas DataFrame с колонками phone_1, phone_2
        Returns:
            pandas DataFrame: Очищенные данные
        """
        # Очистка phone_1
        if 'phone_1' in df.columns:
            df['phone_1'] = df['phone_1'].apply(PhoneValidator.clean_phone)

        # Очистка phone_2
        if 'phone_2' in df.columns:
            df['phone_2'] = df['phone_2'].apply(PhoneValidator.clean_phone)

        # Удаление строк, где оба телефона пустые
        df = df[~(df['phone_1'].isna() & df['phone_2'].isna())]

        return df

    @staticmethod
    def format_phone_for_display(phone):
        """
        Форматирование телефона для отображения
        Args:
            phone: Номер телефона (11 цифр)
        Returns:
            str: Отформатированный номер +7 (XXX) XXX-XX-XX
        """
        if not phone or len(str(phone)) != 11:
            return phone

        phone_str = str(phone)

        return f"+7 ({phone_str[1:4]}) {phone_str[4:7]}-{phone_str[7:9]}-{phone_str[9:11]}"
