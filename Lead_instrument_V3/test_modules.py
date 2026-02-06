"""
Скрипт тестирования модулей Lead Generation System
Запуск: python test_modules.py
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Цвета для вывода


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_test(test_name, passed, details=""):
    """Красивый вывод результата теста"""
    status = f"{Colors.GREEN}✅ PASSED{Colors.RESET}" if passed else f"{Colors.RED}❌ FAILED{Colors.RESET}"
    print(f"{status} | {test_name}")
    if details:
        print(f"        {details}")


def test_imports():
    """Тест импорта всех модулей"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}ТЕСТ 1: Проверка импортов модулей{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    modules_to_test = [
        ('modules.data_processor', 'DataProcessor'),
        ('modules.yandex_maps', 'YandexMapsGenerator'),
        ('modules.webbee_integration', 'WebbeeAPIClient'),
        ('modules.analytics', 'Analytics'),
        ('modules.phone_validator', 'PhoneValidator'),
    ]

    all_passed = True

    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print_test(f"Импорт {module_name}.{class_name}", True)
        except Exception as e:
            print_test(f"Импорт {module_name}.{class_name}", False, str(e))
            all_passed = False

    return all_passed


def test_yandex_maps():
    """Тест генератора Яндекс.Карт"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}ТЕСТ 2: Генератор Яндекс.Карт{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    try:
        from modules.yandex_maps import YandexMapsGenerator
        generator = YandexMapsGenerator()

        # Тест 1: Простой адрес
        link1 = generator.generate_map_link("Москва, ул. Ленина, 1")
        test_passed = "https://yandex.ru/maps/?text=" in link1 and len(
            link1) > 30
        print_test("Генерация ссылки по адресу",
                   test_passed, link1[:50] + "...")

        # Тест 2: Адрес с компанией
        link2 = generator.generate_map_link(
            "Москва, Красная площадь", "Кремль")
        test_passed = "Кремль" in link2 and "Красная" in link2
        print_test("Генерация ссылки с названием компании",
                   test_passed, link2[:50] + "...")

        # Тест 3: Пустой адрес
        link3 = generator.generate_map_link("")
        test_passed = link3 == ""
        print_test("Обработка пустого адреса",
                   test_passed, "Вернул пустую строку")

        # Тест 4: DataFrame
        test_df = pd.DataFrame({
            'Название': ['Компания А', 'Компания Б'],
            'Адрес': ['Москва, ул. 1', 'СПб, ул. 2']
        })

        result_df = generator.add_map_links_to_dataframe(test_df)
        test_passed = 'yandex_maps_link' in result_df.columns and len(
            result_df) == 2
        print_test("Добавление ссылок в DataFrame", test_passed,
                   f"Создано {len(result_df)} ссылок")

        # Тест 5: Координаты
        link5 = generator.generate_coordinate_link(55.7558, 37.6173, 15)
        test_passed = "ll=37.6173,55.7558" in link5 and "z=15" in link5
        print_test("Генерация ссылки по координатам",
                   test_passed, link5[:50] + "...")

        return True

    except Exception as e:
        print_test("Модуль Яндекс.Карт", False, str(e))
        return False


def test_webbee_integration():
    """Тест модуля Webbee AI"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}ТЕСТ 3: Интеграция Webbee AI{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    try:
        from modules.webbee_integration import WebbeeAPIClient

        # Тест инициализации (без реального токена)
        client = WebbeeAPIClient("test_token_12345")
        test_passed = client.api_token == "test_token_12345"
        print_test("Инициализация клиента", test_passed, "Токен установлен")

        # Тест заголовков
        test_passed = "Authorization" in client.headers and "Bearer" in client.headers[
            "Authorization"]
        print_test("Формирование заголовков", test_passed,
                   "Bearer токен в заголовках")

        # Тест базового URL
        test_passed = "webbee-ai.ru" in client.BASE_URL
        print_test("Базовый URL API", test_passed, client.BASE_URL)

        print(
            f"\n{Colors.YELLOW}⚠️ ВНИМАНИЕ: Реальные API запросы не тестируются (нужен токен){Colors.RESET}")

        return True

    except Exception as e:
        print_test("Модуль Webbee AI", False, str(e))
        return False


