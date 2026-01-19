import flet as ft
import atexit
import asyncio
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

    def _on_disconnect(e):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.browser_manager.cleanup_sync()
            return

        try:
            loop.create_task(self.browser_manager.cleanup())
        except Exception:
            self.browser_manager.cleanup_sync()

    self.page.on_disconnect = _on_disconnect
    self.page.on_close = _on_disconnect
    atexit.register(self.browser_manager.cleanup_sync)
