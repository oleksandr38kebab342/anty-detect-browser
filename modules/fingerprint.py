"""Fingerprint utilities.

Provides User-Agent generation helpers based on OS.
"""
from typing import Dict


def generate_user_agent(os_name: str) -> str:
    """Generate a User-Agent string for the given OS.

    Args:
        os_name: Operating system name (Windows, macOS, Linux, Android, iOS).

    Returns:
        A User-Agent string matching the specified OS.
    """
    ua_map: Dict[str, str] = {
        "Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "macOS": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Linux": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Android": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "iOS": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1",
    }
    return ua_map.get(os_name, ua_map["Windows"])
