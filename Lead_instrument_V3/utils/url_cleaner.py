import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class URLCleaner:
    """Очистка URL от UTM-меток и других параметров отслеживания"""

    # Параметры для удаления
    TRACKING_PARAMS = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
        'yclid', 'gclid', 'fbclid', '_openstat', 'from', 'ref'
    ]

    @staticmethod
    def clean_url(url):
        """
        Удаление UTM-меток и других tracking параметров из URL

        Args:
            url: Исходный URL

        Returns:
            str: Очищенный URL или None
        """
        if not url or url == '' or str(url) == 'nan':
            return None

        url_str = str(url).strip()

        # Проверка валидности URL
        if not url_str.startswith(('http://', 'https://')):
            # Если нет протокола, добавляем http://
            url_str = 'http://' + url_str

        try:
            # Парсинг URL
            parsed = urlparse(url_str)

            # Получение query параметров
            query_params = parse_qs(parsed.query)

            # Фильтрация: удаление tracking параметров
            cleaned_params = {
                key: value for key, value in query_params.items()
                if key not in URLCleaner.TRACKING_PARAMS
            }

            # Сборка нового query string
            new_query = urlencode(
                cleaned_params, doseq=True) if cleaned_params else ''

            # Сборка нового URL
            cleaned_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))

            return cleaned_url

        except Exception:
            # Если не удалось распарсить, возвращаем исходный URL
            return url_str

    @staticmethod
    def extract_social_username(url, platform='telegram'):
        """
        Извлечение username из ссылок на соцсети

        Args:
            url: Ссылка на профиль
            platform: 'telegram' или 'vkontakte'

        Returns:
            str: Username без @ и без URL
        """
        if not url or url == '' or str(url) == 'nan':
            return None

        url_str = str(url).strip()

        if platform == 'telegram':
            # https://t.me/username → username
            match = re.search(r't\.me/([a-zA-Z0-9_]+)', url_str)
            if match:
                return match.group(1)

        elif platform == 'vkontakte':
            # https://vk.com/username → username
            match = re.search(r'vk\.com/([a-zA-Z0-9_]+)', url_str)
            if match:
                return match.group(1)

        return url_str
