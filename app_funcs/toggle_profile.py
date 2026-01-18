import json
import threading


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

                profile_settings = {}
                if profile:
                    profile_settings = self.build_profile_launch_settings(profile)

                context = self.browser_manager.launch_profile(
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
                                pages[0].goto(tabs[0])
                                for url in tabs[1:]:
                                    context.new_page().goto(url)
                            else:
                                for url in tabs:
                                    context.new_page().goto(url)
                        except Exception as ex:
                            print(f"Помилка відкриття вкладок: {ex}")
                # Оновлюємо інтерфейс після успішного запуску
                import time
                time.sleep(0.5)
                self.run_ui(self.refresh_profiles)
            except Exception as ex:
                print(f"Помилка запуску профілю {profile_id}: {ex}")
                # Показуємо повідомлення про помилку
                self.run_ui(lambda: self.show_error_dialog(f"Помилка запуску профілю: {ex}"))

        thread = threading.Thread(target=launch, daemon=True)
        thread.start()
        # Оновлюємо одразу для показу статусу "запускається"
        self.refresh_profiles()
