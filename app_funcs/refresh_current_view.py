def refresh_current_view(self):
    """Оновлює поточний вид."""
    if self.current_page == "profiles":
        self.refresh_profiles()
    elif self.current_page == "proxies":
        self.refresh_proxies()
