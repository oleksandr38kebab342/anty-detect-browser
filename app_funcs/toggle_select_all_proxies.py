def toggle_select_all_proxies(self, selected: bool):
    if self._updating_select_all:
        return
    proxies = self.db.get_all_proxies()
    if selected:
        self.selected_proxy_ids = {p['id'] for p in proxies}
    else:
        self.selected_proxy_ids.clear()
    self.refresh_proxies()
