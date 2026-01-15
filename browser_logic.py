"""
Модуль для роботи з Playwright та керування браузерними профілями.
"""
import os
import uuid
import threading
from typing import Optional, Dict
from playwright.sync_api import sync_playwright, BrowserContext, Playwright
from pathlib import Path


class BrowserManager:
    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self.running_browsers: Dict[str, BrowserContext] = {}
        self.playwright: Optional[Playwright] = None
        self._lock = threading.Lock()

    def _get_playwright(self):
        """Отримує або створює екземпляр Playwright."""
        if self.playwright is None:
            self.playwright = sync_playwright().start()
        return self.playwright

    def generate_profile_id(self) -> str:
        """Генерує унікальний ID для профілю."""
        return str(uuid.uuid4())

    def get_profile_path(self, profile_id: str) -> Path:
        """Отримує шлях до папки профілю."""
        return self.profiles_dir / profile_id

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

    def launch_profile(self, profile_id: str, proxy_data: Optional[Dict] = None,
                      headless: bool = False) -> BrowserContext:
        """
        Запускає браузер для профілю.
        
        Args:
            profile_id: ID профілю
            proxy_data: Дані проксі (якщо є)
            headless: Запуск у headless режимі
        
        Returns:
            BrowserContext об'єкт
        """
        with self._lock:
            if profile_id in self.running_browsers:
                return self.running_browsers[profile_id]

            profile_path = self.create_profile_folder(profile_id)
            playwright = self._get_playwright()

            proxy_config = self.get_proxy_config(proxy_data)

            # Спробуємо спочатку з Chrome, якщо не вийде - використаємо Chromium
            launch_options = {
                "headless": headless,
            }

            # Додаємо аргументи для анти-детекту
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]

            try:
                # Спробуємо запустити з Chrome
                try:
                    context = playwright.chromium.launch_persistent_context(
                        user_data_dir=str(profile_path),
                        channel="chrome",
                        **launch_options,
                        proxy=proxy_config if proxy_config else None,
                        viewport={"width": 1920, "height": 1080},
                        args=browser_args
                    )
                except Exception:
                    # Якщо Chrome недоступний, використовуємо Chromium
                    context = playwright.chromium.launch_persistent_context(
                        user_data_dir=str(profile_path),
                        **launch_options,
                        proxy=proxy_config if proxy_config else None,
                        viewport={"width": 1920, "height": 1080},
                        args=browser_args
                    )

                self.running_browsers[profile_id] = context
                return context
            except Exception as e:
                print(f"Помилка запуску браузера для профілю {profile_id}: {e}")
                raise

    def stop_profile(self, profile_id: str):
        """Зупиняє браузер профілю."""
        with self._lock:
            if profile_id in self.running_browsers:
                try:
                    context = self.running_browsers[profile_id]
                    context.close()
                except Exception as e:
                    print(f"Помилка закриття браузера для профілю {profile_id}: {e}")
                finally:
                    del self.running_browsers[profile_id]

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

    def stop_all_profiles(self):
        """Зупиняє всі запущені профілі."""
        with self._lock:
            profile_ids = list(self.running_browsers.keys())
            for profile_id in profile_ids:
                self.stop_profile(profile_id)

    def cleanup(self):
        """Очищає ресурси (закриває Playwright)."""
        self.stop_all_profiles()
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

