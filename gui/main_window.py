import customtkinter as ctk
import tkinter as tk
import os
import time
import threading
from utils.logger import Logger
from tkinter import filedialog, messagebox
from modules.analytics import Analytics
from gui.preview_table import PreviewTable
from utils.config_loader import ConfigLoader
from database.db_manager import DatabaseManager
from modules.data_processor import DataProcessor
from modules.chart_generator import ChartGenerator
from modules.report_exporter import ReportExporter


class MainWindow(ctk.CTk):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()

        # Настройка окна
        self.title("Lead Generation System - MVP v1.0")
        self.geometry("1400x900")

        # Инициализация компонентов
        self.config = ConfigLoader.load_config()
        self.logger = Logger.setup_logger()
        self.db = DatabaseManager()

        # Установка темы
        theme = self.config.get('settings', {}).get('theme', 'dark')
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        # Переменные состояния
        self.loaded_files = []
        self.processed_data = None
        self.processor = None
        self.analytics = Analytics(logger=self.logger)
        self.lead_file = None
        self.deal_file = None
        self.current_theme = theme

        # Создание интерфейса
        self.create_widgets()

        # Загрузка менеджеров из конфига
        self.load_managers_from_config()

        self.logger.info("Приложение запущено")

    def create_widgets(self):
        """Создание элементов интерфейса"""

        # Заголовок с переключателем темы
        self.header_frame = ctk.CTkFrame(self, height=60)
        self.header_frame.pack(fill="x", padx=10, pady=10)

        title_label = ctk.CTkLabel(
            self.header_frame,
            text="🚀 Lead Generation System",
            font=("Arial", 24, "bold")
        )
        title_label.pack(side="left", pady=15, padx=20)

        # Переключатель темы
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame,
            text="🌙 Тёмная тема",
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.pack(side="right", padx=20)
        if self.current_theme == "dark":
            self.theme_switch.select()

        # Кнопка истории
        history_btn = ctk.CTkButton(
            self.header_frame,
            text="📜 История",
            command=self.show_history,
            width=100
        )
        history_btn.pack(side="right", padx=10)

        # Табы (вкладки)
        self.tabview = ctk.CTkTabview(self, width=1380, height=750)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Вкладка 1: Обработка данных
        self.tab_processing = self.tabview.add("📊 Обработка данных")
        self.create_processing_tab()

        # Вкладка 2: Аналитика
        self.tab_analytics = self.tabview.add("📈 Аналитика")
        self.create_analytics_tab()

        self.tabview.add("🤖 Парсинг")  # Новая вкладка
        self.create_parsing_tab()

    def create_processing_tab(self):
        """Создание вкладки обработки данных"""

        # Основной контейнер (2 колонки)
        main_container = ctk.CTkFrame(self.tab_processing)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Левая колонка (загрузка файлов)
        left_panel = ctk.CTkFrame(main_container, width=500)
        left_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Правая колонка (настройки)
        right_panel = ctk.CTkFrame(main_container, width=500)
        right_panel.pack(side="right", fill="both",
                         expand=True, padx=5, pady=5)

        # --- ЛЕВАЯ ПАНЕЛЬ ---

        files_label = ctk.CTkLabel(
            left_panel, text="📁 Загрузка файлов", font=("Arial", 16, "bold"))
        files_label.pack(pady=10)

        self.select_files_btn = ctk.CTkButton(
            left_panel,
            text="Выбрать CSV файлы",
            command=self.select_files,
            height=40,
            font=("Arial", 14)
        )
        self.select_files_btn.pack(pady=10, padx=20, fill="x")

        self.files_listbox_label = ctk.CTkLabel(
            left_panel,
            text="Загруженные файлы (0):",
            font=("Arial", 12)
        )
        self.files_listbox_label.pack(pady=5)

        self.files_listbox = tk.Listbox(
            left_panel,
            height=10,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d"
        )
        self.files_listbox.pack(pady=5, padx=20, fill="both", expand=True)

        self.remove_file_btn = ctk.CTkButton(
            left_panel,
            text="Удалить выбранный файл",
            command=self.remove_selected_file,
            fg_color="red",
            hover_color="darkred"
        )
        self.remove_file_btn.pack(pady=5)

        # --- ПРАВАЯ ПАНЕЛЬ ---

        settings_label = ctk.CTkLabel(
            right_panel, text="⚙️ Настройки", font=("Arial", 16, "bold"))
        settings_label.pack(pady=10)

        managers_label = ctk.CTkLabel(
            right_panel,
            text="Список менеджеров (по одному на строку):",
            font=("Arial", 12)
        )
        managers_label.pack(pady=5)

        self.managers_textbox = ctk.CTkTextbox(right_panel, height=200)
        self.managers_textbox.pack(pady=5, padx=20, fill="both", expand=True)

        self.save_managers_btn = ctk.CTkButton(
            right_panel,
            text="💾 Сохранить список менеджеров",
            command=self.save_managers,
            height=35
        )
        self.save_managers_btn.pack(pady=10, padx=20, fill="x")

        # --- ЦЕНТРАЛЬНАЯ ПАНЕЛЬ (обработка) ---

        process_panel = ctk.CTkFrame(self.tab_processing)
        process_panel.pack(fill="x", padx=10, pady=10)

        self.process_btn = ctk.CTkButton(
            process_panel,
            text="🔄 Очистить и объединить",
            command=self.process_files,
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="green",
            hover_color="darkgreen",
            state="disabled"
        )
        self.process_btn.pack(pady=10, padx=20)

        self.progress_bar = ctk.CTkProgressBar(process_panel, width=600)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            process_panel, text="Готов к обработке")
        self.progress_label.pack(pady=5)

        # --- ПАНЕЛЬ РЕЗУЛЬТАТОВ (УПРОЩЁННАЯ) ---

        results_panel = ctk.CTkFrame(self.tab_processing)
        results_panel.pack(fill="x", padx=10, pady=10)

        results_label = ctk.CTkLabel(
            results_panel, text="📊 Результаты обработки", font=("Arial", 14, "bold"))
        results_label.pack(pady=10)

        self.stats_label = ctk.CTkLabel(
            results_panel,
            text="Ожидание обработки...",
            font=("Arial", 11)
        )
        self.stats_label.pack(pady=5)

        # Кнопка для просмотра таблицы в отдельном окне
        self.preview_btn = ctk.CTkButton(
            results_panel,
            text="👁️ Предпросмотр данных",
            command=self.show_preview,
            height=35,
            state="disabled"
        )
        self.preview_btn.pack(pady=5)

        # Кнопка экспорта
        self.export_btn = ctk.CTkButton(
            results_panel,
            text="📥 Экспортировать для Битрикс24",
            command=self.export_for_bitrix,
            height=40,
            font=("Arial", 14),
            state="disabled"
        )
        self.export_btn.pack(pady=10)

    def create_analytics_tab(self):
        """Создание вкладки аналитики"""

        # Заголовок
        header = ctk.CTkLabel(
            self.tab_analytics,
            text="📈 Анализ результатов из Битрикс24",
            font=("Arial", 18, "bold")
        )
        header.pack(pady=15)

        # Инструкция
        instruction = ctk.CTkLabel(
            self.tab_analytics,
            text="Загрузите экспорты LEAD.csv и DEAL.csv из Битрикс24 для анализа",
            font=("Arial", 11),
            text_color="gray"
        )
        instruction.pack(pady=5)

        # Панель загрузки файлов
        upload_frame = ctk.CTkFrame(self.tab_analytics)
        upload_frame.pack(fill="x", padx=20, pady=15)

        # LEAD файл
        lead_frame = ctk.CTkFrame(upload_frame)
        lead_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(lead_frame, text="📄 LEAD.csv:", font=(
            "Arial", 12, "bold")).pack(side="left", padx=10)

        self.lead_file_label = ctk.CTkLabel(
            lead_frame, text="Файл не выбран", text_color="gray")
        self.lead_file_label.pack(side="left", padx=10)

        ctk.CTkButton(
            lead_frame,
            text="Выбрать файл",
            command=self.select_lead_file,
            width=120
        ).pack(side="right", padx=10)

        # DEAL файл
        deal_frame = ctk.CTkFrame(upload_frame)
        deal_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(deal_frame, text="📄 DEAL.csv:", font=(
            "Arial", 12, "bold")).pack(side="left", padx=10)

        self.deal_file_label = ctk.CTkLabel(
            deal_frame, text="Файл не выбран", text_color="gray")
        self.deal_file_label.pack(side="left", padx=10)

        ctk.CTkButton(
            deal_frame,
            text="Выбрать файл",
            command=self.select_deal_file,
            width=120
        ).pack(side="right", padx=10)

        # Кнопка анализа
        self.analyze_btn = ctk.CTkButton(
            self.tab_analytics,
            text="🔍 Проанализировать данные",
            command=self.analyze_data,
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="purple",
            hover_color="darkviolet",
            state="disabled"
        )
        self.analyze_btn.pack(pady=20)

        # Панель результатов аналитики
        self.analytics_results_frame = ctk.CTkFrame(self.tab_analytics)
        self.analytics_results_frame.pack(
            fill="both", expand=True, padx=20, pady=10)

        self.analytics_text = ctk.CTkTextbox(
            self.analytics_results_frame, height=350)
        self.analytics_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.analytics_text.insert(
            "1.0", "Загрузите файлы LEAD.csv и DEAL.csv для начала анализа")

        # Кнопка экспорта отчёта
        self.export_report_btn = ctk.CTkButton(
            self.tab_analytics,
            text="📊 Экспортировать отчёт (Excel)",
            command=self.export_report,
            height=40,
            font=("Arial", 14),
            state="disabled"
        )
        self.export_report_btn.pack(pady=10)

    def show_preview(self):
        """Показать предпросмотр данных в отдельном окне"""
        if self.processed_data is None:
            messagebox.showwarning(
                "Предупреждение", "Нет данных для отображения")
            return

        # Окно предпросмотра
        preview_window = ctk.CTkToplevel(self)
        preview_window.title("👁️ Предпросмотр данных")
        preview_window.geometry("1200x600")

        # Заголовок
        title = ctk.CTkLabel(
            preview_window, text="📋 Предпросмотр обработанных данных", font=("Arial", 16, "bold"))
        title.pack(pady=15)

        # Таблица
        preview_table = PreviewTable(preview_window)
        preview_table.pack(fill="both", expand=True, padx=20, pady=10)
        preview_table.display_data(self.processed_data, max_rows=50)

        # Кнопка закрытия
        close_btn = ctk.CTkButton(
            preview_window, text="Закрыть", command=preview_window.destroy, height=35)
        close_btn.pack(pady=10)

    # --- Методы для обработки данных ---

    def select_files(self):
        """Выбор CSV файлов"""
        files = filedialog.askopenfilenames(
            title="Выберите CSV файлы",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if files:
            for file in files:
                if file not in self.loaded_files:
                    self.loaded_files.append(file)
                    filename = os.path.basename(file)
                    self.files_listbox.insert(tk.END, filename)

            self.update_files_count()
            self.check_ready_to_process()

    def remove_selected_file(self):
        """Удаление выбранного файла из списка"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            self.files_listbox.delete(index)
            self.loaded_files.pop(index)
            self.update_files_count()
            self.check_ready_to_process()

    def update_files_count(self):
        """Обновление счётчика файлов"""
        count = len(self.loaded_files)
        self.files_listbox_label.configure(
            text=f"Загруженные файлы ({count}):")

    def load_managers_from_config(self):
        """Загрузка менеджеров из конфига"""
        managers = ConfigLoader.get_managers(self.config)
        if managers:
            self.managers_textbox.delete("1.0", "end")
            self.managers_textbox.insert("1.0", "\n".join(managers))

    def save_managers(self):
        """Сохранение списка менеджеров"""
        text = self.managers_textbox.get("1.0", "end").strip()
        managers = [line.strip() for line in text.split("\n") if line.strip()]

        if not managers:
            messagebox.showwarning("Предупреждение", "Список менеджеров пуст!")
            return

        if ConfigLoader.save_managers(managers):
            self.db.save_managers(managers)
            self.config = ConfigLoader.load_config()
            self.logger.info(f"Сохранено {len(managers)} менеджеров")
            messagebox.showinfo(
                "Успех", f"Сохранено {len(managers)} менеджеров")
            self.check_ready_to_process()
        else:
            messagebox.showerror(
                "Ошибка", "Не удалось сохранить список менеджеров")

    def check_ready_to_process(self):
        """Проверка готовности к обработке"""
        managers = self.managers_textbox.get("1.0", "end").strip()
        has_managers = bool(managers)
        has_files = len(self.loaded_files) > 0

        if has_managers and has_files:
            self.process_btn.configure(state="normal", fg_color="green")
        else:
            self.process_btn.configure(state="disabled", fg_color="gray")

    def process_files(self):
        """Обработка файлов"""
        text = self.managers_textbox.get("1.0", "end").strip()
        managers = [line.strip() for line in text.split("\n") if line.strip()]

        if not managers:
            messagebox.showwarning(
                "Предупреждение", "Введите список менеджеров!")
            return

        self.process_btn.configure(state="disabled")
        self.progress_label.configure(text="Обработка файлов...")

        thread = threading.Thread(
            target=self._process_files_thread, args=(managers,))
        thread.start()

    def _process_files_thread(self, managers):
        """Обработка файлов в отдельном потоке"""
        start_time = time.time()

        try:
            self.processor = DataProcessor()

            self.after(0, lambda: self.progress_bar.set(0.3))
            self.after(0, lambda: self.progress_label.configure(
                text="Чтение и валидация файлов..."))

            self.processed_data = self.processor.merge_files(self.loaded_files)

            if self.processed_data is not None:
                processing_time = time.time() - start_time

                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.progress_label.configure(
                    text="✅ Обработка завершена!"))

                stats = self.processor.get_statistics()
                stats_text = (
                    f"Всего строк: {stats['total_rows']} | "
                    f"Валидных: {stats['valid_rows']} | "
                    f"Дубликатов удалено: {stats['duplicates_removed']} | "
                    f"Невалидных телефонов: {stats['invalid_phones']}"
                )
                self.after(
                    0, lambda: self.stats_label.configure(text=stats_text))

                self.after(
                    0, lambda: self.export_btn.configure(state="normal"))

                self.after(
                    0, lambda: self.preview_btn.configure(state="normal"))

                # Логирование
                self.logger.info(
                    f"Обработка завершена за {processing_time:.2f}с")
                Logger.log_processing(
                    ', '.join([os.path.basename(f)
                              for f in self.loaded_files]),
                    stats['total_rows'],
                    stats['valid_rows'],
                    stats['duplicates_removed'],
                    stats['invalid_phones']
                )

                self.after(0, lambda: messagebox.showinfo(
                    "Успех", "Обработка завершена успешно!"))
            else:
                raise Exception("Не удалось обработать файлы")

        except Exception as ex:  # ← Переименовали переменную
            error_msg = str(ex)  # ← Сохраняем сообщение
            self.after(0, lambda msg=error_msg: messagebox.showerror(
                "Ошибка", f"Ошибка обработки: {msg}"))
            self.logger.error(f"Ошибка обработки: {error_msg}")

        finally:
            self.after(0, lambda: self.process_btn.configure(state="normal"))

    def export_for_bitrix(self):
        """Экспорт данных для Битрикс"""
        if self.processed_data is None:
            messagebox.showwarning(
                "Предупреждение", "Сначала обработайте файлы!")
            return

        output_file = filedialog.asksaveasfilename(
            title="Сохранить CSV для Битрикс",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="bitrix_import.csv"
        )

        if output_file:
            try:
                text = self.managers_textbox.get("1.0", "end").strip()
                managers = [line.strip()
                            for line in text.split("\n") if line.strip()]

                self.processor.export_for_bitrix(
                    self.processed_data, managers, output_file)

                # Логирование
                Logger.log_export(output_file, len(self.processed_data))

                # Сохранение в БД
                self.db.save_processing_history(
                    filename=os.path.basename(output_file),
                    rows_processed=len(self.processed_data),
                    status='success'
                )
                messagebox.showinfo(
                    "Успех",
                    f"Файл сохранён:\n{output_file}\n\nТеперь можете импортировать его в Битрикс24"
                )
            except Exception as e:
                self.logger.error(f"Ошибка экспорта: {e}")
                messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")

    # --- Методы для аналитики ---

    def select_lead_file(self):
        """Выбор LEAD.csv"""
        file = filedialog.askopenfilename(
            title="Выберите LEAD.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file:
            self.lead_file = file
            filename = os.path.basename(file)
            self.lead_file_label.configure(text=filename, text_color="white")
            self.check_ready_to_analyze()

    def select_deal_file(self):
        """Выбор DEAL.csv"""
        file = filedialog.askopenfilename(
            title="Выберите DEAL.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file:
            self.deal_file = file
            filename = os.path.basename(file)
            self.deal_file_label.configure(text=filename, text_color="white")
            self.check_ready_to_analyze()

    def check_ready_to_analyze(self):
        """Проверка готовности к анализу"""
        if self.lead_file and self.deal_file:
            self.analyze_btn.configure(state="normal", fg_color="purple")
        else:
            self.analyze_btn.configure(state="disabled", fg_color="gray")

    def analyze_data(self):
        """Анализ данных из Битрикс"""
        if not self.lead_file or not self.deal_file:
            messagebox.showwarning("Предупреждение", "Выберите оба файла!")
            return

        self.analyze_btn.configure(state="disabled")
        thread = threading.Thread(target=self._analyze_data_thread)
        thread.start()

    def _analyze_data_thread(self):
        """Анализ данных в отдельном потоке"""
        try:
            self.after(0, lambda: self.analytics_text.delete("1.0", "end"))
            self.after(0, lambda: self.analytics_text.insert(
                "1.0", "🔄 Загрузка и анализ данных...\n"))

            self.analytics.load_bitrix_exports(self.lead_file, self.deal_file)
            self.analytics.filter_my_leads()
            self.analytics.calculate_metrics()

            summary = self.analytics.get_report_summary()
            self.after(0, lambda: self.analytics_text.delete("1.0", "end"))
            self.after(0, lambda: self.analytics_text.insert("1.0", summary))

            self.after(
                0, lambda: self.export_report_btn.configure(state="normal"))

            # Логирование
            metrics = self.analytics.metrics
            Logger.log_analytics(
                len(self.analytics.lead_df),
                len(self.analytics.deal_df),
                metrics.get('conversion', 0)
            )

            self.after(0, lambda: messagebox.showinfo(
                "Успех", "Анализ завершён!"))

        except Exception as e:
            self.logger.error(f"Ошибка анализа: {e}")
            error_text = f"❌ Ошибка анализа:\n{str(e)}"
            self.after(0, lambda: self.analytics_text.delete("1.0", "end"))
            self.after(0, lambda: self.analytics_text.insert(
                "1.0", error_text))
            self.after(0, lambda: messagebox.showerror(
                "Ошибка", f"Ошибка анализа: {str(e)}"))

        finally:
            self.after(0, lambda: self.analyze_btn.configure(state="normal"))

    def export_report(self):
        """Экспорт отчёта в Excel"""
        if not self.analytics.metrics:
            messagebox.showwarning(
                "Предупреждение", "Сначала проанализируйте данные!")
            return

        output_file = filedialog.asksaveasfilename(
            title="Сохранить отчёт",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="analytics_report.xlsx"
        )

        if output_file:
            try:
                os.makedirs('data/reports', exist_ok=True)

                chart_paths = {}

                rejection_reasons = self.analytics.metrics.get(
                    'rejection_reasons', {})
                if rejection_reasons:
                    pie_path = 'data/reports/rejection_pie.png'
                    ChartGenerator.create_pie_chart(
                        rejection_reasons,
                        "Распределение причин отказа",
                        pie_path
                    )
                    chart_paths['pie'] = pie_path

                top_managers = self.analytics.metrics.get('top_managers', {})
                if top_managers:
                    bar_path = 'data/reports/managers_bar.png'
                    ChartGenerator.create_bar_chart(
                        top_managers,
                        "Топ-менеджеры по количеству сделок",
                        "Менеджер",
                        "Количество сделок",
                        bar_path
                    )
                    chart_paths['bar'] = bar_path

                ReportExporter.export_to_excel(
                    self.analytics.metrics,
                    chart_paths,
                    output_file
                )

                self.logger.info(f"Отчёт экспортирован: {output_file}")

                messagebox.showinfo(
                    "Успех",
                    f"Отчёт сохранён:\n{output_file}"
                )

            except Exception as e:
                self.logger.error(f"Ошибка экспорта отчёта: {e}")
                messagebox.showerror(
                    "Ошибка", f"Ошибка экспорта отчёта: {str(e)}")

    # --- Дополнительные функции ---

    def toggle_theme(self):
        """Переключение темы"""
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
            self.current_theme = "dark"
            self.theme_switch.configure(text="🌙 Тёмная тема")
        else:
            ctk.set_appearance_mode("light")
            self.current_theme = "light"
            self.theme_switch.configure(text="☀️ Светлая тема")

        # Сохранение в конфиг
        self.config['settings']['theme'] = self.current_theme
        ConfigLoader.save_config(self.config)

        self.logger.info(f"Тема изменена на: {self.current_theme}")

    def show_history(self):
        """Показать историю обработок"""
        history = self.db.get_processing_history(limit=10)

        if not history:
            messagebox.showinfo("История", "История обработок пуста")
            return

        # Окно истории
        history_window = ctk.CTkToplevel(self)
        history_window.title("📜 История обработок")
        history_window.geometry("800x600")

        # Заголовок
        title = ctk.CTkLabel(
            history_window, text="📜 История обработок (последние 10)", font=("Arial", 16, "bold"))
        title.pack(pady=15)

        # Текстовое поле с историей
        text_box = ctk.CTkTextbox(history_window)
        text_box.pack(fill="both", expand=True, padx=20, pady=10)

        for idx, record in enumerate(history, 1):
            text_box.insert("end", f"\n{'='*60}\n")
            text_box.insert("end", f"#{idx} | {record['created_at']}\n")
            text_box.insert("end", f"{'='*60}\n")
            text_box.insert(
                "end", f"Входные файлы: {', '.join(record['input_files'])}\n")
            text_box.insert("end", f"Выходной файл: {record['output_file']}\n")
            text_box.insert(
                "end", f"Обработано строк: {record['rows_processed']}\n")
            text_box.insert(
                "end", f"Валидных строк: {record['rows_output']}\n")
            text_box.insert(
                "end", f"Удалено дубликатов: {record['duplicates_removed']}\n")
            text_box.insert(
                "end", f"Невалидных телефонов: {record['invalid_phones']}\n")
            text_box.insert(
                "end", f"Время обработки: {record['processing_time']:.2f}с\n")

        text_box.configure(state="disabled")

        # Кнопка закрытия
        close_btn = ctk.CTkButton(
            history_window, text="Закрыть", command=history_window.destroy)
        close_btn.pack(pady=10)

    def create_parsing_tab(self):
        """Создание вкладки парсинга через Webbee AI"""
        from modules.yandex_maps_url_generator import YandexMapsURLGenerator

        # Инициализация генератора URL
        self.url_generator = YandexMapsURLGenerator()
        if self.logger:
            self.url_generator.set_logger(self.logger)

        # Главный контейнер с прокруткой
        main_scroll = ctk.CTkScrollableFrame(self.tabview.tab("🤖 Парсинг"))
        main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок
        title = ctk.CTkLabel(
            main_scroll,
            text="Парсинг через Webbee AI + Яндекс.Карты",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 10))

        # ============================================================
        # СЕКЦИЯ 1: Генератор ссылок для Яндекс.Карт
        # ============================================================

        url_gen_frame = ctk.CTkFrame(main_scroll)
        url_gen_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            url_gen_frame,
            text="🗺️ Генератор ссылок для парсинга Яндекс.Карт",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Строка с настройками
        settings_frame = ctk.CTkFrame(url_gen_frame)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Сегмент
        ctk.CTkLabel(settings_frame, text="Сегмент:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.segment_entry = ctk.CTkEntry(
            settings_frame, width=200, placeholder_text="кафе, рестораны, автосервис")
        self.segment_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(settings_frame, text="Город:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w")

        # Комбобокс с возможностью ввода
        self.city_combo = ctk.CTkComboBox(
            settings_frame,
            width=200,
            values=self.url_generator.get_popular_cities(),
            command=self.on_city_selected
        )
        self.city_combo.grid(row=0, column=3, padx=5, pady=5)
        self.city_combo.set("Москва")
        # Подсказка для пользователя
        info_label = ctk.CTkLabel(
            url_gen_frame,
            text="💡 Совет: Вы можете вводить название города вручную, просто начните печатать",
            font=("Arial", 10),
            text_color="gray"
        )
        info_label.pack(pady=5)

        # Подсказка о ручном вводе
        ctk.CTkLabel(
            settings_frame,
            text="💡",
            font=("Arial", 12)
        ).grid(row=0, column=5, padx=2, pady=5)
        # Чекбокс для использования районов
        self.use_districts_var = ctk.BooleanVar(value=True)
        self.use_districts_check = ctk.CTkCheckBox(
            settings_frame,
            text="Использовать районы",
            variable=self.use_districts_var,
            command=self.toggle_districts
        )
        self.use_districts_check.grid(row=0, column=4, padx=10, pady=5)

        # Фрейм для выбора районов
        self.districts_frame = ctk.CTkFrame(url_gen_frame)
        self.districts_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(
            self.districts_frame,
            text="Выберите районы (или оставьте пустым для всех):",
            font=("Arial", 12)
        ).pack(anchor="w", padx=5, pady=5)

        # Скроллируемый фрейм для чекбоксов районов
        self.districts_scroll = ctk.CTkScrollableFrame(
            self.districts_frame, height=150)
        self.districts_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.district_vars = {}
        self.district_checkboxes = {}

        # Инициализация районов для Москвы
        self.load_districts("Москва")

        # Кнопки управления
        buttons_frame = ctk.CTkFrame(url_gen_frame)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            buttons_frame,
            text="Выбрать все",
            command=self.select_all_districts,
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            buttons_frame,
            text="Снять все",
            command=self.deselect_all_districts,
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            buttons_frame,
            text="🔗 Сгенерировать ссылки",
            command=self.generate_yandex_urls,
            width=200,
            fg_color="green",
            hover_color="darkgreen"
        ).pack(side="right", padx=5)

        # ============================================================
        # СЕКЦИЯ 2: Webbee AI парсинг
        # ============================================================

        webbee_frame = ctk.CTkFrame(main_scroll)
        webbee_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            webbee_frame,
            text="🤖 Webbee AI - Парсинг",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # API Token
        token_frame = ctk.CTkFrame(webbee_frame)
        token_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(token_frame, text="API Токен:").pack(side="left", padx=5)
        self.webbee_token_entry = ctk.CTkEntry(
            token_frame, width=350, show="*")
        self.webbee_token_entry.pack(side="left", padx=5)

        # Загрузка сохраненного токена
        if 'integrations' in self.config and 'webbee_api_token' in self.config['integrations']:
            saved_token = self.config['integrations']['webbee_api_token']
            if saved_token:
                self.webbee_token_entry.insert(0, saved_token)

        ctk.CTkButton(
            token_frame,
            text="💾 Сохранить",
            command=self.save_webbee_token,
            width=100
        ).pack(side="left", padx=5)

        # URLs для парсинга
        urls_label_frame = ctk.CTkFrame(webbee_frame)
        urls_label_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            urls_label_frame,
            text="URLs для парсинга:",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            urls_label_frame,
            text="📋 Очистить",
            command=self.clear_urls,
            width=100
        ).pack(side="right", padx=5)

        self.parse_urls_text = ctk.CTkTextbox(webbee_frame, height=200)
        self.parse_urls_text.pack(fill="both", expand=True, padx=10, pady=5)

        # ВАЖНО: Кнопка запуска парсинга
        bottom_frame = ctk.CTkFrame(webbee_frame)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        self.urls_count_label = ctk.CTkLabel(
            bottom_frame,
            text="URLs: 0",
            font=("Arial", 12)
        )
        self.urls_count_label.pack(side="left", padx=10)

        # КНОПКА ЗАПУСКА ПАРСИНГА
        self.start_parsing_button = ctk.CTkButton(
            bottom_frame,
            text="🚀 Запустить парсинг",
            command=self.start_webbee_parsing,
            height=40,
            width=200,
            fg_color="orange",
            hover_color="darkorange"
        )
        self.start_parsing_button.pack(side="right", padx=10)

        # Статус
        self.parse_status_label = ctk.CTkLabel(
            webbee_frame, text="", font=("Arial", 12))
        self.parse_status_label.pack(pady=5)

    def on_city_selected(self, choice):
        """Обработка выбора города"""
        self.load_districts(choice)

        # Автоматически включаем районы для мегаполисов
        if self.url_generator.is_megapolis(choice):
            self.use_districts_var.set(True)
            self.districts_frame.pack(
                fill="both", expand=True, padx=10, pady=5)
        else:
            self.use_districts_var.set(False)
            self.districts_frame.pack_forget()

    def load_districts(self, city):
        """Загрузка районов для выбранного города"""
        # Очистка старых чекбоксов
        for widget in self.districts_scroll.winfo_children():
            widget.destroy()

        self.district_vars.clear()
        self.district_checkboxes.clear()

        if not self.url_generator.is_megapolis(city):
            return

        # Создание новых чекбоксов
        districts = self.url_generator.get_districts(city)

        for i, district in enumerate(districts):
            var = ctk.BooleanVar(value=True)  # По умолчанию все выбраны
            self.district_vars[district] = var

            checkbox = ctk.CTkCheckBox(
                self.districts_scroll,
                text=district,
                variable=var
            )
            checkbox.grid(row=i // 3, column=i %
                          3, padx=10, pady=5, sticky="w")
            self.district_checkboxes[district] = checkbox

    def toggle_districts(self):
        """Переключение видимости районов"""
        if self.use_districts_var.get():
            self.districts_frame.pack(
                fill="both", expand=True, padx=10, pady=5)
        else:
            self.districts_frame.pack_forget()

    def select_all_districts(self):
        """Выбрать все районы"""
        for var in self.district_vars.values():
            var.set(True)

    def deselect_all_districts(self):
        """Снять выбор со всех районов"""
        for var in self.district_vars.values():
            var.set(False)

    def generate_yandex_urls(self):
        """Генерация ссылок для Яндекс.Карт"""
        from tkinter import messagebox

        segment = self.segment_entry.get().strip()
        if not segment:
            messagebox.showwarning("Ошибка", "Введите сегмент для поиска")
            return

        # ИСПРАВЛЕНО: теперь можно вводить город вручную
        city = self.city_combo.get().strip()
        if not city:
            messagebox.showwarning("Ошибка", "Введите или выберите город")
            return

        use_districts = self.use_districts_var.get()

        # Получение выбранных районов
        selected_districts = None
        if use_districts and self.url_generator.is_megapolis(city):
            selected_districts = [
                district for district, var in self.district_vars.items()
                if var.get()
            ]

            if not selected_districts:
                messagebox.showwarning("Ошибка", "Выберите хотя бы один район")
                return

        # Генерация ссылок
        results = self.url_generator.generate_urls_for_city(
            city, segment, use_districts, selected_districts
        )

        # Вставка в текстовое поле
        current_text = self.parse_urls_text.get("1.0", "end").strip()
        if current_text:
            self.parse_urls_text.insert("end", "\n")

        for result in results:
            self.parse_urls_text.insert("end", result['url'] + "\n")

        # Обновление счетчика
        self.update_urls_count()

        district_info = ""
        if use_districts and selected_districts:
            district_info = f"\nРайонов: {len(selected_districts)}"

        messagebox.showinfo(
            "Успех",
            f"Сгенерировано {len(results)} ссылок для парсинга!\n\n"
            f"Город: {city}\n"
            f"Сегмент: {segment}"
            f"{district_info}"
        )

        self.logger.info(
            f"Сгенерировано {len(results)} ссылок: {city}, {segment}")

    def update_urls_count(self):
        """Обновление счетчика URLs"""
        urls_text = self.parse_urls_text.get("1.0", "end").strip()
        if urls_text:
            urls = [url.strip()
                    for url in urls_text.split("\n") if url.strip()]
            self.urls_count_label.configure(text=f"URLs: {len(urls)}")
        else:
            self.urls_count_label.configure(text="URLs: 0")

    def clear_urls(self):
        """Очистка списка URLs"""
        self.parse_urls_text.delete("1.0", "end")
        self.update_urls_count()

    # Остальные методы (save_webbee_token, start_webbee_parsing) остаются без изменений

    def save_webbee_token(self):
        """Сохранение Webbee API токена"""
        from tkinter import messagebox
        import json

        token = self.webbee_token_entry.get().strip()
        if not token:
            messagebox.showwarning("Предупреждение", "Введите API токен")
            return

        # Сохранение в config
        if 'integrations' not in self.config:
            self.config['integrations'] = {}

        self.config['integrations']['webbee_api_token'] = token

        # Сохранение config в файл
        try:
            with open('config/config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("Успех", "API токен сохранен")
            self.logger.info("Webbee API токен сохранен")
        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось сохранить токен: {str(e)}")
            self.logger.error(f"Ошибка сохранения токена: {str(e)}")

    def start_webbee_parsing(self):
        """Запуск парсинга через Webbee"""
        from tkinter import messagebox
        from modules.webbee_integration import WebbeeAPIClient
        import threading
        import time
        import os

        # Проверка токена
        token = self.webbee_token_entry.get().strip()
        if not token:
            messagebox.showwarning(
                "Ошибка", "Сначала введите и сохраните API токен")
            return

        # Получение URLs
        urls_text = self.parse_urls_text.get("1.0", "end").strip()
        if not urls_text:
            messagebox.showwarning(
                "Ошибка", "Сначала сгенерируйте ссылки для парсинга")
            return

        urls = [url.strip() for url in urls_text.split("\n") if url.strip()]

        # Получаем сегмент и город для названия
        segment = self.segment_entry.get().strip() or "Парсинг"
        city = self.city_combo.get().strip() or "Неизвестно"

        # Используем алиас робота для Яндекс.Карт
        robot_alias = 'yandexmaps'

        self.parse_status_label.configure(text="⏳ Создание задания...")

        def parse_thread():
            try:
                # Создание клиента Webbee
                webbee_client = WebbeeAPIClient(token)
                webbee_client.set_logger(self.logger)

                task_name = f"{segment} {city} {time.strftime('%Y%m%d_%H%M%S')}"
                task_data = webbee_client.create_task(
                    robot_alias=robot_alias,
                    urls=urls,
                    task_name=task_name
                )

                if "error" in task_data:
                    self.parse_status_label.configure(
                        text=f"❌ Ошибка: {task_data['error']}")
                    messagebox.showerror(
                        "Ошибка", f"Ошибка создания задания:\n{task_data['error']}")
                    self.logger.error(
                        f"Ошибка создания задания Webbee: {task_data['error']}")
                    return

                task_id = task_data.get("id")
                self.parse_status_label.configure(
                    text=f"✅ Задание создано: ID {task_id}")
                self.logger.info(f"Задание Webbee создано: ID {task_id}")

                # Запуск задания
                self.parse_status_label.configure(
                    text=f"⏳ Запуск задания {task_id}...")
                start_result = webbee_client.start_task(task_id)

                if "error" in start_result:
                    self.parse_status_label.configure(text=f"❌ Ошибка запуска")
                    messagebox.showerror(
                        "Ошибка", f"Ошибка запуска:\n{start_result['error']}")
                    self.logger.error(
                        f"Ошибка запуска задания Webbee: {start_result['error']}")
                    return

                self.parse_status_label.configure(
                    text=f"⏳ Парсинг в процессе (ID: {task_id})...")
                self.logger.info(f"Задание Webbee запущено: ID {task_id}")

                # Функция обновления прогресса
                def update_progress(progress):
                    total = progress.get("total", 0)
                    processed = progress.get("processed", 0)
                    success = progress.get("success", 0)

                    if total > 0:
                        percent = (processed / total) * 100
                        self.parse_status_label.configure(
                            text=f"⏳ Прогресс: {processed}/{total} ({percent:.1f}%) | Успешно: {success}"
                        )

                # Ожидание завершения
                if not webbee_client.wait_for_completion(
                    task_id,
                    check_interval=15,
                    progress_callback=update_progress
                ):
                    self.parse_status_label.configure(
                        text="❌ Парсинг не завершен")
                    messagebox.showerror(
                        "Ошибка", "Парсинг не завершен или завершился с ошибкой")
                    self.logger.error("Парсинг Webbee не завершен")
                    return

                # Скачивание результатов
                self.parse_status_label.configure(
                    text="⏳ Скачивание результатов...")
                results = webbee_client.download_results_csv(task_id)

                if results is not None and not results.empty:
                    # Сохранение результатов
                    os.makedirs("data/processed", exist_ok=True)
                    output_file = f"data/processed/webbee_yandexmaps_{int(time.time())}.csv"
                    results.to_csv(output_file, index=False,
                                   encoding='utf-8-sig')

                    self.parse_status_label.configure(
                        text=f"✅ Парсинг завершен! Получено {len(results)} записей | Файл: {output_file}"
                    )

                    messagebox.showinfo(
                        "Успех",
                        f"Парсинг завершен!\n\n"
                        f"Получено: {len(results)} записей\n"
                        f"Робот: Яндекс.Карты\n"
                        f"Файл: {output_file}"
                    )
                    self.logger.info(
                        f"Webbee парсинг завершен: {len(results)} записей, файл: {output_file}")
                else:
                    self.parse_status_label.configure(
                        text="❌ Ошибка скачивания результатов")
                    messagebox.showerror(
                        "Ошибка", "Не удалось скачать результаты")
                    self.logger.error("Ошибка скачивания результатов Webbee")

            except Exception as e:
                self.parse_status_label.configure(text=f"❌ Ошибка: {str(e)}")
                messagebox.showerror(
                    "Ошибка", f"Критическая ошибка:\n{str(e)}")
                self.logger.error(f"Критическая ошибка Webbee: {str(e)}")

        threading.Thread(target=parse_thread, daemon=True).start()


if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()
