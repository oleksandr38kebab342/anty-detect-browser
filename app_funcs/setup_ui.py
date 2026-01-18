import flet as ft


def setup_ui(self):
    """Створення інтерфейсу."""
    # Бокове меню
    self.nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        leading=ft.FloatingActionButton(
            icon=ft.Icons.PERSON_ADD,
            tooltip="Новий профіль",
            on_click=self.show_create_profile_dialog,
        ),
        group_alignment=-0.25,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.PERSON_OUTLINE,
                selected_icon=ft.Icons.PERSON,
                label="Профілі",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LANGUAGE_OUTLINED,
                selected_icon=ft.Icons.LANGUAGE,
                label="Проксі",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Налаштування",
            ),
        ],
        on_change=self.on_nav_change,
    )

    # Перемикач теми
    self.theme_switch = ft.Switch(
        label="Темна тема",
        value=self.current_theme == ft.ThemeMode.DARK,
        on_change=self.toggle_theme,
    )

    # Головна панель
    self.main_content = ft.Container(
        content=self.build_profiles_view(),
        expand=True,
        padding=20,
    )

    # Розмітка
    self.page.add(
        ft.Row(
            [
                self.nav_rail,
                ft.VerticalDivider(width=1),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    "Anty-Detect Browser",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.main_content,
                    ],
                    expand=True,
                    spacing=10,
                ),
            ],
            expand=True,
        )
    )

    # Оновлюємо список профілів
    self.refresh_profiles()
