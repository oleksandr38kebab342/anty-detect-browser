import flet as ft


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
    if self.proxies_table and self.proxies_table.page:
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
            if header_checkbox.page:
                header_checkbox.update()
            self._updating_select_all = False
