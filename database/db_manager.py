import sqlite3
import json
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """Управление SQLite базой данных"""

    def __init__(self, db_path='data/database.db'):
        self.db_path = db_path
        Path('data').mkdir(exist_ok=True)
        self.init_database()

    def init_database(self):
        """Инициализация таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица истории обработки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_files TEXT,
                output_file TEXT,
                rows_processed INTEGER,
                rows_output INTEGER,
                duplicates_removed INTEGER,
                invalid_phones INTEGER,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица менеджеров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS managers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_processing_history(self, input_files, output_file, stats, processing_time):
        """Сохранение истории обработки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO processing_history 
            (input_files, output_file, rows_processed, rows_output, 
             duplicates_removed, invalid_phones, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            json.dumps(input_files),
            output_file,
            stats.get('total_rows', 0),
            stats.get('valid_rows', 0),
            stats.get('duplicates_removed', 0),
            stats.get('invalid_phones', 0),
            processing_time
        ))

        conn.commit()
        conn.close()

    def get_processing_history(self, limit=10):
        """Получение истории обработок"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, input_files, output_file, rows_processed, rows_output,
                   duplicates_removed, invalid_phones, processing_time, created_at
            FROM processing_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'input_files': json.loads(row[1]),
                'output_file': row[2],
                'rows_processed': row[3],
                'rows_output': row[4],
                'duplicates_removed': row[5],
                'invalid_phones': row[6],
                'processing_time': row[7],
                'created_at': row[8]
            })

        return history

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
