import threading


def check_all_proxies(self, e):
    """Перевіряє всі проксі в списку."""
    proxies = self.db.get_all_proxies()

    if not proxies:
        self.show_error_dialog("Немає проксі для перевірки")
        return

    # Встановлюємо статус "перевіряється" для всіх
    for proxy in proxies:
        self.proxy_statuses[proxy['id']] = {'status': 'checking'}

    self.refresh_proxies()

    def check_all_in_thread():
        import time
        checked = 0

        for proxy in proxies:
            # Запускаємо перевірку кожного проксі
            self.check_proxy(proxy['id'])
            checked += 1

            # Невелика затримка між перевірками
            time.sleep(0.2)

        # Показуємо результат після завершення
        time.sleep(2)  # Даємо час на завершення всіх перевірок

        working = sum(1 for pid, status in self.proxy_statuses.items() if status.get('status') == 'working')
        failed = sum(1 for pid, status in self.proxy_statuses.items() if status.get('status') == 'failed')

        self.run_ui(
            lambda: self.show_success_dialog(
                f"Перевірка завершена\n\n✓ Працюють: {working}\n✗ Не працюють: {failed}"
            )
        )

    thread = threading.Thread(target=check_all_in_thread, daemon=True)
    thread.start()
