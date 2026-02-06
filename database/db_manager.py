import sqlite3
import json
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """Управление SQLite базой данных"""

    def __init__(self, db_path='data/database.db'):
        self.db_path = db_path

        # Создать папку для базы данных если её нет
        from pathlib import Path
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self.init_database()

    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Создание таблицы истории обработки
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rows_processed INTEGER,
                    status TEXT
                )
            ''')

            conn.commit()
            print(f"✅ База данных инициализирована: {self.db_path}")

        except sqlite3.Error as e:
            print(f"❌ Ошибка инициализации базы данных: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def save_processing_history(self, filename, rows_processed, status='success'):
        """Сохранение истории обработки файла"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO processing_history (filename, rows_processed, status)
                VALUES (?, ?, ?)
            ''', (filename, rows_processed, status))

            conn.commit()
            print(f"✅ История обработки сохранена: {filename}")

        except sqlite3.Error as e:
            print(f"❌ Ошибка сохранения истории: {e}")
            # Не пробрасываем исключение - это не критично
        finally:
            if conn:
                conn.close()

    def get_processing_history(self, limit=10):
        """Получение истории обработки файлов"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT filename, processed_date, rows_processed, status
                FROM processing_history
                ORDER BY processed_date DESC
                LIMIT ?
            ''', (limit,))

            history = cursor.fetchall()
            return history

        except sqlite3.Error as e:
            print(f"❌ Ошибка получения истории: {e}")
            return []  # Возвращаем пустой список при ошибке
        finally:
            if conn:
                conn.close()

    def save_managers(self, managers_list):
        """Сохранение списка менеджеров"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Деактивация всех менеджеров
        cursor.execute('UPDATE managers SET is_active = 0')

        # Добавление/активация менеджеров
        for manager in managers_list:
            cursor.execute('''
                INSERT INTO managers (name, is_active) VALUES (?, 1)
                ON CONFLICT(name) DO UPDATE SET is_active = 1
            ''', (manager,))

        conn.commit()
        conn.close()

    def get_active_managers(self):
        """Получение активных менеджеров"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT name FROM managers WHERE is_active = 1 ORDER BY name')
        managers = [row[0] for row in cursor.fetchall()]

        conn.close()
        return managers
