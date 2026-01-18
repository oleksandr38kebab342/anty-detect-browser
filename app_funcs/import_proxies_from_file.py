import os


def import_proxies_from_file(self, file_path: str):
    """Імпортує проксі з файлу за шляхом."""
    if not file_path or not os.path.exists(file_path):
        self.show_error_dialog("Файл не знайдено")
        return

    try:
        imported_count = 0
        failed_count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                proxy_data = self.parse_proxy_line(line)
                if proxy_data:
                    try:
                        # Генеруємо назву якщо не вказана
                        name = f"Проксі {proxy_data['host']}:{proxy_data['port']}"

                        self.db.create_proxy(
                            name=name,
                            type=proxy_data['type'],
                            host=proxy_data['host'],
                            port=proxy_data['port'],
                            username=proxy_data.get('username'),
                            password=proxy_data.get('password')
                        )
                        imported_count += 1
                    except Exception as ex:
                        failed_count += 1
                        print(f"Помилка імпорту рядка {line_num}: {ex}")

        # Показуємо результат
        if imported_count > 0:
            self.show_success_dialog(f"Успішно додано {imported_count} проксі")
            self.refresh_proxies()
        else:
            self.show_error_dialog("Не вдалося імпортувати жодного проксі")

    except Exception as ex:
        self.show_error_dialog(f"Помилка читання файлу: {ex}")
