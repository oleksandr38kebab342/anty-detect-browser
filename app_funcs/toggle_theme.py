import flet as ft


def toggle_theme(self, e):
    """Перемикає тему та зберігає вибір."""
    self.current_theme = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
    self.page.theme_mode = self.current_theme

    # Зберігаємо вибір теми
    theme_value = "dark" if self.current_theme == ft.ThemeMode.DARK else "light"
    self.db.set_setting("theme", theme_value)

    self.page.update()
