import flet as ft


def delete_proxy(self, proxy_id: int):
    """Видаляє проксі."""
    def confirm_delete(e):
        self.db.delete_proxy(proxy_id)
        dialog.open = False
        self.page.update()
        self.refresh_proxies()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Підтвердження"),
        content=ft.Text("Ви впевнені, що хочете видалити цей проксі?"),
        actions=[
            ft.TextButton("Скасувати", on_click=lambda e: self.close_dialog(dialog)),
            ft.TextButton(
                "Видалити",
                on_click=confirm_delete,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    self.open_dialog(dialog)
