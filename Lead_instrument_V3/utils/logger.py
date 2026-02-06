import logging
import os
from datetime import datetime


class Logger:
    """Логирование операций в файл"""

    @staticmethod
    def setup_logger(log_dir='logs'):
        """Настройка логгера"""
        # Создание папки для логов
        os.makedirs(log_dir, exist_ok=True)

        # Имя файла с текущей датой
        log_filename = f"{log_dir}/app_{datetime.now().strftime('%Y-%m-%d')}.log"

        # Настройка формата
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # Вывод в консоль
            ]
        )

        return logging.getLogger('LeadGenSystem')

    @staticmethod
    def log_processing(filename, total_rows, valid_rows, duplicates, invalid_phones):
        """Логирование обработки файла"""
        logger = logging.getLogger('LeadGenSystem')
        logger.info(f"Обработан файл: {filename}")
        logger.info(f"  Всего строк: {total_rows}")
        logger.info(f"  Валидных: {valid_rows}")
        logger.info(f"  Дубликатов удалено: {duplicates}")
        logger.info(f"  Невалидных телефонов: {invalid_phones}")

    @staticmethod
    def log_export(output_file, rows_count):
        """Логирование экспорта"""
        logger = logging.getLogger('LeadGenSystem')
        logger.info(f"Экспорт в Битрикс: {output_file}")
        logger.info(f"  Строк экспортировано: {rows_count}")

    @staticmethod
    def log_analytics(lead_count, deal_count, conversion):
        """Логирование аналитики"""
        logger = logging.getLogger('LeadGenSystem')
        logger.info(f"Анализ данных выполнен")
        logger.info(f"  LEAD: {lead_count}, DEAL: {deal_count}")
        logger.info(f"  Конверсия: {conversion}%")
