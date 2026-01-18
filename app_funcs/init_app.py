import flet as ft
from database.db_handler import Database
from browser_logic import BrowserManager


def __init__(self, page: ft.Page):
    self.page = page
    self.db = Database()
    self.browser_manager = BrowserManager()
    self.current_page = "profiles"

    # Завантажуємо збережену тему (за замовчуванням світла)
    saved_theme = self.db.get_setting("theme", "light")
    if saved_theme == "dark":
        self.current_theme = ft.ThemeMode.DARK
    else:
        self.current_theme = ft.ThemeMode.LIGHT

    # Словник для зберігання статусів проксі
    self.proxy_statuses = {}
    self.selected_proxy_ids = set()
    self.select_all_proxies = False
    self._updating_select_all = False

    # Ініціалізація UI
    self.setup_page()
    self.setup_ui()
