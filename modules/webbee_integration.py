"""
Модуль интеграции с Webbee AI API для автопарсинга данных
"""
import requests
import time
from typing import Dict, List, Optional, Any
import pandas as pd
from io import StringIO


class WebbeeAPIClient:
    """Клиент для работы с Webbee AI API"""

    # Правильный URL из документации
    BASE_URL = "https://analytics.webbee-ai.ru/webbee-api/v1.0"

    # Алиасы роботов (можно посмотреть в интерфейсе Webbee)
    ROBOTS = {
        'avito': 'avito',
        'yandex_maps': 'yandexmaps',  # Уточните правильный алиас!
        'html': 'html',
        '2gis': '2gis',
    }

    def __init__(self, api_token: str):
        """
        Инициализация клиента

        Args:
            api_token: API токен от Webbee AI
        """
        self.api_token = api_token
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
            elif level == "WARNING":
                self.logger.warning(message)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Выполнение HTTP запроса к API

        Args:
                method: HTTP метод (GET, POST, PATCH, DELETE)
                endpoint: Endpoint API
                **kwargs: Дополнительные параметры для requests

        Returns:
                Ответ API в виде словаря
        """
        url = f"{self.BASE_URL}{endpoint}"

        # Добавляем токен к параметрам
        if 'params' not in kwargs:
            kwargs['params'] = {}
        kwargs['params']['webbeeApiToken'] = self.api_token

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()

            # Для методов, которые возвращают 204 No Content
            if response.status_code == 204:
                return {"status": "success"}

            # Проверяем Content-Type в заголовках
            content_type = response.headers.get('Content-Type', '').lower()

            # Если ответ - CSV файл
            if 'text/csv' in content_type or 'application/csv' in content_type:
                return {"content": response.text, "type": "csv"}

            # Если ответ - plain text (может быть CSV без правильного Content-Type)
            if 'text/plain' in content_type:
                # Пробуем определить, это CSV или нет
                if response.text and (',' in response.text or ';' in response.text):
                    return {"content": response.text, "type": "csv"}

            # Если нет Content-Type или он неизвестен, проверяем содержимое
            # Если начинается с '{' или '[' - это JSON
            text = response.text.strip()
            if text and (text[0] in ['{', '[']):
                try:
                    return response.json()
                except:
                    pass

            # В противном случае считаем что это CSV
            if text:
                return {"content": text, "type": "csv"}

            # Если ничего не подошло, пробуем JSON
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                pass

            self._log(f"Ошибка API: {error_msg}", "ERROR")
            return {"error": error_msg}

        except Exception as e:
            self._log(f"Ошибка запроса: {str(e)}", "ERROR")
            return {"error": str(e)}

    def create_task(self, robot_alias: str, urls: List[str],
                    task_name: Optional[str] = None,
                    comment: Optional[str] = None,
                    settings: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Создание задания парсинга

        Args:
            robot_alias: Алиас робота (avito, yandex_maps, 2gis, html)
            urls: Список URL для парсинга
            task_name: Название задания
            comment: Комментарий
            settings: Дополнительные настройки

        Returns:
            Словарь с данными созданного задания
        """
        # Формирование URLs как строка с переносами
        urls_string = "\n".join(urls)

        payload = {
            "robot": robot_alias,
            "name": task_name or f"Task_{int(time.time())}",
            "urls": urls_string,
        }

        if comment:
            payload["comment"] = comment

        if settings:
            payload["settings"] = settings

        self._log(
            f"Создание задания: {task_name}, робот: {robot_alias}, URLs: {len(urls)}")

        result = self._make_request("POST", "/tasks", json=payload)

        if "error" not in result:
            task_id = result.get("id")
            self._log(f"Задание создано: ID={task_id}")

        return result

    def start_task(self, task_id: int, uid: Optional[str] = None) -> Dict[str, Any]:
        """
        Запуск задания парсинга

        Args:
            task_id: ID задания
            uid: Уникальный идентификатор для предотвращения дублирования

        Returns:
            Статус запуска
        """
        params = {}
        if uid:
            params['uid'] = uid

        self._log(f"Запуск задания: ID={task_id}")

        result = self._make_request(
            "PATCH", f"/tasks/{task_id}/start", params=params)

        if "error" not in result:
            self._log(f"Задание запущено успешно")

        return result

    def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """
        Получение статуса задания

        Args:
            task_id: ID задания

        Returns:
            Информация о статусе задания
        """
        result = self._make_request("GET", f"/tasks/{task_id}/status")

        if "error" not in result:
            progress = result.get("progress", {})
            total = progress.get("total", 0)
            processed = progress.get("processed", 0)
            success = progress.get("success", 0)

            self._log(
                f"Статус задания {task_id}: обработано {processed}/{total}, успешно: {success}")

        return result

    def wait_for_completion(self, task_id: int,
                            check_interval: int = 10,
                            max_wait_time: int = 3600,
                            progress_callback=None) -> bool:
        """
        Ожидание завершения задания с callback для прогресса

        Args:
            task_id: ID задания
            check_interval: Интервал проверки статуса (секунды)
            max_wait_time: Максимальное время ожидания (секунды)
            progress_callback: Функция для обновления прогресса

        Returns:
            True если завершено успешно, False если ошибка или таймаут
        """
        self._log(f"Ожидание завершения задания {task_id}...")

        elapsed_time = 0

        while elapsed_time < max_wait_time:
            status_data = self.get_task_status(task_id)

            if "error" in status_data:
                return False

            # Обновление прогресса через callback
            if progress_callback and "progress" in status_data:
                progress = status_data["progress"]
                progress_callback(progress)

            # Проверка завершения
            completed_at = status_data.get("completedAt")
            if completed_at:
                self._log(f"Задание {task_id} завершено!")
                return True

            # Ожидание перед следующей проверкой
            time.sleep(check_interval)
            elapsed_time += check_interval

        self._log(f"Превышено время ожидания для задания {task_id}", "ERROR")
        return False

    def download_results_csv(self, task_id: int) -> Optional[pd.DataFrame]:
        """
        Скачивание результатов парсинга в формате CSV

        Args:
                task_id: ID задания

        Returns:
                DataFrame с результатами или None при ошибке
        """
        self._log(f"Скачивание результатов задания {task_id}")

        result = self._make_request("GET", f"/tasks/{task_id}/result/csv")

        if "error" in result:
            self._log(
                f"Ошибка получения результатов: {result['error']}", "ERROR")
            return None

        if result.get("type") == "csv" and "content" in result:
            try:
                # Проверяем что content не пустой
                if not result["content"] or result["content"].strip() == "":
                    self._log("Пустой результат от API", "WARNING")
                    return None

                # ИСПРАВЛЕНО: Webbee использует табуляцию как разделитель
                # Вариант 1: CSV с табуляцией (основной формат Webbee)
                try:
                    df = pd.read_csv(
                        StringIO(result["content"]),
                        sep='\t',  # ← КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ!
                        encoding='utf-8',
                        on_bad_lines='skip',
                        engine='python'
                    )
                    self._log(f"Получено {len(df)} записей (разделитель TAB)")
                    return df
                except Exception as e1:
                    self._log(
                        f"Попытка с TAB не удалась: {str(e1)}", "WARNING")

                    # Вариант 2: CSV с запятой (запасной вариант)
                    try:
                        df = pd.read_csv(
                            StringIO(result["content"]),
                            encoding='utf-8',
                            on_bad_lines='skip',
                            engine='python'
                        )
                        self._log(
                            f"Получено {len(df)} записей (разделитель ',')")
                        return df
                    except Exception as e2:
                        self._log(
                            f"Попытка с запятой не удалась: {str(e2)}", "WARNING")

                        # Вариант 3: CSV с точкой с запятой
                        try:
                            df = pd.read_csv(
                                StringIO(result["content"]),
                                sep=';',
                                encoding='utf-8',
                                on_bad_lines='skip',
                                engine='python'
                            )
                            self._log(
                                f"Получено {len(df)} записей (разделитель ';')")
                            return df
                        except Exception as e3:
                            self._log(
                                f"Все попытки парсинга не удались. Последняя ошибка: {str(e3)}", "ERROR")
                            return None

            except Exception as e:
                self._log(
                    f"Критическая ошибка парсинга CSV: {str(e)}", "ERROR")
                return None

        self._log("Неожиданный формат ответа от API", "ERROR")
        return None

    def stop_task(self, task_id: int) -> Dict[str, Any]:
        """
        Остановка задания

        Args:
            task_id: ID задания

        Returns:
            Статус остановки
        """
        self._log(f"Остановка задания: ID={task_id}")
        return self._make_request("PATCH", f"/tasks/{task_id}/stop")

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """
        Удаление задания

        Args:
            task_id: ID задания

        Returns:
            Статус удаления
        """
        self._log(f"Удаление задания: ID={task_id}")
        return self._make_request("DELETE", f"/tasks/{task_id}")

    def get_collected_fields(self, task_id: int) -> Dict[str, Any]:
        """
        Получение списка собранных полей

        Args:
            task_id: ID задания

        Returns:
            Словарь с полями и примерами значений
        """
        return self._make_request("GET", f"/tasks/{task_id}/collected-fields")


# Пример использования
if __name__ == "__main__":
    # ВНИМАНИЕ: Замените на ваш реальный API токен!
    API_TOKEN = "your_api_token_here"

    client = WebbeeAPIClient(API_TOKEN)

    # Пример парсинга Яндекс.Карт
    urls_to_parse = [
        "https://yandex.ru/maps/moscow/search/кафе",
    ]

    # Создание задания
    task = client.create_task(
        robot_alias="yandex_maps",  # Уточните правильный алиас
        urls=urls_to_parse,
        task_name="Test Parse"
    )

    if "error" not in task:
        task_id = task["id"]
        print(f"Задание создано: {task_id}")

        # Запуск
        start = client.start_task(task_id)

        if "error" not in start:
            # Ожидание
            if client.wait_for_completion(task_id):
                # Скачивание
                results = client.download_results_csv(task_id)
                if results is not None:
                    print(f"Получено {len(results)} записей")
                    print(results.head())
