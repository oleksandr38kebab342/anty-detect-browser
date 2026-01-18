import flet as ft


def refresh_profiles(self):
    """Оновлює список профілів."""
    profiles = self.db.get_all_profiles()
    rows = []

    for profile in profiles:
        profile_id = profile['profile_id']
        is_running = self.browser_manager.is_profile_running(profile_id)
        status = ft.Text(
            "Running" if is_running else "Ready",
            color=ft.Colors.GREEN if is_running else ft.Colors.GREY,
        )

        proxy_text = profile.get('proxy_name', 'Немає') if profile.get('proxy_name') else 'Немає'

        actions = ft.Row(
            [
                ft.IconButton(
                    ft.Icons.PLAY_ARROW if not is_running else ft.Icons.STOP,
                    tooltip="Запустити" if not is_running else "Зупинити",
                    data=profile_id,
                    on_click=self.toggle_profile,
                ),
                ft.IconButton(
                    ft.Icons.EDIT,
                    tooltip="Редагувати",
                    on_click=lambda e, pid=profile_id: self.show_edit_profile_dialog(pid),
                ),
                ft.IconButton(
                    ft.Icons.DELETE,
                    tooltip="Видалити",
                    icon_color=ft.Colors.RED,
                    on_click=lambda e, pid=profile_id: self.delete_profile(pid),
                ),
            ],
            tight=True,
        )

        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(profile['name'])),
                    ft.DataCell(status),
                    ft.DataCell(ft.Text(profile.get('notes', '') or '')),
                    ft.DataCell(ft.Text(proxy_text)),
                    ft.DataCell(ft.Text(profile.get('tags', '') or '')),
                    ft.DataCell(actions),
                ]
            )
        )

    self.profiles_table.rows = rows
    if self.profiles_table and self.profiles_table.page:
        self.profiles_table.update()
