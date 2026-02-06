import sys

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"❌ ОШИБКА ИМПОРТА: {e}")
    print("Проверьте что все файлы на месте и зависимости установлены")
    sys.exit(1)

if __name__ == '__main__':
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
