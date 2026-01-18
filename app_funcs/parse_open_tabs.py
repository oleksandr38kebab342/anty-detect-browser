from typing import List


def parse_open_tabs(self, value: str) -> List[str]:
    """Парсить список URL з поля вкладок."""
    if not value:
        return []
    lines = [line.strip() for line in value.splitlines()]
    return [line for line in lines if line]
