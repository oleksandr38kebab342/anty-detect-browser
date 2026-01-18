import json
from typing import List, Dict
import flet as ft
from database.db_handler import save_profile
from modules.fingerprint import generate_user_agent


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

    def on_generate_ua(e):
        ua_field.value = generate_user_agent(os_dropdown.value)
        ua_field.update()
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

        save_profile(
            self.db,
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
