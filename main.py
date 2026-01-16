"""
Головний файл додатка - Flet UI для керування браузерними профілями.
"""
import flet as ft
import threading
import re
import os
from typing import Optional, List, Dict
from database import Database
from browser_logic import BrowserManager


class AntyDetectBrowser:
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = Database()
        self.browser_manager = BrowserManager()
        self.current_page = "profiles"
        
        # Завантажуємо збережену тему (за замовчуванням світла)
        saved_theme = self.db.get_setting("theme", "light")
        if saved_theme == "dark":
            self.current_theme = ft.ThemeMode.DARK
        else:
            self.current_theme = ft.ThemeMode.LIGHT
        
        # Словник для зберігання статусів проксі
        self.proxy_statuses = {}
        self.selected_proxy_ids = set()
        self.select_all_proxies = False
        
        # Ініціалізація UI
        self.setup_page()
        self.setup_ui()

    def setup_page(self):
        """Налаштування сторінки."""
        self.page.title = "Anty-Detect Browser"
        self.page.theme_mode = self.current_theme
        self.page.window.width = 1200
        self.page.window.height = 800
        self.page.window.min_width = 800
        self.page.window.min_height = 600

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

    def toggle_theme(self, e):
        """Перемикає тему та зберігає вибір."""
        self.current_theme = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
        self.page.theme_mode = self.current_theme
        
        # Зберігаємо вибір теми
        theme_value = "dark" if self.current_theme == ft.ThemeMode.DARK else "light"
        self.db.set_setting("theme", theme_value)
        
        self.page.update()

    def on_nav_change(self, e):
        """Обробник зміни розділу в навігації."""
        index = e.control.selected_index
        if index == 0:
            self.current_page = "profiles"
            self.main_content.content = self.build_profiles_view()
        elif index == 1:
            self.current_page = "proxies"
            self.main_content.content = self.build_proxies_view()
        elif index == 2:
            self.current_page = "settings"
            self.main_content.content = self.build_settings_view()
        
        self.main_content.update()
        self.refresh_current_view()

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
                ft.Text(f"profiles/", size=14, color=ft.Colors.SECONDARY),
            ],
            spacing=10,
        )

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
        if hasattr(self, 'profiles_table'):
            self.profiles_table.update()

    def refresh_proxies(self):
        """Оновлює список проксі."""
        proxies = self.db.get_all_proxies()
        rows = []

        for proxy in proxies:
            address = f"{proxy['host']}:{proxy['port']}"
            is_selected = proxy['id'] in self.selected_proxy_ids

            select_checkbox = ft.Checkbox(
                value=is_selected,
                on_change=lambda e, pid=proxy['id']: self.toggle_proxy_selection(pid, e.control.value),
            )
            
            # Статус (буде оновлюватися при перевірці)
            status_text = ft.Text("Не перевірено", color=ft.Colors.GREY)
            if proxy['id'] in self.proxy_statuses:
                status_info = self.proxy_statuses[proxy['id']]
                if status_info['status'] == 'working':
                    status_text = ft.Text("✓ Працює", color=ft.Colors.GREEN)
                elif status_info['status'] == 'failed':
                    status_text = ft.Text("✗ Не працює", color=ft.Colors.RED)
                elif status_info['status'] == 'checking':
                    status_text = ft.Text("Перевіряється...", color=ft.Colors.ORANGE)

            status_cell = ft.Row(
                [
                    status_text,
                    ft.IconButton(
                        ft.Icons.CHECK_CIRCLE,
                        tooltip="Перевірити проксі",
                        icon_size=20,
                        on_click=lambda e, pid=proxy['id']: self.check_proxy(pid),
                    ),
                ],
                tight=True,
                spacing=5,
            )

            actions = ft.Row(
                [
                    ft.IconButton(
                        ft.Icons.EDIT,
                        tooltip="Редагувати",
                        on_click=lambda e, pid=proxy['id']: self.show_edit_proxy_dialog(pid),
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE,
                        tooltip="Видалити",
                        icon_color=ft.Colors.RED,
                        on_click=lambda e, pid=proxy['id']: self.delete_proxy(pid),
                    ),
                ],
                tight=True,
            )

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(select_checkbox),
                        ft.DataCell(ft.Text(proxy['name'])),
                        ft.DataCell(ft.Text(proxy['type'].upper())),
                        ft.DataCell(ft.Text(address)),
                        ft.DataCell(status_cell),
                        ft.DataCell(actions),
                    ]
                )
            )

        self.proxies_table.rows = rows
        if hasattr(self, 'proxies_table'):
            self.proxies_table.update()

        # Оновлюємо стан "обрати всі"
        self.select_all_proxies = len(proxies) > 0 and all(
            p['id'] in self.selected_proxy_ids for p in proxies
        )
        if self.proxies_table.columns:
            header_checkbox = self.proxies_table.columns[0].label
            if isinstance(header_checkbox, ft.Checkbox):
                header_checkbox.value = self.select_all_proxies
                header_checkbox.update()

    def refresh_current_view(self):
        """Оновлює поточний вид."""
        if self.current_page == "profiles":
            self.refresh_profiles()
        elif self.current_page == "proxies":
            self.refresh_proxies()

    def open_dialog(self, dialog: ft.AlertDialog):
        """Відкриває діалог, сумісно з різними версіями Flet."""
        if dialog not in self.page.overlay:
            self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def close_dialog(self, dialog: ft.AlertDialog):
        """Закриває діалог."""
        dialog.open = False
        self.page.update()

    def run_ui(self, func):
        """Безпечно виконує синхронну UI-дію через run_task."""
        async def _run():
            func()

        self.page.run_task(_run)

    def toggle_proxy_selection(self, proxy_id: int, selected: bool):
        if selected:
            self.selected_proxy_ids.add(proxy_id)
        else:
            self.selected_proxy_ids.discard(proxy_id)

    def toggle_select_all_proxies(self, selected: bool):
        proxies = self.db.get_all_proxies()
        if selected:
            self.selected_proxy_ids = {p['id'] for p in proxies}
        else:
            self.selected_proxy_ids.clear()
        self.refresh_proxies()

    def check_selected_proxies(self, e):
        if not self.selected_proxy_ids:
            self.show_error_dialog("Оберіть проксі для перевірки")
            return

        for proxy_id in list(self.selected_proxy_ids):
            self.check_proxy(proxy_id)

    def show_create_profile_dialog(self, e):
        """Показує діалог створення профілю."""
        name_field = ft.TextField(label="Назва профілю", autofocus=True)
        notes_field = ft.TextField(label="Нотатки", multiline=True, max_lines=3)
        tags_field = ft.TextField(label="Теги (через кому)")
        
        # Вибір проксі
        proxies = self.db.get_all_proxies()
        proxy_options = [ft.dropdown.Option(key=None, text="Без проксі")]
        for proxy in proxies:
            proxy_options.append(ft.dropdown.Option(key=proxy['id'], text=proxy['name']))
        
        proxy_dropdown = ft.Dropdown(
            label="Проксі",
            options=proxy_options,
        )

        def create_profile(e):
            if not name_field.value:
                name_field.error_text = "Введіть назву профілю"
                dialog.update()
                return

            profile_id = self.browser_manager.generate_profile_id()
            self.browser_manager.create_profile_folder(profile_id)

            proxy_id = proxy_dropdown.value if proxy_dropdown.value else None

            self.db.create_profile(
                name=name_field.value,
                profile_id=profile_id,
                notes=notes_field.value or "",
                proxy_id=proxy_id,
                tags=tags_field.value or "",
            )

            dialog.open = False
            self.page.update()
            self.refresh_profiles()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Створити профіль"),
            content=ft.Container(
                content=ft.Column(
                    [name_field, notes_field, tags_field, proxy_dropdown],
                    tight=True,
                    width=400,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: self.close_dialog(dialog)),
                ft.TextButton("Створити", on_click=create_profile),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.open_dialog(dialog)

    def show_edit_profile_dialog(self, profile_id: str):
        """Показує діалог редагування профілю."""
        profile = self.db.get_profile_by_id(profile_id)
        if not profile:
            return

        name_field = ft.TextField(label="Назва профілю", value=profile['name'], autofocus=True)
        notes_field = ft.TextField(label="Нотатки", value=profile.get('notes', '') or '', multiline=True, max_lines=3)
        tags_field = ft.TextField(label="Теги (через кому)", value=profile.get('tags', '') or '')
        
        # Вибір проксі
        proxies = self.db.get_all_proxies()
        proxy_options = [ft.dropdown.Option(key=None, text="Без проксі")]
        for proxy in proxies:
            proxy_options.append(ft.dropdown.Option(key=proxy['id'], text=proxy['name']))
        
        proxy_dropdown = ft.Dropdown(
            label="Проксі",
            options=proxy_options,
            value=profile.get('proxy_id'),
        )

        def update_profile(e):
            if not name_field.value:
                name_field.error_text = "Введіть назву профілю"
                dialog.update()
                return

            self.db.update_profile(
                profile_id=profile_id,
                name=name_field.value,
                notes=notes_field.value or "",
                proxy_id=proxy_dropdown.value if proxy_dropdown.value else None,
                tags=tags_field.value or "",
            )

            dialog.open = False
            self.page.update()
            self.refresh_profiles()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редагувати профіль"),
            content=ft.Container(
                content=ft.Column(
                    [name_field, notes_field, tags_field, proxy_dropdown],
                    tight=True,
                    width=400,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: self.close_dialog(dialog)),
                ft.TextButton("Зберегти", on_click=update_profile),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.open_dialog(dialog)

    def show_create_proxy_dialog(self, e):
        """Показує діалог створення проксі."""
        name_field = ft.TextField(
            label="Назва проксі",
            autofocus=True,
            hint_text="Наприклад: US Proxy 1"
        )
        type_field = ft.Dropdown(
            label="Тип",
            options=[
                ft.dropdown.Option("http", "HTTP"),
                ft.dropdown.Option("https", "HTTPS"),
                ft.dropdown.Option("socks4", "SOCKS4"),
                ft.dropdown.Option("socks5", "SOCKS5"),
            ],
            value="http",
        )
        host_field = ft.TextField(
            label="IP адреса або хост",
            hint_text="192.168.1.1 або proxy.example.com"
        )
        port_field = ft.TextField(
            label="Порт",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="8080"
        )
        username_field = ft.TextField(
            label="Логін (опціонально)",
            hint_text="username"
        )
        password_field = ft.TextField(
            label="Пароль (опціонально)",
            password=True,
            can_reveal_password=True
        )

        error_text = ft.Text(value="", color=ft.Colors.RED, size=12, visible=False)

        def validate_and_create(e):
            # Скидаємо помилки
            name_field.error_text = None
            host_field.error_text = None
            port_field.error_text = None
            error_text.visible = False

            # Валідація
            is_valid = True

            if not name_field.value or not name_field.value.strip():
                name_field.error_text = "Введіть назву"
                is_valid = False

            if not host_field.value or not host_field.value.strip():
                host_field.error_text = "Введіть IP або хост"
                is_valid = False

            if not port_field.value or not port_field.value.strip():
                port_field.error_text = "Введіть порт"
                is_valid = False
            else:
                try:
                    port = int(port_field.value)
                    if port < 1 or port > 65535:
                        port_field.error_text = "Порт має бути від 1 до 65535"
                        is_valid = False
                except ValueError:
                    port_field.error_text = "Введіть правильний порт (число)"
                    is_valid = False

            if not is_valid:
                dialog.content.update()
                return

            try:
                port = int(port_field.value)
                proxy_name = name_field.value.strip()
                self.db.create_proxy(
                    name=proxy_name,
                    type=type_field.value,
                    host=host_field.value.strip(),
                    port=port,
                    username=username_field.value.strip() if username_field.value else None,
                    password=password_field.value if password_field.value else None,
                )

                dialog.open = False
                self.page.update()
                self.refresh_proxies()
                self.show_success_dialog(f"Проксі '{proxy_name}' успішно додано")
            except Exception as ex:
                error_text.value = f"Помилка: {str(ex)}"
                error_text.visible = True
                dialog.content.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Додати проксі"),
            content=ft.Container(
                content=ft.Column(
                    [
                        error_text,
                        name_field,
                        type_field,
                        host_field,
                        port_field,
                        username_field,
                        password_field,
                        ft.Text(
                            "Підказка: Логін і пароль потрібні лише якщо проксі вимагає авторизацію",
                            size=11,
                            color=ft.Colors.SECONDARY,
                        )
                    ],
                    tight=True,
                    width=400,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=450,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: self.close_dialog(dialog)),
                ft.Button("Додати", on_click=validate_and_create),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.open_dialog(dialog)

    def show_edit_proxy_dialog(self, proxy_id: int):
        """Показує діалог редагування проксі."""
        proxy = self.db.get_proxy_by_id(proxy_id)
        if not proxy:
            return

        name_field = ft.TextField(
            label="Назва проксі",
            value=proxy['name'],
            autofocus=True
        )
        type_field = ft.Dropdown(
            label="Тип",
            options=[
                ft.dropdown.Option("http", "HTTP"),
                ft.dropdown.Option("https", "HTTPS"),
                ft.dropdown.Option("socks4", "SOCKS4"),
                ft.dropdown.Option("socks5", "SOCKS5"),
            ],
            value=proxy['type'],
        )
        host_field = ft.TextField(
            label="IP адреса або хост",
            value=proxy['host']
        )
        port_field = ft.TextField(
            label="Порт",
            value=str(proxy['port']),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        username_field = ft.TextField(
            label="Логін (опціонально)",
            value=proxy.get('username') or ''
        )
        password_field = ft.TextField(
            label="Пароль (опціонально)",
            value=proxy.get('password') or '',
            password=True,
            can_reveal_password=True
        )

        error_text = ft.Text(value="", color=ft.Colors.RED, size=12, visible=False)

        def validate_and_update(e):
            # Скидаємо помилки
            name_field.error_text = None
            host_field.error_text = None
            port_field.error_text = None
            error_text.visible = False

            # Валідація
            is_valid = True

            if not name_field.value or not name_field.value.strip():
                name_field.error_text = "Введіть назву"
                is_valid = False

            if not host_field.value or not host_field.value.strip():
                host_field.error_text = "Введіть IP або хост"
                is_valid = False

            if not port_field.value or not port_field.value.strip():
                port_field.error_text = "Введіть порт"
                is_valid = False
            else:
                try:
                    port = int(port_field.value)
                    if port < 1 or port > 65535:
                        port_field.error_text = "Порт має бути від 1 до 65535"
                        is_valid = False
                except ValueError:
                    port_field.error_text = "Введіть правильний порт (число)"
                    is_valid = False

            if not is_valid:
                dialog.content.update()
                return

            try:
                port = int(port_field.value)
                proxy_name = name_field.value.strip()
                self.db.update_proxy(
                    proxy_id=proxy_id,
                    name=proxy_name,
                    type=type_field.value,
                    host=host_field.value.strip(),
                    port=port,
                    username=username_field.value.strip() if username_field.value else None,
                    password=password_field.value if password_field.value else None,
                )

                dialog.open = False
                self.page.update()
                self.refresh_proxies()
                self.show_success_dialog(f"Проксі '{proxy_name}' успішно оновлено")
            except Exception as ex:
                error_text.value = f"Помилка: {str(ex)}"
                error_text.visible = True
                dialog.content.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редагувати проксі"),
            content=ft.Container(
                content=ft.Column(
                    [
                        error_text,
                        name_field,
                        type_field,
                        host_field,
                        port_field,
                        username_field,
                        password_field,
                    ],
                    tight=True,
                    width=400,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=450,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: self.close_dialog(dialog)),
                ft.Button("Зберегти", on_click=validate_and_update),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.open_dialog(dialog)

    def toggle_profile(self, e):
        """Запускає або зупиняє профіль."""
        # Отримуємо profile_id з data атрибута кнопки
        profile_id = e.control.data if hasattr(e.control, 'data') else None
        
        if not profile_id:
            return
            
        is_running = self.browser_manager.is_profile_running(profile_id)

        if is_running:
            self.browser_manager.stop_profile(profile_id)
            self.refresh_profiles()
        else:
            # Запускаємо в окремому потоці
            def launch():
                try:
                    profile = self.db.get_profile_by_id(profile_id)
                    proxy_data = None
                    if profile and profile.get('proxy_id'):
                        proxy = self.db.get_proxy_by_id(profile['proxy_id'])
                        if proxy:
                            proxy_data = dict(proxy)
                    
                    self.browser_manager.launch_profile(profile_id, proxy_data, headless=False)
                    # Оновлюємо інтерфейс після успішного запуску
                    import time
                    time.sleep(0.5)
                    self.run_ui(self.refresh_profiles)
                except Exception as ex:
                    print(f"Помилка запуску профілю {profile_id}: {ex}")
                    # Показуємо повідомлення про помилку
                    self.run_ui(lambda: self.show_error_dialog(f"Помилка запуску профілю: {ex}"))

            thread = threading.Thread(target=launch, daemon=True)
            thread.start()
            # Оновлюємо одразу для показу статусу "запускається"
            self.refresh_profiles()

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

    def check_proxy(self, proxy_id: int):
        """Перевіряє валідність проксі."""
        proxy = self.db.get_proxy_by_id(proxy_id)
        if not proxy:
            return

        # Встановлюємо статус "перевіряється"
        self.proxy_statuses[proxy_id] = {'status': 'checking'}
        self.refresh_proxies()

        def check_in_thread():
            try:
                import requests
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                # Формуємо проксі для requests
                proxy_url = f"{proxy['type']}://"
                if proxy.get('username') and proxy.get('password'):
                    proxy_url += f"{proxy['username']}:{proxy['password']}@"
                proxy_url += f"{proxy['host']}:{proxy['port']}"

                proxies_dict = {
                    'http': proxy_url,
                    'https': proxy_url
                }

                # Налаштування сесії з таймаутом
                session = requests.Session()
                retry = Retry(total=1, backoff_factor=0.1)
                adapter = HTTPAdapter(max_retries=retry)
                session.mount('http://', adapter)
                session.mount('https://', adapter)

                # Перевіряємо через google.com з таймаутом 10 секунд
                response = session.get(
                    'http://www.google.com',
                    proxies=proxies_dict,
                    timeout=10,
                    allow_redirects=True
                )

                if response.status_code == 200:
                    self.proxy_statuses[proxy_id] = {'status': 'working'}
                else:
                    self.proxy_statuses[proxy_id] = {'status': 'failed'}
            except Exception as e:
                # Спробуємо альтернативний метод через Playwright для SOCKS
                if proxy['type'] in ['socks4', 'socks5']:
                    try:
                        self.check_proxy_with_playwright(proxy, proxy_id)
                    except Exception as pw_ex:
                        self.proxy_statuses[proxy_id] = {'status': 'failed', 'error': str(e)}
                else:
                    self.proxy_statuses[proxy_id] = {'status': 'failed', 'error': str(e)}
            finally:
                # Оновлюємо UI
                self.run_ui(self.refresh_proxies)

        thread = threading.Thread(target=check_in_thread, daemon=True)
        thread.start()

    def check_proxy_with_playwright(self, proxy: Dict, proxy_id: int):
        """Перевіряє проксі через Playwright (для SOCKS та складних випадків)."""
        try:
            from playwright.sync_api import sync_playwright
            
            proxy_config = self.browser_manager.get_proxy_config(proxy)
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(proxy=proxy_config)
                page = context.new_page()
                
                # Встановлюємо таймаут на 15 секунд
                page.set_default_timeout(15000)
                
                # Намагаємось відкрити Google
                page.goto('https://www.google.com')
                
                # Перевіряємо, чи завантажилась сторінка
                if 'google' in page.url.lower():
                    self.proxy_statuses[proxy_id] = {'status': 'working'}
                else:
                    self.proxy_statuses[proxy_id] = {'status': 'failed'}
                
                context.close()
                browser.close()
        except Exception as e:
            self.proxy_statuses[proxy_id] = {'status': 'failed', 'error': str(e)}

    def check_all_proxies(self, e):
        """Перевіряє всі проксі в списку."""
        proxies = self.db.get_all_proxies()
        
        if not proxies:
            self.show_error_dialog("Немає проксі для перевірки")
            return

        # Встановлюємо статус "перевіряється" для всіх
        for proxy in proxies:
            self.proxy_statuses[proxy['id']] = {'status': 'checking'}
        
        self.refresh_proxies()

        def check_all_in_thread():
            import time
            checked = 0
            
            for proxy in proxies:
                # Запускаємо перевірку кожного проксі
                self.check_proxy(proxy['id'])
                checked += 1
                
                # Невелика затримка між перевірками
                time.sleep(0.2)
            
            # Показуємо результат після завершення
            time.sleep(2)  # Даємо час на завершення всіх перевірок
            
            working = sum(1 for pid, status in self.proxy_statuses.items() if status.get('status') == 'working')
            failed = sum(1 for pid, status in self.proxy_statuses.items() if status.get('status') == 'failed')
            
            self.run_ui(
                lambda: self.show_success_dialog(
                    f"Перевірка завершена\n\n✓ Працюють: {working}\n✗ Не працюють: {failed}"
                )
            )

        thread = threading.Thread(target=check_all_in_thread, daemon=True)
        thread.start()

    def parse_proxy_line(self, line: str) -> Optional[Dict]:
        """Парсить рядок з проксі у форматі: ip:port, ip:port:user:pass, type://ip:port:user:pass, type://user:pass@ip:port"""
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        proxy_type = 'http'
        host = None
        port = None
        username = None
        password = None

        # Формат 1: type://user:pass@host:port або type://host:port
        protocol_match = re.match(r'^(https?|socks[45])://', line, re.IGNORECASE)
        if protocol_match:
            proxy_type = protocol_match.group(1).lower()
            line = line[len(protocol_match.group(0)):]
        
        # Перевіряємо наявність user:pass@
        auth_match = re.match(r'^([^:@]+):([^@]+)@(.+)$', line)
        if auth_match:
            username = auth_match.group(1)
            password = auth_match.group(2)
            line = auth_match.group(3)
        
        # Тепер розбираємо host:port або host:port:user:pass (якщо немає @)
        if not username:
            parts = line.split(':')
            if len(parts) >= 2:
                host = parts[0]
                try:
                    port = int(parts[1])
                except ValueError:
                    return None
                
                # Перевіряємо чи є логін і пароль після порту
                if len(parts) >= 3:
                    username = parts[2] if parts[2] else None
                if len(parts) >= 4:
                    password = parts[3] if parts[3] else None
            else:
                return None
        else:
            # Якщо вже є username з @, просто розбираємо host:port
            parts = line.split(':')
            if len(parts) >= 2:
                host = parts[0]
                try:
                    port = int(parts[1])
                except ValueError:
                    return None
            else:
                return None

        if not host or not port:
            return None

        # Валідація типу
        if proxy_type not in ['http', 'https', 'socks4', 'socks5']:
            proxy_type = 'http'

        return {
            'type': proxy_type,
            'host': host,
            'port': port,
            'username': username,
            'password': password
        }

    def import_proxies_from_file(self, file_path: str):
        """Імпортує проксі з файлу за шляхом."""
        if not file_path or not os.path.exists(file_path):
            self.show_error_dialog("Файл не знайдено")
            return

        try:
            imported_count = 0
            failed_count = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    proxy_data = self.parse_proxy_line(line)
                    if proxy_data:
                        try:
                            # Генеруємо назву якщо не вказана
                            name = f"Проксі {proxy_data['host']}:{proxy_data['port']}"
                            
                            self.db.create_proxy(
                                name=name,
                                type=proxy_data['type'],
                                host=proxy_data['host'],
                                port=proxy_data['port'],
                                username=proxy_data.get('username'),
                                password=proxy_data.get('password')
                            )
                            imported_count += 1
                        except Exception as ex:
                            failed_count += 1
                            print(f"Помилка імпорту рядка {line_num}: {ex}")

            # Показуємо результат
            if imported_count > 0:
                self.show_success_dialog(f"Успішно додано {imported_count} проксі")
                self.refresh_proxies()
            else:
                self.show_error_dialog("Не вдалося імпортувати жодного проксі")

        except Exception as ex:
            self.show_error_dialog(f"Помилка читання файлу: {ex}")

    def show_import_proxy_dialog(self, e):
        """Показує діалог імпорту проксі з файлу."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            file_path = filedialog.askopenfilename(
                title="Виберіть файл з проксі",
                filetypes=[("Text files", "*.txt")]
            )
            root.destroy()

            if not file_path:
                return

            self.import_proxies_from_file(file_path)
        except Exception as ex:
            self.show_error_dialog(f"Помилка відкриття діалогу файлу: {ex}")

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


def main(page: ft.Page):
    app = AntyDetectBrowser(page)
    
    # Оновлюємо статуси профілів періодично
    def update_statuses():
        import time
        while True:
            time.sleep(2)
            try:
                if page.window_alive:
                    app.run_ui(app.refresh_profiles)
            except:
                break

    status_thread = threading.Thread(target=update_statuses, daemon=True)
    status_thread.start()


if __name__ == "__main__":
    ft.run(main)

