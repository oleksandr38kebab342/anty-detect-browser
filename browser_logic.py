"""
Модуль для роботи з Playwright та керування браузерними профілями.
"""
import uuid
import threading
import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright, BrowserContext, Playwright
from pathlib import Path


class BrowserManager:
    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self.running_browsers: Dict[str, BrowserContext] = {}
        self.playwright: Optional[Playwright] = None
        self._lock = threading.Lock()
        self._playwright_lock = asyncio.Lock()

    async def _get_playwright(self):
        """Отримує або створює екземпляр Playwright."""
        async with self._playwright_lock:
            if self.playwright is None:
                try:
                    print("Ініціалізація Playwright...")
                    self.playwright = await async_playwright().start()
                    print("Playwright ініціалізовано успішно")
                except Exception as e:
                    print(f"Критична помилка ініціалізації Playwright: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            return self.playwright

    def generate_profile_id(self) -> str:
        """Генерує унікальний ID для профілю."""
        return str(uuid.uuid4())

    def get_profile_path(self, profile_id: str) -> Path:
        """Отримує шлях до папки профілю."""
        return self.profiles_dir / profile_id

    def get_tabs_file_path(self, profile_id: str) -> Path:
        """Отримує шлях до файлу з збереженими вкладками."""
        return self.get_profile_path(profile_id) / "saved_tabs.json"

    async def save_open_tabs(self, profile_id: str) -> None:
        """Зберігає поточні відкриті вкладки профілю."""
        if profile_id not in self.running_browsers:
            return
            
        try:
            context = self.running_browsers[profile_id]
            pages = context.pages
            tabs_data = []
            
            for page in pages:
                try:
                    url = page.url
                    title = await page.title()
                    # Пропускаємо службові сторінки Chrome
                    if not url.startswith(('chrome://', 'chrome-extension://', 'about:')):
                        tabs_data.append({
                            'url': url,
                            'title': title
                        })
                except Exception:
                    continue
            
            if tabs_data:
                tabs_file = self.get_tabs_file_path(profile_id)
                tabs_file.parent.mkdir(exist_ok=True)
                
                import json
                with open(tabs_file, 'w', encoding='utf-8') as f:
                    json.dump(tabs_data, f, ensure_ascii=False, indent=2)
                    
                print(f"Збережено {len(tabs_data)} вкладок для профілю {profile_id}")
            
        except Exception as e:
            print(f"Помилка збереження вкладок для профілю {profile_id}: {e}")

    def load_saved_tabs(self, profile_id: str) -> list:
        """Завантажує збережені вкладки профілю."""
        tabs_file = self.get_tabs_file_path(profile_id)
        
        if not tabs_file.exists():
            return []
            
        try:
            import json
            with open(tabs_file, 'r', encoding='utf-8') as f:
                tabs_data = json.load(f)
                return [tab['url'] for tab in tabs_data if 'url' in tab]
        except Exception as e:
            print(f"Помилка завантаження збережених вкладок для профілю {profile_id}: {e}")
            return []

    def create_profile_folder(self, profile_id: str) -> Path:
        """Створює папку для профілю."""
        profile_path = self.get_profile_path(profile_id)
        profile_path.mkdir(exist_ok=True)
        return profile_path

    def get_proxy_config(self, proxy_data: Optional[Dict]) -> Optional[Dict]:
        """Формує конфігурацію проксі для Playwright."""
        if not proxy_data:
            return None

        proxy_config = {
            "server": f"{proxy_data['type']}://{proxy_data['host']}:{proxy_data['port']}"
        }

        if proxy_data.get('username') and proxy_data.get('password'):
            proxy_config["username"] = proxy_data['username']
            proxy_config["password"] = proxy_data['password']

        return proxy_config

    async def launch_profile(self, profile_id: str, proxy_data: Optional[Dict] = None,
                      headless: bool = False, profile_settings: Optional[Dict] = None) -> BrowserContext:
        """
        Запускає браузер для профілю.
        
        Args:
            profile_id: ID профілю
            proxy_data: Дані проксі (якщо є)
            headless: Запуск у headless режимі
        
        Returns:
            BrowserContext об'єкт
        """
        print(f"Спроба запуску профілю {profile_id}")
        with self._lock:
            if profile_id in self.running_browsers:
                print(f"Профіль {profile_id} вже запущений")
                return self.running_browsers[profile_id]

            profile_path = self.create_profile_folder(profile_id)
            print(f"Шлях до профілю: {profile_path}")
            
            try:
                print("Початок ініціалізації Playwright...")
                playwright = await self._get_playwright()
                print("Playwright отримано успішно")
            except Exception as e:
                print(f"Помилка отримання Playwright: {e}")
                import traceback
                traceback.print_exc()
                raise

            proxy_config = self.get_proxy_config(proxy_data)
            if proxy_config:
                print(f"Використання проксі: {proxy_config}")
            
            profile_settings = profile_settings or {}

            user_agent = profile_settings.get("user_agent")
            locale = profile_settings.get("locale")
            timezone_id = profile_settings.get("timezone_id")
            geolocation = profile_settings.get("geolocation")
            permissions = profile_settings.get("permissions")
            extra_http_headers = profile_settings.get("extra_http_headers")

            context_options = {
                "no_viewport": True,
            }
            if user_agent:
                context_options["user_agent"] = user_agent
            if locale:
                context_options["locale"] = locale
            if timezone_id:
                context_options["timezone_id"] = timezone_id
            if geolocation:
                context_options["geolocation"] = geolocation
            if permissions is not None:
                context_options["permissions"] = permissions
            if extra_http_headers:
                context_options["extra_http_headers"] = extra_http_headers

            # Спробуємо спочатку з Chrome, якщо не вийде - використаємо Chromium
            launch_options = {
                "headless": headless,
            }

            # Додаємо аргументи для анти-детекту
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage", 
                "--no-sandbox",
                "--start-maximized",
                "--force-device-scale-factor=1",
                "--enable-features=VaapiVideoDecoder",
                "--disable-features=VizDisplayCompositor",
                # Аргументи для кращого збереження сесії
                "--enable-local-storage",
                "--enable-session-storage", 
                "--enable-offline-web-application-cache",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                # Увімкнути автоматичне відновлення вкладок
                "--restore-last-session",
                # Покращити збереження стану
                "--enable-session-service",
                "--disable-background-mode",
            ]

            try:
                # Спробуємо запустити з Chrome
                print(f"Налаштування запуску:")
                print(f"  Профіль: {profile_path}")
                print(f"  Проксі: {proxy_config}")
                print(f"  Headless: {headless}")
                print(f"  Аргументи: {browser_args}")
                print(f"  Контекст: {context_options}")
                
                try:
                    print("Спроба запуску з Chrome...")
                    # Додаємо таймаут для запуску
                    context = await asyncio.wait_for(
                        playwright.chromium.launch_persistent_context(
                            user_data_dir=str(profile_path),
                            channel="chrome",
                            **launch_options,
                            proxy=proxy_config if proxy_config else None,
                            args=browser_args,
                            **context_options
                        ),
                        timeout=60.0  # 60 секунд таймаут
                    )
                    print("Chrome успішно запущено")
                except Exception as chrome_error:
                    print(f"Помилка запуску Chrome: {chrome_error}")
                    import traceback
                    traceback.print_exc()
                    # Якщо Chrome недоступний, використовуємо Chromium
                    print("Спроба запуску з Chromium...")
                    try:
                        context = await asyncio.wait_for(
                            playwright.chromium.launch_persistent_context(
                                user_data_dir=str(profile_path),
                                **launch_options,
                                proxy=proxy_config if proxy_config else None,
                                args=browser_args,
                                **context_options
                            ),
                            timeout=60.0  # 60 секунд таймаут
                        )
                        print("Chromium успішно запущено")
                    except Exception as chromium_error:
                        print(f"Помилка запуску Chromium: {chromium_error}")
                        import traceback
                        traceback.print_exc()
                        raise

                self.running_browsers[profile_id] = context
                print(f"Профіль {profile_id} додано до running_browsers")
                return context
            except Exception as e:
                print(f"Помилка запуску браузера для профілю {profile_id}: {e}")
                import traceback
                traceback.print_exc()
                raise

    async def stop_profile(self, profile_id: str):
        """Зупиняє браузер профілю."""
        print(f"Спроба зупинки профілю {profile_id}")
        with self._lock:
            if profile_id in self.running_browsers:
                try:
                    context = self.running_browsers[profile_id]
                    
                    # Дочекаємося збереження стану сторінок перед закриттям
                    try:
                        print(f"Підготовка до закриття профілю {profile_id}")
                        pages = context.pages
                        
                        # Chrome автоматично збереже сесію (вкладки, куки, кеш)
                        # при використанні persistent context
                        
                        # Дочекаємося завантаження всіх сторінок перед закриттям
                        for page in pages:
                            try:
                                await page.wait_for_load_state('networkidle', timeout=5000)
                            except Exception:
                                pass
                        
                        # Невеликий таймаут для збереження стану
                        await asyncio.sleep(1)
                        print(f"Стан сторінок збережено для профілю {profile_id}")
                    except Exception as e:
                        print(f"Попередження: не вдалося зберегти стан сторінок для {profile_id}: {e}")
                    
                    print(f"Закриття браузера для профілю {profile_id}")
                    await context.close()
                    print(f"Браузер закрито для профілю {profile_id}")
                except Exception as e:
                    print(f"Помилка закриття браузера для профілю {profile_id}: {e}")
                finally:
                    if profile_id in self.running_browsers:
                        del self.running_browsers[profile_id]
                    print(f"Профіль {profile_id} видалено з running_browsers")

    def is_profile_running(self, profile_id: str) -> bool:
        """Перевіряє, чи запущений профіль."""
        with self._lock:
            if profile_id not in self.running_browsers:
                return False
            
            context = self.running_browsers[profile_id]
            # Перевіряємо, чи контекст ще активний
            try:
                # Спробуємо отримати список сторінок
                pages = context.pages
                return True
            except:
                # Якщо контекст закритий, видаляємо його
                del self.running_browsers[profile_id]
                return False

    async def stop_all_profiles(self):
        """Зупиняє всі запущені профілі."""
        with self._lock:
            profile_ids = list(self.running_browsers.keys())
        for profile_id in profile_ids:
            await self.stop_profile(profile_id)

    async def cleanup(self):
        """Очищає ресурси (закриває Playwright)."""
        await self.stop_all_profiles()
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def cleanup_sync(self):
        """Спроба синхронно закрити Playwright при завершенні застосунку."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(self.cleanup())
            except Exception:
                pass
            return

        try:
            task = loop.create_task(self.cleanup())
            if not loop.is_running():
                loop.run_until_complete(task)
        except Exception:
            pass

