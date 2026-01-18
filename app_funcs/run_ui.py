def run_ui(self, func):
    """Безпечно виконує синхронну UI-дію через run_task."""
    async def _run():
        func()

    self.page.run_task(_run)
