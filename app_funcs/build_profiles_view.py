import flet as ft


def build_profiles_view(self):
    """Створює вид профілів."""
    # Заголовок та кнопка створення
    header = ft.Row(
        [
            ft.Text("Профілі", size=20, weight=ft.FontWeight.BOLD),
            ft.Button(
                "Створити профіль",
                icon=ft.Icons.PERSON_ADD,
                on_click=self.show_create_profile_dialog,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Таблиця профілів
    self.profiles_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Назва")),
            ft.DataColumn(ft.Text("Статус")),
            ft.DataColumn(ft.Text("Нотатки")),
            ft.DataColumn(ft.Text("Проксі")),
            ft.DataColumn(ft.Text("Теги")),
            ft.DataColumn(ft.Text("Дії")),
        ],
        rows=[],
    )

    return ft.Column(
        [
            header,
            ft.Container(
                content=ft.Column(
                    [self.profiles_table],
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
