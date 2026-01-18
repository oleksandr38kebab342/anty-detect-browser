def on_nav_change(self, e):
    """Обробник зміни розділу в навігації."""
    index = e.control.selected_index
    if index == 0:
        self.current_page = "profiles"
        self.main_content.content = self.build_profiles_view()
    elif index == 1:
        self.current_page = "proxies"
        self.main_content.content = self.build_proxies_view()
    elif index == 2:
        self.current_page = "settings"
        self.main_content.content = self.build_settings_view()

    self.main_content.update()
    self.refresh_current_view()
