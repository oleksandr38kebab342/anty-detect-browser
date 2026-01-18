def show_import_proxy_dialog(self, e):
    """Показує діалог імпорту проксі з файлу."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.askopenfilename(
            title="Виберіть файл з проксі",
            filetypes=[("Text files", "*.txt")]
        )
        root.destroy()

        if not file_path:
            return

        self.import_proxies_from_file(file_path)
    except Exception as ex:
        self.show_error_dialog(f"Помилка відкриття діалогу файлу: {ex}")
