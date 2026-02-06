import customtkinter as ctk
import tkinter as tk
from tkinter import ttk


class PreviewTable(ctk.CTkFrame):
    """Компонент предпросмотра таблицы данных"""

    def __init__(self, parent):
        super().__init__(parent)

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self,
            text="📋 Предпросмотр данных (первые 10 строк)",
            font=("Arial", 12, "bold")
        )
        self.title_label.pack(pady=5)

        # Frame для таблицы с прокруткой
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Горизонтальный скроллбар
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")

        # Вертикальный скроллбар
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")

        # Treeview для таблицы
        self.tree = ttk.Treeview(
            table_frame,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
            selectmode="browse",
            height=10
        )
        self.tree.pack(fill="both", expand=True)

        h_scrollbar.config(command=self.tree.xview)
        v_scrollbar.config(command=self.tree.yview)

        # Стиль для Treeview (темная тема)
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0
        )
        style.configure("Treeview.Heading",
                        background="#1f538d", foreground="white")
        style.map("Treeview", background=[("selected", "#1f538d")])

    def display_data(self, dataframe, max_rows=10):
        """Отображение данных из DataFrame"""
        # Очистка существующих данных
        self.tree.delete(*self.tree.get_children())

        if dataframe is None or dataframe.empty:
            return

        # Ограничение количества строк
        df_preview = dataframe.head(max_rows)

        # Настройка колонок
        columns = list(df_preview.columns)
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        # Заголовки колонок
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="w")

        # Заполнение данных
        for _, row in df_preview.iterrows():
            values = [str(val)[:50]
                      for val in row]  # Ограничение длины значений
            self.tree.insert("", "end", values=values)

    def clear(self):
        """Очистка таблицы"""
        self.tree.delete(*self.tree.get_children())
