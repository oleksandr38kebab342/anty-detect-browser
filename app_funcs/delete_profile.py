import flet as ft


def delete_profile(self, profile_id: str):
    """Видаляє профіль."""
    def confirm_delete(e):
        # Зупиняємо профіль, якщо він запущений
        if self.browser_manager.is_profile_running(profile_id):
            self.browser_manager.stop_profile(profile_id)

        # Видаляємо з бази даних
        self.db.delete_profile(profile_id)

        # Видаляємо папку профілю (опціонально)
        import shutil
        profile_path = self.browser_manager.get_profile_path(profile_id)
        if profile_path.exists():
            try:
                shutil.rmtree(profile_path)
            except Exception as e:
                print(f"Помилка видалення папки профілю: {e}")

        dialog.open = False
        self.page.update()
        self.refresh_profiles()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Підтвердження"),
        content=ft.Text("Ви впевнені, що хочете видалити цей профіль?"),
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
