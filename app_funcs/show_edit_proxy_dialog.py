import flet as ft


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
