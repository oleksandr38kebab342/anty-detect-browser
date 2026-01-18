from typing import Dict


def check_proxy_with_playwright(self, proxy: Dict, proxy_id: int):
    """Перевіряє проксі через Playwright (для SOCKS та складних випадків)."""
    try:
        from playwright.sync_api import sync_playwright

        proxy_config = self.browser_manager.get_proxy_config(proxy)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(proxy=proxy_config)
            page = context.new_page()

            # Встановлюємо таймаут на 15 секунд
            page.set_default_timeout(15000)

            # Намагаємось відкрити Google
            page.goto('https://www.google.com')

            # Перевіряємо, чи завантажилась сторінка
            if 'google' in page.url.lower():
                self.proxy_statuses[proxy_id] = {'status': 'working'}
            else:
                self.proxy_statuses[proxy_id] = {'status': 'failed'}

            context.close()
            browser.close()
    except Exception as e:
        self.proxy_statuses[proxy_id] = {'status': 'failed', 'error': str(e)}
