import flet as ft


def open_dialog(self, dialog: ft.AlertDialog):
    """Відкриває діалог, сумісно з різними версіями Flet."""
    if dialog not in self.page.overlay:
        self.page.overlay.append(dialog)
    dialog.open = True
    self.page.update()
