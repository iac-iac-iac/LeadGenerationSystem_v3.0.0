"""
Модуль генерации URL для парсинга Яндекс.Карт через Webbee AI
"""
import urllib.parse
from typing import List, Dict


class YandexMapsURLGenerator:
    """Генератор URL для парсинга Яндекс.Карт"""

    # Базовый URL (ИСПРАВЛЕНО!)
    BASE_URL = "https://yandex.ru/maps/?text="

    # Районы для мегаполисов
    DISTRICTS = {
        'Москва': [
            'ЦАО',  # Центральный
            'САО',  # Северный
            'СВАО',  # Северо-Восточный
            'ВАО',  # Восточный
            'ЮВАО',  # Юго-Восточный
            'ЮАО',  # Южный
            'ЮЗАО',  # Юго-Западный
            'ЗАО',  # Западный
            'СЗАО',  # Северо-Западный
            'ЗелАО',  # Зеленоградский
            'ТАО',  # Троицкий
            'НАО',  # Новомосковский
            'Химки',
            'Балашиха',
            'Подольск',
            'Королёв',
            'Мытищи',
            'Люберцы',
            'Красногорск',
            'Одинцово',
        ],
        'Санкт-Петербург': [
            'Адмиралтейский район',
            'Василеостровский район',
            'Выборгский район',
            'Калининский район',
            'Кировский район',
            'Колпинский район',
            'Красногвардейский район',
            'Красносельский район',
            'Кронштадтский район',
            'Курортный район',
            'Московский район',
            'Невский район',
            'Петроградский район',
            'Петродворцовый район',
            'Приморский район',
            'Пушкинский район',
            'Фрунзенский район',
            'Центральный район',
        ],
    }

    # Популярные города (для быстрого выбора)
    POPULAR_CITIES = [
        'Москва',
        'Санкт-Петербург',
        'Новосибирск',
        'Екатеринбург',
        'Казань',
        'Нижний Новгород',
        'Челябинск',
        'Самара',
        'Омск',
        'Ростов-на-Дону',
        'Уфа',
        'Красноярск',
        'Воронеж',
        'Пермь',
        'Волгоград',
    ]

    def __init__(self):
        self.logger = None

    def set_logger(self, logger):
        """Установка логгера"""
        self.logger = logger

    def _log(self, message: str, level: str = "INFO"):
        """Логирование"""
        if self.logger:
            if level == "INFO":
                self.logger.info(message)
            elif level == "ERROR":
                self.logger.error(message)

    def get_popular_cities(self) -> List[str]:
        """Получить список популярных городов"""
        return self.POPULAR_CITIES

    def is_megapolis(self, city: str) -> bool:
        """Проверка, является ли город мегаполисом с районами"""
        return city in self.DISTRICTS

    def get_districts(self, city: str) -> List[str]:
        """Получить список районов для города"""
        return self.DISTRICTS.get(city, [])

    def generate_url(self, segment: str, city: str, district: str = None) -> str:
        """
        Генерация одной ссылки для парсинга

        Args:
            segment: Сегмент поиска (кафе, рестораны и т.д.)
            city: Название города
            district: Район (опционально)

        Returns:
            URL для парсинга
        """
        # ИСПРАВЛЕНО: правильный порядок - сегмент + город + район
        if district:
            query = f"{segment} {city} {district}"
        else:
            query = f"{segment} {city}"

        # Кодирование запроса
        encoded_query = urllib.parse.quote(query)

        # Формирование URL (ИСПРАВЛЕНО!)
        url = f"{self.BASE_URL}{encoded_query}"

        return url

    def generate_urls_for_city(self, city: str, segment: str,
                               use_districts: bool = True,
                               selected_districts: List[str] = None) -> List[Dict[str, str]]:
        """
        Генерация всех ссылок для города

        Args:
            city: Название города
            segment: Сегмент поиска
            use_districts: Использовать районы для мегаполисов
            selected_districts: Список выбранных районов (если None - все)

        Returns:
            Список словарей с информацией о ссылках
        """
        results = []

        if use_districts and self.is_megapolis(city):
            # Генерация для каждого района
            districts = selected_districts if selected_districts else self.get_districts(
                city)

            for district in districts:
                url = self.generate_url(segment, city, district)
                results.append({
                    'city': city,
                    'segment': segment,
                    'district': district,
                    'url': url
                })

            self._log(
                f"Сгенерировано {len(results)} ссылок для {city} по районам")
        else:
            # Генерация без районов
            url = self.generate_url(segment, city)
            results.append({
                'city': city,
                'segment': segment,
                'district': None,
                'url': url
            })

            self._log(f"Сгенерирована 1 ссылка для {city}")

        return results

    def generate_urls_batch(self, cities: List[str], segment: str,
                            use_districts: bool = True) -> List[Dict[str, str]]:
        """
        Пакетная генерация ссылок для нескольких городов

        Args:
            cities: Список городов
            segment: Сегмент поиска
            use_districts: Использовать районы

        Returns:
            Список всех сгенерированных ссылок
        """
        all_results = []

        for city in cities:
            results = self.generate_urls_for_city(city, segment, use_districts)
            all_results.extend(results)

        self._log(
            f"Всего сгенерировано {len(all_results)} ссылок для {len(cities)} городов")

        return all_results


# Пример использования
if __name__ == "__main__":
    generator = YandexMapsURLGenerator()

    # Тест 1: Генерация для Москвы с районами
    print("=== Тест 1: Москва с районами ===")
    results = generator.generate_urls_for_city(
        "Москва", "кафе", use_districts=True)
    for r in results[:3]:  # Показываем первые 3
        print(f"{r['city']} {r['district']}: {r['url']}")
    print(f"Всего: {len(results)} ссылок\n")

    # Тест 2: Генерация для города без районов
    print("=== Тест 2: Казань без районов ===")
    results = generator.generate_urls_for_city(
        "Казань", "рестораны", use_districts=False)
    for r in results:
        print(f"{r['city']}: {r['url']}")
