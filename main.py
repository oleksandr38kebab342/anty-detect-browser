"""
Головний файл додатка - Flet UI для керування браузерними профілями.
"""
import flet as ft
import threading
from typing import Optional
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
                ft.ElevatedButton(
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
                    border=ft.border.all(1, ft.Colors.OUTLINE),
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
                ft.ElevatedButton(
                    "Додати проксі",
                    icon=ft.Icons.ADD_LINK,
                    on_click=self.show_create_proxy_dialog,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.proxies_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Назва")),
                ft.DataColumn(ft.Text("Тип")),
                ft.DataColumn(ft.Text("Адреса")),
                ft.DataColumn(ft.Text("Порт")),
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
                    border=ft.border.all(1, ft.Colors.OUTLINE),
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
                        ft.DataCell(ft.Text(proxy['name'])),
                        ft.DataCell(ft.Text(proxy['type'].upper())),
                        ft.DataCell(ft.Text(proxy['host'])),
                        ft.DataCell(ft.Text(str(proxy['port']))),
                        ft.DataCell(actions),
                    ]
                )
            )

        self.proxies_table.rows = rows
        if hasattr(self, 'proxies_table'):
            self.proxies_table.update()

    def refresh_current_view(self):
        """Оновлює поточний вид."""
        if self.current_page == "profiles":
            self.refresh_profiles()
        elif self.current_page == "proxies":
            self.refresh_proxies()

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
                ft.TextButton("Скасувати", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.TextButton("Створити", on_click=create_profile),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

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
                ft.TextButton("Скасувати", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.TextButton("Зберегти", on_click=update_profile),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_create_proxy_dialog(self, e):
        """Показує діалог створення проксі."""
        name_field = ft.TextField(label="Назва проксі", autofocus=True)
        type_field = ft.Dropdown(
            label="Тип",
            options=[
                ft.dropdown.Option("http"),
                ft.dropdown.Option("https"),
                ft.dropdown.Option("socks5"),
            ],
            value="http",
        )
        host_field = ft.TextField(label="IP адреса")
        port_field = ft.TextField(label="Порт", keyboard_type=ft.KeyboardType.NUMBER)
        username_field = ft.TextField(label="Логін (опціонально)")
        password_field = ft.TextField(label="Пароль (опціонально)", password=True)

        def create_proxy(e):
            if not name_field.value or not host_field.value or not port_field.value:
                return

            try:
                port = int(port_field.value)
            except ValueError:
                port_field.error_text = "Введіть правильний порт"
                dialog.update()
                return

            self.db.create_proxy(
                name=name_field.value,
                type=type_field.value,
                host=host_field.value,
                port=port,
                username=username_field.value or None,
                password=password_field.value or None,
            )

            dialog.open = False
            self.page.update()
            self.refresh_proxies()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Додати проксі"),
            content=ft.Container(
                content=ft.Column(
                    [name_field, type_field, host_field, port_field, username_field, password_field],
                    tight=True,
                    width=400,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=400,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.TextButton("Додати", on_click=create_proxy),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_edit_proxy_dialog(self, proxy_id: int):
        """Показує діалог редагування проксі."""
        proxy = self.db.get_proxy_by_id(proxy_id)
        if not proxy:
            return

        name_field = ft.TextField(label="Назва проксі", value=proxy['name'], autofocus=True)
        type_field = ft.Dropdown(
            label="Тип",
            options=[
                ft.dropdown.Option("http"),
                ft.dropdown.Option("https"),
                ft.dropdown.Option("socks5"),
            ],
            value=proxy['type'],
        )
        host_field = ft.TextField(label="IP адреса", value=proxy['host'])
        port_field = ft.TextField(label="Порт", value=str(proxy['port']), keyboard_type=ft.KeyboardType.NUMBER)
        username_field = ft.TextField(label="Логін (опціонально)", value=proxy.get('username') or '')
        password_field = ft.TextField(label="Пароль (опціонально)", value=proxy.get('password') or '', password=True)

        def update_proxy(e):
            if not name_field.value or not host_field.value or not port_field.value:
                return

            try:
                port = int(port_field.value)
            except ValueError:
                port_field.error_text = "Введіть правильний порт"
                dialog.update()
                return

            self.db.update_proxy(
                proxy_id=proxy_id,
                name=name_field.value,
                type=type_field.value,
                host=host_field.value,
                port=port,
                username=username_field.value or None,
                password=password_field.value or None,
            )

            dialog.open = False
            self.page.update()
            self.refresh_proxies()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редагувати проксі"),
            content=ft.Container(
                content=ft.Column(
                    [name_field, type_field, host_field, port_field, username_field, password_field],
                    tight=True,
                    width=400,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=400,
            ),
            actions=[
                ft.TextButton("Скасувати", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.TextButton("Зберегти", on_click=update_proxy),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

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
                    self.page.run_task(self.refresh_profiles)
                except Exception as ex:
                    print(f"Помилка запуску профілю {profile_id}: {ex}")
                    # Показуємо повідомлення про помилку
                    self.page.run_task(
                        lambda: self.show_error_dialog(f"Помилка запуску профілю: {ex}")
                    )

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
                ft.TextButton("Скасувати", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.TextButton("Видалити", on_click=confirm_delete, color=ft.Colors.RED),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

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
                ft.TextButton("Скасувати", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
                ft.TextButton("Видалити", on_click=confirm_delete, color=ft.Colors.RED),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_error_dialog(self, message: str):
        """Показує діалог з помилкою."""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Помилка"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: setattr(dialog, 'open', False) or self.page.update()),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


def main(page: ft.Page):
    app = AntyDetectBrowser(page)
    
    # Оновлюємо статуси профілів періодично
    def update_statuses():
        import time
        while True:
            time.sleep(2)
            try:
                if page.window_alive:
                    page.run_task(app.refresh_profiles)
            except:
                break

    status_thread = threading.Thread(target=update_statuses, daemon=True)
    status_thread.start()


if __name__ == "__main__":
    ft.app(target=main)

