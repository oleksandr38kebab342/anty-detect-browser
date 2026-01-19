import json
import asyncio


def toggle_profile(self, e):
    """Запускає або зупиняє профіль."""
    # Отримуємо profile_id з data атрибута кнопки
    profile_id = e.control.data if hasattr(e.control, 'data') else None

    if not profile_id:
        return

    is_running = self.browser_manager.is_profile_running(profile_id)

    if is_running:
        async def stop():
            await self.browser_manager.stop_profile(profile_id)
            self.refresh_profiles()

        self.page.run_task(stop)
    else:
        async def launch():
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

                context = await self.browser_manager.launch_profile(
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
                                page = pages[0]
                            else:
                                page = await context.new_page()

                            await page.goto(tabs[0])
                            try:
                                await page.evaluate(
                                    """() => { window.moveTo(0,0); window.resizeTo(screen.availWidth, screen.availHeight); }"""
                                )
                            except Exception:
                                pass

                            for url in tabs[1:]:
                                await page.evaluate("url => window.open(url, '_blank')", url)
                        except Exception as ex:
                            print(f"Помилка відкриття вкладок: {ex}")
                else:
                    pages = context.pages
                    if pages:
                        try:
                            await pages[0].evaluate(
                                """() => { window.moveTo(0,0); window.resizeTo(screen.availWidth, screen.availHeight); }"""
                            )
                        except Exception:
                            pass
                # Оновлюємо інтерфейс після успішного запуску
                await asyncio.sleep(0.5)
                self.refresh_profiles()
            except Exception as ex:
                print(f"Помилка запуску профілю {profile_id}: {ex}")
                # Показуємо повідомлення про помилку
                self.show_error_dialog(f"Помилка запуску профілю: {ex}")

        self.page.run_task(launch)
        # Оновлюємо одразу для показу статусу "запускається"
        self.refresh_profiles()
