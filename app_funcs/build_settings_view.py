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
            ft.Container(
                content=ft.Column([
                    ft.Text("🔄 Функція 'Продовжити з місця зупинки'", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("✅ Активна", color=ft.Colors.GREEN, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Браузер автоматично відновлює:\n"
                        "• Відкриті вкладки\n"
                        "• Куки та сесії\n"
                        "• Збережені паролі\n"
                        "• Кеш і локальні дані\n"
                        "• Історію переглядів",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ]),
                padding=16,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            ),
            ft.Divider(),
            ft.Text("Шлях до профілів:", size=16),
            ft.Text("profiles/", size=14, color=ft.Colors.SECONDARY),
        ],
        spacing=10,
    )
