import json
import asyncio
import os


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
                print(f"Спроба запуску профілю {profile_id}")
                profile = self.db.get_profile_by_id(profile_id)
                proxy_data = None
                if profile and profile.get('proxy_id'):
                    proxy = self.db.get_proxy_by_id(profile['proxy_id'])
                    if proxy:
                        proxy_data = dict(proxy)

                profile_settings = {}
                if profile:
                    profile_settings = self.build_profile_launch_settings(profile)

                print(f"Запуск браузера для профілю {profile_id}")
                
                # Додаємо timeout для launch_profile
                try:
                    context = await asyncio.wait_for(
                        self.browser_manager.launch_profile(
                            profile_id,
                            proxy_data,
                            headless=False,
                            profile_settings=profile_settings
                        ),
                        timeout=120.0  # 2 хвилини таймаут
                    )
                except asyncio.TimeoutError:
                    print(f"Таймаут запуску профілю {profile_id}")
                    self.show_error_dialog(f"Таймаут запуску профілю. Спробуйте ще раз.")
                    return
                    
                print(f"Браузер запущено для профілю {profile_id}")

                # Перевіряємо, чи це перший запуск профілю
                profile_path = self.browser_manager.get_profile_path(profile_id)
                session_marker = profile_path / ".session_started"
                
                # Це перший запуск, якщо немає маркера сесії
                is_first_launch = not session_marker.exists()
                
                print(f"Перший запуск: {is_first_launch}")
                
                # Відкриваємо стартові вкладки тільки при першому запуску
                if is_first_launch and profile and profile.get("open_tabs"):
                    # Перший запуск - відкриваємо стартові вкладки
                    try:
                        tabs = json.loads(profile.get("open_tabs"))
                    except Exception:
                        tabs = []

                    if tabs:
                        try:
                            print(f"Перший запуск профілю, відкриваємо стартові вкладки: {tabs}")
                            pages = context.pages
                            
                            # Якщо є існуюча сторінка, використовуємо її для першої вкладки
                            if pages:
                                page = pages[0]
                                await page.goto(tabs[0])
                            else:
                                # Створюємо нову сторінку для першої стартової вкладки
                                page = await context.new_page()
                                await page.goto(tabs[0])
                            
                            try:
                                await page.evaluate(
                                    """() => { window.moveTo(0,0); window.resizeTo(screen.availWidth, screen.availHeight); }"""
                                )
                            except Exception:
                                pass

                            # Відкриваємо решту стартових вкладок
                            for url in tabs[1:]:
                                new_page = await context.new_page()
                                await new_page.goto(url)
                                
                        except Exception as ex:
                            print(f"Помилка відкриття стартових вкладок: {ex}")
                    else:
                        print("Перший запуск профілю, стартові вкладки не налаштовані")
                else:
                    print("Повторний запуск - Chrome автоматично відновить сесію (вкладки, куки, кеш)")

                # Максимізуємо вікно
                pages = context.pages
                if pages:
                    try:
                        await pages[0].evaluate(
                            """() => { window.moveTo(0,0); window.resizeTo(screen.availWidth, screen.availHeight); }"""
                        )
                    except Exception:
                        pass
                
                # Позначаємо, що профіль вже запускався
                try:
                    session_marker.touch()
                except Exception:
                    pass
                # Оновлюємо інтерфейс після успішного запуску
                await asyncio.sleep(0.5)
                self.refresh_profiles()
                print(f"Профіль {profile_id} успішно запущено")
            except Exception as ex:
                print(f"Помилка запуску профілю {profile_id}: {ex}")
                import traceback
                traceback.print_exc()
                # Показуємо повідомлення про помилку
                self.show_error_dialog(f"Помилка запуску профілю: {ex}")

        self.page.run_task(launch)
        # Оновлюємо одразу для показу статусу "запускається"
        self.refresh_profiles()
