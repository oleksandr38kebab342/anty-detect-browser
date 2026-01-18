import threading


def check_proxy(self, proxy_id: int):
    """Перевіряє валідність проксі."""
    proxy = self.db.get_proxy_by_id(proxy_id)
    if not proxy:
        return

    # Встановлюємо статус "перевіряється"
    self.proxy_statuses[proxy_id] = {'status': 'checking'}
    self.refresh_proxies()

    def check_in_thread():
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            # Формуємо проксі для requests
            proxy_url = f"{proxy['type']}://"
            if proxy.get('username') and proxy.get('password'):
                proxy_url += f"{proxy['username']}:{proxy['password']}@"
            proxy_url += f"{proxy['host']}:{proxy['port']}"

            proxies_dict = {
                'http': proxy_url,
                'https': proxy_url
            }

            # Налаштування сесії з таймаутом
            session = requests.Session()
            retry = Retry(total=1, backoff_factor=0.1)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)

            # Перевіряємо через ipify з таймаутом 15 секунд
            response = session.get(
                'https://api.ipify.org?format=json',
                proxies=proxies_dict,
                timeout=15,
                allow_redirects=True
            )

            if response.status_code == 200:
                self.proxy_statuses[proxy_id] = {'status': 'working'}
            else:
                self.proxy_statuses[proxy_id] = {
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            # Спробуємо альтернативний метод через Playwright для SOCKS
            if proxy['type'] in ['socks4', 'socks5']:
                try:
                    self.check_proxy_with_playwright(proxy, proxy_id)
                except Exception:
                    self.proxy_statuses[proxy_id] = {'status': 'failed', 'error': str(e)}
            else:
                self.proxy_statuses[proxy_id] = {'status': 'failed', 'error': str(e)}
        finally:
            # Оновлюємо UI
            self.run_ui(self.refresh_proxies)

    thread = threading.Thread(target=check_in_thread, daemon=True)
    thread.start()
