"""
Головний файл додатка - Flet UI для керування браузерними профілями.
"""
import flet as ft
import threading
import re
import os
import json
from urllib.parse import urlparse
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
        self._updating_select_all = False
        
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
                    status_text = ft.Text("Працює", color=ft.Colors.GREEN)
                elif status_info['status'] == 'failed':
                    error_msg = status_info.get('error')
                    status_text = ft.Text("Не працює", color=ft.Colors.RED, tooltip=error_msg or None)
                elif status_info['status'] == 'checking':
                    status_text = ft.Text("Перевіряється...", color=ft.Colors.ORANGE)

            icon_color = None
            icon_name = ft.Icons.CHECK_CIRCLE_OUTLINE
            if proxy['id'] in self.proxy_statuses:
                status_value = self.proxy_statuses[proxy['id']].get('status')
                if status_value == 'working':
                    icon_color = ft.Colors.GREEN
                    icon_name = ft.Icons.CHECK_CIRCLE
                elif status_value == 'failed':
                    icon_color = ft.Colors.RED
                    icon_name = ft.Icons.CANCEL

            status_cell = ft.Row(
                [
                    status_text,
                    ft.IconButton(
                        icon_name,
                        tooltip="Перевірити проксі",
                        icon_size=20,
                        icon_color=icon_color,
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
                self._updating_select_all = True
                header_checkbox.value = self.select_all_proxies
                header_checkbox.update()
                self._updating_select_all = False

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

    def generate_user_agent_for_os(self, os_name: str) -> str:
        """Генерує User-Agent для обраної ОС."""
        ua_map = {
            "Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "macOS": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Linux": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Android": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "iOS": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1",
        }
        return ua_map.get(os_name, ua_map["Windows"])

    def parse_open_tabs(self, value: str) -> List[str]:
        """Парсить список URL з поля вкладок."""
        if not value:
            return []
        lines = [line.strip() for line in value.splitlines()]
        return [line for line in lines if line]

    def validate_open_tabs(self, value: str) -> List[str]:
        """Повертає список некоректних URL."""
        invalid = []
        for url in self.parse_open_tabs(value):
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                invalid.append(url)
        return invalid

    def build_profile_launch_settings(self, profile: Dict) -> Dict:
        """Готує налаштування запуску профілю для Playwright."""
        timezone_id = None
        if profile.get("timezone_mode") == "custom":
            timezone_id = profile.get("timezone_value")

        geolocation = None
        permissions = None
        if profile.get("geolocation_mode") == "manual":
            if profile.get("geolocation_lat") is not None and profile.get("geolocation_lon") is not None:
                geolocation = {
                    "latitude": float(profile.get("geolocation_lat")),
                    "longitude": float(profile.get("geolocation_lon")),
                }
                permissions = ["geolocation"]
        elif profile.get("geolocation_mode") == "block":
            permissions = []

        locale = None
        extra_http_headers = None
        if profile.get("language_mode") == "custom" and profile.get("languages"):
            try:
                languages = json.loads(profile.get("languages"))
            except Exception:
                languages = []
            if languages:
                locale = languages[0]
                extra_http_headers = {"Accept-Language": ",".join(languages)}

        return {
            "user_agent": profile.get("user_agent") or None,
            "locale": locale,
            "timezone_id": timezone_id,
            "geolocation": geolocation,
            "permissions": permissions,
            "extra_http_headers": extra_http_headers,
        }

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
        if self._updating_select_all:
            return
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

        # Скидаємо вибір після запуску перевірки
        self.selected_proxy_ids.clear()
        self.refresh_proxies()

    def show_create_profile_dialog(self, e):
        """Показує діалог створення профілю."""
        name_field = ft.TextField(label="Назва профілю", autofocus=True)
        os_dropdown = ft.Dropdown(
            label="Operating System",
            options=[
                ft.dropdown.Option("Windows"),
                ft.dropdown.Option("macOS"),
                ft.dropdown.Option("Linux"),
                ft.dropdown.Option("Android"),
                ft.dropdown.Option("iOS"),
            ],
            value="Windows",
        )
        ua_field = ft.TextField(label="User-Agent")
        ua_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Згенерувати User-Agent",
        )
        open_tabs_field = ft.TextField(
            label="Стартові вкладки",
            multiline=True,
            min_lines=1,
            max_lines=5,
            hint_text="https://example.com\nhttps://another.com",
        )
        open_tabs_error = ft.Text(value="", color=ft.Colors.RED, size=12, visible=False)

        notes_field = ft.TextField(label="Нотатки", multiline=True, max_lines=3)
        tags_field = ft.TextField(label="Теги (через кому)")

        timezone_options = [
            "UTC",
            "Europe/Kyiv",
            "Europe/London",
            "Europe/Warsaw",
            "Europe/Berlin",
            "America/New_York",
            "America/Chicago",
            "America/Los_Angeles",
            "Asia/Tokyo",
            "Asia/Singapore",
            "Asia/Dubai",
            "Australia/Sydney",
        ]

        timezone_mode = ft.RadioGroup(
            value="ip",
            content=ft.Column(
                [
                    ft.Radio(value="ip", label="На основі IP"),
                    ft.Radio(value="system", label="Реальний (системний)"),
                    ft.Radio(value="custom", label="Настроюваний (UTC)"),
                ],
                spacing=5,
            ),
        )
        timezone_dropdown = ft.Dropdown(
            label="Часовий пояс",
            options=[ft.dropdown.Option(tz) for tz in timezone_options],
            visible=False,
        )

        geolocation_mode = ft.RadioGroup(
            value="ip",
            content=ft.Column(
                [
                    ft.Radio(value="ip", label="На основі IP"),
                    ft.Radio(value="manual", label="Налаштувати"),
                    ft.Radio(value="block", label="Блокувати"),
                ],
                spacing=5,
            ),
        )
        geo_lat_field = ft.TextField(label="Latitude", keyboard_type=ft.KeyboardType.NUMBER, visible=False)
        geo_lon_field = ft.TextField(label="Longitude", keyboard_type=ft.KeyboardType.NUMBER, visible=False)

        language_mode = ft.RadioGroup(
            value="ip",
            content=ft.Column(
                [
                    ft.Radio(value="ip", label="На основі IP"),
                    ft.Radio(value="custom", label="Налаштувати"),
                ],
                spacing=5,
            ),
        )

        language_options = [
            "en-US", "uk-UA", "ru-RU", "de-DE", "fr-FR", "es-ES",
            "it-IT", "pl-PL", "tr-TR", "zh-CN", "ja-JP",
        ]
        language_checkboxes = [ft.Checkbox(label=lang, value=False) for lang in language_options]
        languages_container = ft.Column(language_checkboxes, visible=False, spacing=5)

        # Проксі
        proxies = self.db.get_all_proxies()
        proxy_mode = ft.RadioGroup(
            value="none",
            content=ft.Column(
                [
                    ft.Radio(value="none", label="Без проксі"),
                    ft.Radio(value="manual", label="Ввести проксі"),
                    ft.Radio(value="saved", label="Збережені проксі"),
                ],
                spacing=5,
            ),
        )

        proxy_type_field = ft.Dropdown(
            label="Тип проксі",
            options=[
                ft.dropdown.Option("http", "HTTP"),
                ft.dropdown.Option("https", "HTTPS"),
                ft.dropdown.Option("socks4", "SOCKS4"),
                ft.dropdown.Option("socks5", "SOCKS5"),
            ],
            value="http",
            visible=False,
        )
        proxy_host_field = ft.TextField(
            label="IP адреса або хост",
            hint_text="192.168.1.1 або proxy.example.com",
            visible=False,
        )
        proxy_port_field = ft.TextField(
            label="Порт",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="8080",
            visible=False,
        )
        proxy_user_field = ft.TextField(
            label="Логін (опціонально)",
            visible=False,
        )
        proxy_pass_field = ft.TextField(
            label="Пароль (опціонально)",
            password=True,
            can_reveal_password=True,
            visible=False,
        )

        def format_proxy_label(proxy: Dict) -> str:
            name = proxy.get("name") or ""
            host = proxy.get("host") or ""
            port = proxy.get("port")
            host_port = f"{host}:{port}" if host and port else ""
            if host_port and host_port not in name:
                return f"{name} ({host_port})" if name else host_port
            return name or host_port

        selected_saved_proxy_id = {"value": None}
        selected_saved_proxy_label = ""

        saved_proxy_display = ft.TextField(
            label="Збережені проксі",
            value=selected_saved_proxy_label,
            read_only=True,
            visible=False,
        )
        proxy_error = ft.Text(value="", color=ft.Colors.RED, size=12, visible=False)
        proxy_picker_state = {"open": False}

        def open_saved_proxy_picker(e=None):
            if proxy_picker_state["open"]:
                return
            proxy_picker_state["open"] = True
            search_field = ft.TextField(
                label="Пошук",
                hint_text="назва або IP",
                autofocus=True,
            )

            list_view = ft.ListView(expand=True, spacing=0, auto_scroll=False)
            list_container = ft.Container(
                content=list_view,
                expand=True,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                padding=5,
            )

            def proxy_subtitle(proxy: Dict) -> str:
                name = proxy.get("name") or ""
                host = proxy.get("host") or ""
                port = proxy.get("port")
                host_port = f"{host}:{port}" if host and port else ""
                if host_port and host_port not in name:
                    return host_port
                return ""

            def render_list(query: str = ""):
                q = (query or "").strip().lower()
                filtered = []
                for proxy in proxies:
                    name = (proxy.get("name") or "").lower()
                    host = (proxy.get("host") or "").lower()
                    port = str(proxy.get("port") or "")
                    if not q or q in name or q in host or q in port:
                        filtered.append(proxy)

                tiles = []
                for p in filtered:
                    tiles.append(
                        ft.ListTile(
                            leading=ft.Container(
                                content=ft.Text(str(p.get("id", "")), size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6,
                            ),
                            title=ft.Text(format_proxy_label(p)),
                            subtitle=ft.Text(proxy_subtitle(p)) if proxy_subtitle(p) else None,
                            on_click=lambda e, pid=p["id"], label=format_proxy_label(p): select_proxy(pid, label),
                        )
                    )
                    tiles.append(ft.Divider(height=1))

                if tiles:
                    tiles = tiles[:-1]

                list_view.controls = tiles

                if proxy_picker:
                    try:
                        if proxy_picker.page:
                            list_view.update()
                    except RuntimeError:
                        pass

            def select_proxy(proxy_id: int, label: str):
                selected_saved_proxy_id["value"] = str(proxy_id)
                saved_proxy_display.value = label
                if dialog:
                    try:
                        if dialog.page:
                            saved_proxy_display.update()
                    except RuntimeError:
                        pass

                self.close_dialog(proxy_picker)
                proxy_picker_state["open"] = False

            search_field.on_change = lambda e: render_list(search_field.value)

            proxy_picker = ft.AlertDialog(
                modal=True,
                title=ft.Text("Вибір проксі"),
                content=ft.Container(
                    content=ft.Column(
                        [search_field, list_container],
                        spacing=10,
                        expand=True,
                    ),
                    width=450,
                    height=500,
                ),
                actions=[
                    ft.TextButton("Закрити", on_click=lambda e: (self.close_dialog(proxy_picker), proxy_picker_state.__setitem__("open", False))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            render_list()
            self.open_dialog(proxy_picker)

        create_button = ft.Button("Створити профіль", disabled=True)

        def update_visibility(e=None):
            timezone_dropdown.visible = timezone_mode.value == "custom"
            geo_lat_field.visible = geolocation_mode.value == "manual"
            geo_lon_field.visible = geolocation_mode.value == "manual"
            languages_container.visible = language_mode.value == "custom"
            is_manual = proxy_mode.value == "manual"
            is_saved = proxy_mode.value == "saved"

            proxy_type_field.visible = is_manual
            proxy_host_field.visible = is_manual
            proxy_port_field.visible = is_manual
            proxy_user_field.visible = is_manual
            proxy_pass_field.visible = is_manual

            saved_proxy_display.visible = is_saved
            proxy_error.visible = False
            if dialog:
                try:
                    if dialog.page:
                        dialog.content.update()
                except RuntimeError:
                    pass

        def get_selected_languages() -> List[str]:
            return [cb.label for cb in language_checkboxes if cb.value]

        preview_title = ft.Text("Огляд", weight=ft.FontWeight.BOLD)
        preview_os = ft.Text("OS: —")
        preview_ua = ft.Text("User-Agent: —", max_lines=2)
        preview_tz = ft.Text("Часовий пояс: —")
        preview_geo = ft.Text("Геолокація: —")
        preview_lang = ft.Text("Мова: —")

        def update_preview():
            preview_os.value = f"OS: {os_dropdown.value or '—'}"
            preview_ua.value = f"User-Agent: {ua_field.value or '—'}"
            tz_value = "—"
            if timezone_mode.value == "ip":
                tz_value = "На основі IP"
            elif timezone_mode.value == "system":
                tz_value = "Реальний (системний)"
            elif timezone_mode.value == "custom":
                tz_value = timezone_dropdown.value or "—"
            preview_tz.value = f"Часовий пояс: {tz_value}"

            geo_value = "—"
            if geolocation_mode.value == "ip":
                geo_value = "На основі IP"
            elif geolocation_mode.value == "block":
                geo_value = "Блокувати"
            elif geolocation_mode.value == "manual":
                lat = geo_lat_field.value or "—"
                lon = geo_lon_field.value or "—"
                geo_value = f"{lat}, {lon}"
            preview_geo.value = f"Геолокація: {geo_value}"

            if language_mode.value == "ip":
                preview_lang.value = "Мова: На основі IP"
            else:
                langs = get_selected_languages()
                preview_lang.value = f"Мова: {', '.join(langs) if langs else '—'}"

        preview_title = ft.Text("Огляд", weight=ft.FontWeight.BOLD)
        preview_os = ft.Text("OS: —")
        preview_ua = ft.Text("User-Agent: —", max_lines=2)
        preview_tz = ft.Text("Часовий пояс: —")
        preview_geo = ft.Text("Геолокація: —")
        preview_lang = ft.Text("Мова: —")

        def update_preview():
            preview_os.value = f"OS: {os_dropdown.value or '—'}"
            preview_ua.value = f"User-Agent: {ua_field.value or '—'}"
            tz_value = "—"
            if timezone_mode.value == "ip":
                tz_value = "На основі IP"
            elif timezone_mode.value == "system":
                tz_value = "Реальний (системний)"
            elif timezone_mode.value == "custom":
                tz_value = timezone_dropdown.value or "—"
            preview_tz.value = f"Часовий пояс: {tz_value}"

            geo_value = "—"
            if geolocation_mode.value == "ip":
                geo_value = "На основі IP"
            elif geolocation_mode.value == "block":
                geo_value = "Блокувати"
            elif geolocation_mode.value == "manual":
                lat = geo_lat_field.value or "—"
                lon = geo_lon_field.value or "—"
                geo_value = f"{lat}, {lon}"
            preview_geo.value = f"Геолокація: {geo_value}"

            if language_mode.value == "ip":
                preview_lang.value = "Мова: На основі IP"
            else:
                langs = get_selected_languages()
                preview_lang.value = f"Мова: {', '.join(langs) if langs else '—'}"

        def validate_form() -> bool:
            is_valid = True

            # Валідація URL
            invalid_urls = self.validate_open_tabs(open_tabs_field.value or "")
            if invalid_urls:
                open_tabs_error.value = "Некоректні URL: " + ", ".join(invalid_urls)
                open_tabs_error.visible = True
                is_valid = False
            else:
                open_tabs_error.visible = False

            # Часовий пояс
            if timezone_mode.value == "custom" and not timezone_dropdown.value:
                timezone_dropdown.error_text = "Оберіть часовий пояс"
                is_valid = False
            else:
                timezone_dropdown.error_text = None

            # Геолокація
            if geolocation_mode.value == "manual":
                try:
                    lat = float(geo_lat_field.value) if geo_lat_field.value else None
                    lon = float(geo_lon_field.value) if geo_lon_field.value else None
                    if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        geo_lat_field.error_text = "Введіть коректну широту (-90..90)"
                        geo_lon_field.error_text = "Введіть коректну довготу (-180..180)"
                        is_valid = False
                    else:
                        geo_lat_field.error_text = None
                        geo_lon_field.error_text = None
                except ValueError:
                    geo_lat_field.error_text = "Введіть число"
                    geo_lon_field.error_text = "Введіть число"
                    is_valid = False
            else:
                geo_lat_field.error_text = None
                geo_lon_field.error_text = None

            # Мова
            if language_mode.value == "custom" and not get_selected_languages():
                is_valid = False

            # Проксі
            if proxy_mode.value == "manual":
                proxy_host_field.error_text = None
                proxy_port_field.error_text = None
                if not proxy_host_field.value or not proxy_host_field.value.strip():
                    proxy_host_field.error_text = "Введіть IP або хост"
                    is_valid = False
                if not proxy_port_field.value or not proxy_port_field.value.strip():
                    proxy_port_field.error_text = "Введіть порт"
                    is_valid = False
                else:
                    try:
                        port_val = int(proxy_port_field.value)
                        if port_val < 1 or port_val > 65535:
                            proxy_port_field.error_text = "Порт має бути від 1 до 65535"
                            is_valid = False
                    except ValueError:
                        proxy_port_field.error_text = "Введіть правильний порт (число)"
                        is_valid = False
            elif proxy_mode.value == "saved":
                if not selected_saved_proxy_id["value"]:
                    proxy_error.value = "Оберіть збережений проксі"
                    proxy_error.visible = True
                    is_valid = False

            create_button.disabled = not is_valid
            if dialog:
                try:
                    if dialog.page:
                        dialog.content.update()
                except RuntimeError:
                    pass
            return is_valid

        def on_generate_ua(e):
            ua_field.value = self.generate_user_agent_for_os(os_dropdown.value)
            ua_field.update()
            update_preview()
            update_preview()

        ua_button.on_click = on_generate_ua

        def create_profile(e):
            if not validate_form():
                return

            profile_id = self.browser_manager.generate_profile_id()
            self.browser_manager.create_profile_folder(profile_id)

            profile_name = name_field.value.strip() if name_field.value else ""
            if not profile_name:
                profile_name = f"ID_{self.db.get_next_profile_number()}"

            proxy_id = None
            if proxy_mode.value == "saved" and selected_saved_proxy_id["value"]:
                proxy_id = int(selected_saved_proxy_id["value"])
            elif proxy_mode.value == "manual":
                port_val = int(proxy_port_field.value)
                proxy_name = f"Proxy {proxy_host_field.value.strip()}:{port_val}"
                proxy_id = self.db.create_proxy(
                    name=proxy_name,
                    type=proxy_type_field.value,
                    host=proxy_host_field.value.strip(),
                    port=port_val,
                    username=proxy_user_field.value.strip() if proxy_user_field.value else None,
                    password=proxy_pass_field.value if proxy_pass_field.value else None,
                )

            open_tabs = self.parse_open_tabs(open_tabs_field.value or "")
            languages = get_selected_languages()

            self.db.create_profile(
                name=profile_name,
                profile_id=profile_id,
                notes=notes_field.value or "",
                proxy_id=proxy_id,
                tags=tags_field.value or "",
                os=os_dropdown.value,
                user_agent=ua_field.value or "",
                open_tabs=json.dumps(open_tabs, ensure_ascii=False),
                timezone_mode=timezone_mode.value,
                timezone_value=timezone_dropdown.value if timezone_mode.value == "custom" else None,
                geolocation_mode=geolocation_mode.value,
                geolocation_lat=float(geo_lat_field.value) if geolocation_mode.value == "manual" else None,
                geolocation_lon=float(geo_lon_field.value) if geolocation_mode.value == "manual" else None,
                language_mode=language_mode.value,
                languages=json.dumps(languages, ensure_ascii=False) if language_mode.value == "custom" else None,
            )

            dialog.open = False
            self.page.update()
            self.refresh_profiles()

        def on_field_change(e):
            validate_form()
            update_preview()

        name_field.on_change = on_field_change
        os_dropdown.on_change = on_field_change
        open_tabs_field.on_change = on_field_change
        proxy_mode.on_change = lambda e: (update_visibility(), validate_form())
        proxy_type_field.on_change = on_field_change
        proxy_host_field.on_change = on_field_change
        proxy_port_field.on_change = on_field_change
        proxy_user_field.on_change = on_field_change
        proxy_pass_field.on_change = on_field_change
        saved_proxy_display.on_click = open_saved_proxy_picker
        timezone_mode.on_change = lambda e: (update_visibility(), validate_form())
        timezone_dropdown.on_change = on_field_change
        geolocation_mode.on_change = lambda e: (update_visibility(), validate_form())
        geo_lat_field.on_change = on_field_change
        geo_lon_field.on_change = on_field_change
        language_mode.on_change = lambda e: (update_visibility(), validate_form())
        for cb in language_checkboxes:
            cb.on_change = on_field_change

        ua_field.expand = True

        preview_box = ft.Container(
            content=ft.Column(
                [
                    preview_title,
                    ft.Divider(height=1),
                    preview_os,
                    preview_ua,
                    preview_tz,
                    preview_geo,
                    preview_lang,
                ],
                spacing=6,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=10,
            padding=12,
            width=280,
        )

        left_form = ft.Column(
            [
                name_field,
                os_dropdown,
                ft.Row([ua_field, ua_button], spacing=10),
                open_tabs_field,
                open_tabs_error,
                ft.Divider(),
                ft.Text("Проксі", weight=ft.FontWeight.BOLD),
                proxy_mode,
                proxy_type_field,
                proxy_host_field,
                proxy_port_field,
                proxy_user_field,
                proxy_pass_field,
                saved_proxy_display,
                proxy_error,
                ft.Divider(),
                ft.Text("Часовий пояс", weight=ft.FontWeight.BOLD),
                timezone_mode,
                timezone_dropdown,
                ft.Divider(),
                ft.Text("Геолокація", weight=ft.FontWeight.BOLD),
                geolocation_mode,
                geo_lat_field,
                geo_lon_field,
                ft.Divider(),
                ft.Text("Мова", weight=ft.FontWeight.BOLD),
                language_mode,
                languages_container,
                ft.Divider(),
                notes_field,
                tags_field,
            ],
            tight=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        settings_content = ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=left_form, width=360, expand=True),
                    preview_box,
                ],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True,
            ),
            expand=True,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Створити профіль"),
            content=ft.Container(
                content=settings_content,
                width=860,
                height=680,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: self.close_dialog(dialog)),
                create_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        create_button.on_click = create_profile
        update_visibility()
        validate_form()
        update_preview()

        self.open_dialog(dialog)

    def show_edit_profile_dialog(self, profile_id: str):
        """Показує діалог редагування профілю."""
        profile = self.db.get_profile_by_id(profile_id)
        if not profile:
            return

        name_field = ft.TextField(label="Назва профілю", value=profile['name'], autofocus=True)
        os_dropdown = ft.Dropdown(
            label="Operating System",
            options=[
                ft.dropdown.Option("Windows"),
                ft.dropdown.Option("macOS"),
                ft.dropdown.Option("Linux"),
                ft.dropdown.Option("Android"),
                ft.dropdown.Option("iOS"),
            ],
            value=profile.get("os") or "Windows",
        )
        ua_field = ft.TextField(label="User-Agent", value=profile.get("user_agent") or "")
        ua_button = ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Згенерувати User-Agent")

        open_tabs_value = ""
        if profile.get("open_tabs"):
            try:
                open_tabs_value = "\n".join(json.loads(profile.get("open_tabs")))
            except Exception:
                open_tabs_value = ""
        open_tabs_field = ft.TextField(
            label="Стартові вкладки",
            multiline=True,
            min_lines=1,
            max_lines=5,
            value=open_tabs_value,
        )
        open_tabs_error = ft.Text(value="", color=ft.Colors.RED, size=12, visible=False)

        notes_field = ft.TextField(label="Нотатки", value=profile.get('notes', '') or '', multiline=True, max_lines=3)
        tags_field = ft.TextField(label="Теги (через кому)", value=profile.get('tags', '') or '')

        timezone_options = [
            "UTC",
            "Europe/Kyiv",
            "Europe/London",
            "Europe/Warsaw",
            "Europe/Berlin",
            "America/New_York",
            "America/Chicago",
            "America/Los_Angeles",
            "Asia/Tokyo",
            "Asia/Singapore",
            "Asia/Dubai",
            "Australia/Sydney",
        ]

        timezone_mode = ft.RadioGroup(
            value=profile.get("timezone_mode") or "ip",
            content=ft.Column(
                [
                    ft.Radio(value="ip", label="На основі IP"),
                    ft.Radio(value="system", label="Реальний (системний)"),
                    ft.Radio(value="custom", label="Настроюваний (UTC)"),
                ],
                spacing=5,
            ),
        )
        timezone_dropdown = ft.Dropdown(
            label="Часовий пояс",
            options=[ft.dropdown.Option(tz) for tz in timezone_options],
            value=profile.get("timezone_value"),
            visible=(profile.get("timezone_mode") == "custom"),
        )

        geolocation_mode = ft.RadioGroup(
            value=profile.get("geolocation_mode") or "ip",
            content=ft.Column(
                [
                    ft.Radio(value="ip", label="На основі IP"),
                    ft.Radio(value="manual", label="Налаштувати"),
                    ft.Radio(value="block", label="Блокувати"),
                ],
                spacing=5,
            ),
        )
        geo_lat_field = ft.TextField(
            label="Latitude",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(profile.get("geolocation_lat")) if profile.get("geolocation_lat") is not None else "",
            visible=(profile.get("geolocation_mode") == "manual"),
        )
        geo_lon_field = ft.TextField(
            label="Longitude",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(profile.get("geolocation_lon")) if profile.get("geolocation_lon") is not None else "",
            visible=(profile.get("geolocation_mode") == "manual"),
        )

        language_mode = ft.RadioGroup(
            value=profile.get("language_mode") or "ip",
            content=ft.Column(
                [
                    ft.Radio(value="ip", label="На основі IP"),
                    ft.Radio(value="custom", label="Налаштувати"),
                ],
                spacing=5,
            ),
        )
        language_options = [
            "en-US", "uk-UA", "ru-RU", "de-DE", "fr-FR", "es-ES",
            "it-IT", "pl-PL", "tr-TR", "zh-CN", "ja-JP",
        ]

        selected_languages = []
        if profile.get("languages"):
            try:
                selected_languages = json.loads(profile.get("languages"))
            except Exception:
                selected_languages = []

        language_checkboxes = [
            ft.Checkbox(label=lang, value=lang in selected_languages)
            for lang in language_options
        ]
        languages_container = ft.Column(language_checkboxes, visible=(profile.get("language_mode") == "custom"), spacing=5)

        # Проксі
        proxies = self.db.get_all_proxies()
        proxy_mode_value = "saved" if profile.get("proxy_id") else "none"
        proxy_mode = ft.RadioGroup(
            value=proxy_mode_value,
            content=ft.Column(
                [
                    ft.Radio(value="none", label="Без проксі"),
                    ft.Radio(value="manual", label="Ввести проксі"),
                    ft.Radio(value="saved", label="Збережені проксі"),
                ],
                spacing=5,
            ),
        )

        proxy_type_field = ft.Dropdown(
            label="Тип проксі",
            options=[
                ft.dropdown.Option("http", "HTTP"),
                ft.dropdown.Option("https", "HTTPS"),
                ft.dropdown.Option("socks4", "SOCKS4"),
                ft.dropdown.Option("socks5", "SOCKS5"),
            ],
            value="http",
            visible=False,
        )
        proxy_host_field = ft.TextField(
            label="IP адреса або хост",
            hint_text="192.168.1.1 або proxy.example.com",
            visible=False,
        )
        proxy_port_field = ft.TextField(
            label="Порт",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="8080",
            visible=False,
        )
        proxy_user_field = ft.TextField(
            label="Логін (опціонально)",
            visible=False,
        )
        proxy_pass_field = ft.TextField(
            label="Пароль (опціонально)",
            password=True,
            can_reveal_password=True,
            visible=False,
        )

        def format_proxy_label(proxy: Dict) -> str:
            name = proxy.get("name") or ""
            host = proxy.get("host") or ""
            port = proxy.get("port")
            host_port = f"{host}:{port}" if host and port else ""
            if host_port and host_port not in name:
                return f"{name} ({host_port})" if name else host_port
            return name or host_port

        selected_saved_proxy_id = {"value": str(profile.get("proxy_id")) if profile.get("proxy_id") else (str(proxies[0]["id"]) if proxies else None)}
        selected_saved_proxy_label = ""
        if selected_saved_proxy_id["value"]:
            for p in proxies:
                if str(p["id"]) == selected_saved_proxy_id["value"]:
                    selected_saved_proxy_label = format_proxy_label(p)
                    break

        saved_proxy_display = ft.TextField(
            label="Збережені проксі",
            value=selected_saved_proxy_label,
            read_only=True,
            visible=proxy_mode_value == "saved",
        )
        proxy_error = ft.Text(value="", color=ft.Colors.RED, size=12, visible=False)
        proxy_picker_state = {"open": False}

        def open_saved_proxy_picker(e=None):
            if proxy_picker_state["open"]:
                return
            proxy_picker_state["open"] = True
            search_field = ft.TextField(
                label="Пошук",
                hint_text="назва або IP",
                autofocus=True,
            )

            list_view = ft.ListView(expand=True, spacing=0, auto_scroll=False)
            list_container = ft.Container(
                content=list_view,
                expand=True,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                padding=5,
            )

            def proxy_subtitle(proxy: Dict) -> str:
                name = proxy.get("name") or ""
                host = proxy.get("host") or ""
                port = proxy.get("port")
                host_port = f"{host}:{port}" if host and port else ""
                if host_port and host_port not in name:
                    return host_port
                return ""

            def render_list(query: str = ""):
                q = (query or "").strip().lower()
                filtered = []
                for proxy in proxies:
                    name = (proxy.get("name") or "").lower()
                    host = (proxy.get("host") or "").lower()
                    port = str(proxy.get("port") or "")
                    if not q or q in name or q in host or q in port:
                        filtered.append(proxy)

                tiles = []
                for p in filtered:
                    tiles.append(
                        ft.ListTile(
                            leading=ft.Container(
                                content=ft.Text(str(p.get("id", "")), size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6,
                            ),
                            title=ft.Text(format_proxy_label(p)),
                            subtitle=ft.Text(proxy_subtitle(p)) if proxy_subtitle(p) else None,
                            on_click=lambda e, pid=p["id"], label=format_proxy_label(p): select_proxy(pid, label),
                        )
                    )
                    tiles.append(ft.Divider(height=1))

                if tiles:
                    tiles = tiles[:-1]

                list_view.controls = tiles

                if proxy_picker:
                    try:
                        if proxy_picker.page:
                            list_view.update()
                    except RuntimeError:
                        pass

            def select_proxy(proxy_id: int, label: str):
                selected_saved_proxy_id["value"] = str(proxy_id)
                saved_proxy_display.value = label
                if dialog:
                    try:
                        if dialog.page:
                            saved_proxy_display.update()
                    except RuntimeError:
                        pass

                self.close_dialog(proxy_picker)
                proxy_picker_state["open"] = False

            search_field.on_change = lambda e: render_list(search_field.value)

            proxy_picker = ft.AlertDialog(
                modal=True,
                title=ft.Text("Вибір проксі"),
                content=ft.Container(
                    content=ft.Column(
                        [search_field, list_container],
                        spacing=10,
                        expand=True,
                    ),
                    width=450,
                    height=500,
                ),
                actions=[
                    ft.TextButton("Закрити", on_click=lambda e: (self.close_dialog(proxy_picker), proxy_picker_state.__setitem__("open", False))),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            render_list()
            self.open_dialog(proxy_picker)

        save_button = ft.Button("Зберегти")

        def update_visibility(e=None):
            timezone_dropdown.visible = timezone_mode.value == "custom"
            geo_lat_field.visible = geolocation_mode.value == "manual"
            geo_lon_field.visible = geolocation_mode.value == "manual"
            languages_container.visible = language_mode.value == "custom"
            is_manual = proxy_mode.value == "manual"
            is_saved = proxy_mode.value == "saved"

            proxy_type_field.visible = is_manual
            proxy_host_field.visible = is_manual
            proxy_port_field.visible = is_manual
            proxy_user_field.visible = is_manual
            proxy_pass_field.visible = is_manual

            saved_proxy_display.visible = is_saved
            proxy_error.visible = False
            if dialog:
                try:
                    if dialog.page:
                        dialog.content.update()
                except RuntimeError:
                    pass

        def get_selected_languages() -> List[str]:
            return [cb.label for cb in language_checkboxes if cb.value]

        def validate_form() -> bool:
            is_valid = True

            invalid_urls = self.validate_open_tabs(open_tabs_field.value or "")
            if invalid_urls:
                open_tabs_error.value = "Некоректні URL: " + ", ".join(invalid_urls)
                open_tabs_error.visible = True
                is_valid = False
            else:
                open_tabs_error.visible = False

            if timezone_mode.value == "custom" and not timezone_dropdown.value:
                timezone_dropdown.error_text = "Оберіть часовий пояс"
                is_valid = False
            else:
                timezone_dropdown.error_text = None

            if geolocation_mode.value == "manual":
                try:
                    lat = float(geo_lat_field.value) if geo_lat_field.value else None
                    lon = float(geo_lon_field.value) if geo_lon_field.value else None
                    if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        geo_lat_field.error_text = "Введіть коректну широту (-90..90)"
                        geo_lon_field.error_text = "Введіть коректну довготу (-180..180)"
                        is_valid = False
                    else:
                        geo_lat_field.error_text = None
                        geo_lon_field.error_text = None
                except ValueError:
                    geo_lat_field.error_text = "Введіть число"
                    geo_lon_field.error_text = "Введіть число"
                    is_valid = False
            else:
                geo_lat_field.error_text = None
                geo_lon_field.error_text = None

            if language_mode.value == "custom" and not get_selected_languages():
                is_valid = False

            # Проксі
            if proxy_mode.value == "manual":
                proxy_host_field.error_text = None
                proxy_port_field.error_text = None
                if not proxy_host_field.value or not proxy_host_field.value.strip():
                    proxy_host_field.error_text = "Введіть IP або хост"
                    is_valid = False
                if not proxy_port_field.value or not proxy_port_field.value.strip():
                    proxy_port_field.error_text = "Введіть порт"
                    is_valid = False
                else:
                    try:
                        port_val = int(proxy_port_field.value)
                        if port_val < 1 or port_val > 65535:
                            proxy_port_field.error_text = "Порт має бути від 1 до 65535"
                            is_valid = False
                    except ValueError:
                        proxy_port_field.error_text = "Введіть правильний порт (число)"
                        is_valid = False
            elif proxy_mode.value == "saved":
                if not selected_saved_proxy_id["value"]:
                    proxy_error.value = "Оберіть збережений проксі"
                    proxy_error.visible = True
                    is_valid = False

            save_button.disabled = not is_valid
            if dialog:
                try:
                    if dialog.page:
                        dialog.content.update()
                except RuntimeError:
                    pass
            return is_valid

        def on_generate_ua(e):
            ua_field.value = self.generate_user_agent_for_os(os_dropdown.value)
            ua_field.update()

        ua_button.on_click = on_generate_ua

        def update_profile(e):
            if not validate_form():
                return

            proxy_id = None
            if proxy_mode.value == "saved" and selected_saved_proxy_id["value"]:
                proxy_id = int(selected_saved_proxy_id["value"])
            elif proxy_mode.value == "manual":
                port_val = int(proxy_port_field.value)
                proxy_name = f"Proxy {proxy_host_field.value.strip()}:{port_val}"
                proxy_id = self.db.create_proxy(
                    name=proxy_name,
                    type=proxy_type_field.value,
                    host=proxy_host_field.value.strip(),
                    port=port_val,
                    username=proxy_user_field.value.strip() if proxy_user_field.value else None,
                    password=proxy_pass_field.value if proxy_pass_field.value else None,
                )

            open_tabs = self.parse_open_tabs(open_tabs_field.value or "")
            languages = get_selected_languages()

            self.db.update_profile(
                profile_id=profile_id,
                name=name_field.value.strip() or profile["name"],
                notes=notes_field.value or "",
                proxy_id=proxy_id,
                tags=tags_field.value or "",
                os=os_dropdown.value,
                user_agent=ua_field.value or "",
                open_tabs=json.dumps(open_tabs, ensure_ascii=False),
                timezone_mode=timezone_mode.value,
                timezone_value=timezone_dropdown.value if timezone_mode.value == "custom" else None,
                geolocation_mode=geolocation_mode.value,
                geolocation_lat=float(geo_lat_field.value) if geolocation_mode.value == "manual" else None,
                geolocation_lon=float(geo_lon_field.value) if geolocation_mode.value == "manual" else None,
                language_mode=language_mode.value,
                languages=json.dumps(languages, ensure_ascii=False) if language_mode.value == "custom" else None,
            )

            dialog.open = False
            self.page.update()
            self.refresh_profiles()

        def on_field_change(e):
            validate_form()
            update_preview()

        name_field.on_change = on_field_change
        os_dropdown.on_change = on_field_change
        open_tabs_field.on_change = on_field_change
        proxy_mode.on_change = lambda e: (update_visibility(), validate_form())
        proxy_type_field.on_change = on_field_change
        proxy_host_field.on_change = on_field_change
        proxy_port_field.on_change = on_field_change
        proxy_user_field.on_change = on_field_change
        proxy_pass_field.on_change = on_field_change
        saved_proxy_display.on_click = open_saved_proxy_picker
        timezone_mode.on_change = lambda e: (update_visibility(), validate_form())
        timezone_dropdown.on_change = on_field_change
        geolocation_mode.on_change = lambda e: (update_visibility(), validate_form())
        geo_lat_field.on_change = on_field_change
        geo_lon_field.on_change = on_field_change
        language_mode.on_change = lambda e: (update_visibility(), validate_form())
        for cb in language_checkboxes:
            cb.on_change = on_field_change

        ua_field.expand = True

        preview_box = ft.Container(
            content=ft.Column(
                [
                    preview_title,
                    ft.Divider(height=1),
                    preview_os,
                    preview_ua,
                    preview_tz,
                    preview_geo,
                    preview_lang,
                ],
                spacing=6,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=10,
            padding=12,
            width=280,
        )

        left_form = ft.Column(
            [
                name_field,
                os_dropdown,
                ft.Row([ua_field, ua_button], spacing=10),
                open_tabs_field,
                open_tabs_error,
                ft.Divider(),
                ft.Text("Проксі", weight=ft.FontWeight.BOLD),
                proxy_mode,
                proxy_type_field,
                proxy_host_field,
                proxy_port_field,
                proxy_user_field,
                proxy_pass_field,
                saved_proxy_display,
                proxy_error,
                ft.Divider(),
                ft.Text("Часовий пояс", weight=ft.FontWeight.BOLD),
                timezone_mode,
                timezone_dropdown,
                ft.Divider(),
                ft.Text("Геолокація", weight=ft.FontWeight.BOLD),
                geolocation_mode,
                geo_lat_field,
                geo_lon_field,
                ft.Divider(),
                ft.Text("Мова", weight=ft.FontWeight.BOLD),
                language_mode,
                languages_container,
                ft.Divider(),
                notes_field,
                tags_field,
            ],
            tight=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        settings_content = ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=left_form, width=360, expand=True),
                    preview_box,
                ],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True,
            ),
            expand=True,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редагувати профіль"),
            content=ft.Container(
                content=settings_content,
                width=860,
                height=680,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: self.close_dialog(dialog)),
                save_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        save_button.on_click = update_profile
        update_visibility()
        validate_form()
        update_preview()

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
                    
                    profile_settings = {}
                    if profile:
                        profile_settings = self.build_profile_launch_settings(profile)

                    context = self.browser_manager.launch_profile(
                        profile_id,
                        proxy_data,
                        headless=False,
                        profile_settings=profile_settings
                    )

                    # Відкриваємо стартові вкладки
                    if profile and profile.get("open_tabs"):
                        try:
                            tabs = json.loads(profile.get("open_tabs"))
                        except Exception:
                            tabs = []

                        if tabs:
                            try:
                                pages = context.pages
                                if pages:
                                    pages[0].goto(tabs[0])
                                    for url in tabs[1:]:
                                        context.new_page().goto(url)
                                else:
                                    for url in tabs:
                                        context.new_page().goto(url)
                            except Exception as ex:
                                print(f"Помилка відкриття вкладок: {ex}")
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

                # Перевіряємо через ipify з таймаутом 15 секунд
                response = session.get(
                    'https://api.ipify.org?format=json',
                    proxies=proxies_dict,
                    timeout=15,
                    allow_redirects=True
                )

                if response.status_code == 200:
                    self.proxy_statuses[proxy_id] = {'status': 'working'}
                else:
                    self.proxy_statuses[proxy_id] = {
                        'status': 'failed',
                        'error': f"HTTP {response.status_code}"
                    }
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

