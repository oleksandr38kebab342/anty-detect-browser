import re
from typing import Optional, Dict


def parse_proxy_line(self, line: str) -> Optional[Dict]:
    """Парсить рядок з проксі у форматі: ip:port, ip:port:user:pass, type://ip:port:user:pass, type://user:pass@ip:port"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    proxy_type = 'http'
    host = None
    port = None
    username = None
    password = None

    # Формат 1: type://user:pass@host:port або type://host:port
    protocol_match = re.match(r'^(https?|socks[45])://', line, re.IGNORECASE)
    if protocol_match:
        proxy_type = protocol_match.group(1).lower()
        line = line[len(protocol_match.group(0)):]

    # Перевіряємо наявність user:pass@
    auth_match = re.match(r'^([^:@]+):([^@]+)@(.+)$', line)
    if auth_match:
        username = auth_match.group(1)
        password = auth_match.group(2)
        line = auth_match.group(3)

    # Тепер розбираємо host:port або host:port:user:pass (якщо немає @)
    if not username:
        parts = line.split(':')
        if len(parts) >= 2:
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                return None

            # Перевіряємо чи є логін і пароль після порту
            if len(parts) >= 3:
                username = parts[2] if parts[2] else None
            if len(parts) >= 4:
                password = parts[3] if parts[3] else None
        else:
            return None
    else:
        # Якщо вже є username з @, просто розбираємо host:port
        parts = line.split(':')
        if len(parts) >= 2:
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                return None
        else:
            return None

    if not host or not port:
        return None

    # Валідація типу
    if proxy_type not in ['http', 'https', 'socks4', 'socks5']:
        proxy_type = 'http'

    return {
        'type': proxy_type,
        'host': host,
        'port': port,
        'username': username,
        'password': password
    }
