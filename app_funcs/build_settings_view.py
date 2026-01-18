import flet as ft


def build_settings_view(self):
    """Створює вид налаштувань."""
    return ft.Column(
        [
            ft.Text("Налаштування", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row(
                [
                    ft.Text("Тема:", size=16),
                    self.theme_switch,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            ft.Text("Шлях до профілів:", size=16),
            ft.Text("profiles/", size=14, color=ft.Colors.SECONDARY),
        ],
        spacing=10,
    )
