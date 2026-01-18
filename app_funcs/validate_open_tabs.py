from typing import List
from urllib.parse import urlparse


def validate_open_tabs(self, value: str) -> List[str]:
    """Повертає список некоректних URL."""
    invalid = []
    for url in self.parse_open_tabs(value):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            invalid.append(url)
    return invalid
