def check_selected_proxies(self, e):
    if not self.selected_proxy_ids:
        self.show_error_dialog("Оберіть проксі для перевірки")
        return

    for proxy_id in list(self.selected_proxy_ids):
        self.check_proxy(proxy_id)

    # Скидаємо вибір після запуску перевірки
    self.selected_proxy_ids.clear()
    self.refresh_proxies()
