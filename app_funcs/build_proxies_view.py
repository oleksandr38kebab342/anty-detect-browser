import flet as ft


def build_proxies_view(self):
    """Створює вид проксі."""
    header = ft.Row(
        [
            ft.Text("Проксі", size=20, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    ft.Button(
                        "Перевірити",
                        icon=ft.Icons.CHECKLIST,
                        on_click=self.check_selected_proxies,
                    ),
                    ft.Button(
                        "Імпорт з .txt",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=self.show_import_proxy_dialog,
                    ),
                    ft.Button(
                        "Додати проксі",
                        icon=ft.Icons.ADD_LINK,
                        on_click=self.show_create_proxy_dialog,
                    ),
                ],
                spacing=10,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    self.proxies_table = ft.DataTable(
        columns=[
            ft.DataColumn(
                ft.Checkbox(
                    value=False,
                    on_change=lambda e: self.toggle_select_all_proxies(e.control.value),
                )
            ),
            ft.DataColumn(ft.Text("Назва")),
            ft.DataColumn(ft.Text("Тип")),
            ft.DataColumn(ft.Text("IP:Port")),
            ft.DataColumn(ft.Text("Статус")),
            ft.DataColumn(ft.Text("Дії")),
        ],
        rows=[],
    )

    return ft.Column(
        [
            header,
            ft.Container(
                content=ft.Column(
                    [self.proxies_table],
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
            ),
        ],
        expand=True,
        spacing=10,
    )