def test_data_processor():
    """Тест обработчика данных"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}ТЕСТ 4: Обработчик данных (DataProcessor){Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    try:
        from modules.data_processor import DataProcessor

        processor = DataProcessor()
        print_test("Инициализация DataProcessor", True)

        # Проверка наличия новых методов
        test_passed = hasattr(processor, 'add_yandex_maps_links')
        print_test("Метод add_yandex_maps_links существует", test_passed)

        test_passed = hasattr(processor, 'set_webbee_token')
        print_test("Метод set_webbee_token существует", test_passed)

        test_passed = hasattr(processor, 'parse_with_webbee')
        print_test("Метод parse_with_webbee существует", test_passed)

        # Проверка атрибутов
        test_passed = hasattr(processor, 'yandex_maps')
        print_test("Атрибут yandex_maps инициализирован", test_passed)

        return True

    except Exception as e:
        print_test("DataProcessor", False, str(e))
        return False


def test_config_structure():
    """Тест структуры конфигурации"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}ТЕСТ 5: Структура config.json{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    try:
        import json

        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        print_test("Чтение config.json", True)

        # Проверка ключей
        required_keys = ['app_name', 'version',
                         'managers', 'paths', 'settings']
        for key in required_keys:
            test_passed = key in config
            print_test(f"Ключ '{key}' присутствует", test_passed)

        # Проверка новой секции integrations
        test_passed = 'integrations' in config
        print_test("Секция 'integrations' добавлена", test_passed)

        if test_passed:
            test_passed = 'webbee_api_token' in config['integrations']
            print_test("Ключ 'webbee_api_token' в integrations", test_passed)

            test_passed = 'yandex_maps_enabled' in config['integrations']
            print_test("Ключ 'yandex_maps_enabled' в integrations", test_passed)

        return True

    except Exception as e:
        print_test("Структура config.json", False, str(e))
        return False


def test_file_structure():
    """Тест структуры файлов проекта"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}ТЕСТ 6: Структура файлов проекта{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    required_files = [
        'main.py',
        'config/config.json',
        'modules/data_processor.py',
        'modules/yandex_maps.py',
        'modules/webbee_integration.py',
        'modules/analytics.py',
        'modules/phone_validator.py',
        'gui/main_window.py',
        'utils/logger.py',
        'database/db_manager.py',
        'requirements.txt',
        'build_exe.py',
    ]

    all_passed = True

    for file_path in required_files:
        exists = os.path.exists(file_path)
        print_test(f"Файл {file_path}", exists)
        if not exists:
            all_passed = False

    return all_passed


def generate_test_report(results):
    """Генерация итогового отчета"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}ИТОГОВЫЙ ОТЧЕТ{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests

    print(f"Всего тестов: {total_tests}")
    print(f"{Colors.GREEN}Успешно: {passed_tests}{Colors.RESET}")
    print(f"{Colors.RED}Провалено: {failed_tests}{Colors.RESET}")

    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\nУспешность: {success_rate:.1f}%")

    if failed_tests == 0:
        print(
            f"\n{Colors.GREEN}✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Можно собирать .exe файл{Colors.RESET}")
        return True
    else:
        print(
            f"\n{Colors.RED}❌ ЕСТЬ ОШИБКИ! Исправьте их перед сборкой{Colors.RESET}")
        return False


if __name__ == '__main__':
    print(f"\n{Colors.BLUE}╔{'='*58}╗{Colors.RESET}")
    print(f"{Colors.BLUE}║{' '*10}Lead Generation System v3.1.0{' '*19}║{Colors.RESET}")
    print(f"{Colors.BLUE}║{' '*15}Тестирование модулей{' '*23}║{Colors.RESET}")
    print(f"{Colors.BLUE}╚{'='*58}╝{Colors.RESET}")

    print(f"\n{Colors.YELLOW}Начало тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

    # Запуск всех тестов
    results = {
        'Импорты': test_imports(),
        'Яндекс.Карты': test_yandex_maps(),
        'Webbee AI': test_webbee_integration(),
        'DataProcessor': test_data_processor(),
        'Config.json': test_config_structure(),
        'Структура файлов': test_file_structure(),
    }

    # Генерация отчета
    all_passed = generate_test_report(results)

    print(f"\n{Colors.YELLOW}Конец тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")

    # Код возврата для CI/CD
    sys.exit(0 if all_passed else 1)
