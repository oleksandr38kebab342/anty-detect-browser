import threading
import flet as ft
from app_core import AntyDetectBrowser
from app_funcs.update_statuses import update_statuses


def main(page: ft.Page):
    app = AntyDetectBrowser(page)

    status_thread = threading.Thread(target=update_statuses, args=(page, app), daemon=True)
    status_thread.start()
