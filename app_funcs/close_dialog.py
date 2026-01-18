import flet as ft


def close_dialog(self, dialog: ft.AlertDialog):
    """Закриває діалог."""
    dialog.open = False
    self.page.update()
