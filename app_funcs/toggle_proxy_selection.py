def toggle_proxy_selection(self, proxy_id: int, selected: bool):
    if selected:
        self.selected_proxy_ids.add(proxy_id)
    else:
        self.selected_proxy_ids.discard(proxy_id)
