"""Функція для ручного збереження поточних вкладок профілю."""


def save_profile_tabs_manually(self, profile_id: str):
    """Зберігає поточні вкладки профілю вручну."""
    async def _save_tabs():
        try:
            if not self.browser_manager.is_profile_running(profile_id):
                self.show_error_dialog("Профіль не запущений. Спочатку запустіть профіль.")
                return
                
            await self.browser_manager.save_open_tabs(profile_id)
            self.show_success_dialog("Вкладки профілю успішно збережені!")
            
        except Exception as ex:
            print(f"Помилка збереження вкладок: {ex}")
            self.show_error_dialog(f"Помилка збереження вкладок: {ex}")
    
    self.page.run_task(_save_tabs)