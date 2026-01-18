import flet as ft


def show_success_dialog(self, message: str):
    """Показує діалог з успішним повідомленням."""
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Успіх"),
        content=ft.Text(message),
        actions=[
            ft.TextButton("OK", on_click=lambda e: self.close_dialog(dialog)),
        ],
    )
    self.open_dialog(dialog)
