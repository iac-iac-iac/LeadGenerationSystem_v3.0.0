from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI


class ChartGenerator:
    """Генерация диаграмм для аналитики"""

    @staticmethod
    def create_pie_chart(data_dict, title, output_path):
        """
        Создание круговой диаграммы

        Args:
            data_dict: Словарь {label: value}
            title: Заголовок диаграммы
            output_path: Путь для сохранения
        """
        if not data_dict:
            print("⚠️  Нет данных для круговой диаграммы")
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        labels = list(data_dict.keys())
        values = list(data_dict.values())

        # Цветовая палитра
        colors = plt.cm.Set3.colors

        # Создание диаграммы
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )

        # Стилизация текста
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)

        ax.set_title(title, fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"✅ Круговая диаграмма сохранена: {output_path}")
        return output_path

    @staticmethod
    def create_bar_chart(data_dict, title, xlabel, ylabel, output_path):
        """
        Создание столбчатой диаграммы

        Args:
            data_dict: Словарь {label: value}
            title: Заголовок
            xlabel: Подпись оси X
            ylabel: Подпись оси Y
            output_path: Путь для сохранения
        """
        if not data_dict:
            print("⚠️  Нет данных для столбчатой диаграммы")
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        labels = list(data_dict.keys())
        values = list(data_dict.values())

        # Цвет столбцов
        colors = plt.cm.viridis.colors

        bars = ax.bar(labels, values, color=colors[:len(labels)])

        # Добавление значений над столбцами
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{int(height)}',
                ha='center',
                va='bottom',
                fontweight='bold'
            )

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(axis='y', alpha=0.3)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"✅ Столбчатая диаграмма сохранена: {output_path}")
        return output_path
