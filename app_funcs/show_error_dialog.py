import flet as ft


def show_error_dialog(self, message: str):
    """Показує діалог з помилкою."""
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Помилка"),
        content=ft.Text(message),
        actions=[
            ft.TextButton("OK", on_click=lambda e: self.close_dialog(dialog)),
        ],
    )
    self.open_dialog(dialog)
