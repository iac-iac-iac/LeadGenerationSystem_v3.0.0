import json
import os


class ConfigLoader:
    """Загрузка и сохранение конфигурации"""

    DEFAULT_CONFIG = {
        "app_name": "Lead Generation System",
        "version": "1.0.0",
        "managers": [],
        "paths": {
            "input": "data/input",
            "output": "data/output",
            "reports": "data/reports",
            "database": "data/database.db"
        },
        "settings": {
            "preview_rows": 10,
            "theme": "dark"
        }
    }

    @staticmethod
    def load_config(config_path='config/config.json'):
        """Загрузка конфига из файла"""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки конфига: {e}")
                return ConfigLoader.DEFAULT_CONFIG
        else:
            # Создание дефолтного конфига
            ConfigLoader.save_config(ConfigLoader.DEFAULT_CONFIG, config_path)
            return ConfigLoader.DEFAULT_CONFIG

    @staticmethod
    def save_config(config, config_path='config/config.json'):
        """Сохранение конфига в файл"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")
            return False

    @staticmethod
    def get_managers(config):
        """Получить список менеджеров"""
        return config.get('managers', [])

    @staticmethod
    def save_managers(managers, config_path='config/config.json'):
        """Сохранить список менеджеров"""
        config = ConfigLoader.load_config(config_path)
        config['managers'] = managers
        return ConfigLoader.save_config(config, config_path)
