def setup_page(self):
    """Налаштування сторінки."""
    self.page.title = "Anty-Detect Browser"
    self.page.theme_mode = self.current_theme
    self.page.window.width = 1200
    self.page.window.height = 800
    self.page.window.min_width = 800
    self.page.window.min_height = 600
