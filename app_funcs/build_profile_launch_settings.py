import json
from typing import Dict


def build_profile_launch_settings(self, profile: Dict) -> Dict:
    """Готує налаштування запуску профілю для Playwright."""
    timezone_id = None
    if profile.get("timezone_mode") == "custom":
        timezone_id = profile.get("timezone_value")

    geolocation = None
    permissions = None
    if profile.get("geolocation_mode") == "manual":
        if profile.get("geolocation_lat") is not None and profile.get("geolocation_lon") is not None:
            geolocation = {
                "latitude": float(profile.get("geolocation_lat")),
                "longitude": float(profile.get("geolocation_lon")),
            }
            permissions = ["geolocation"]
    elif profile.get("geolocation_mode") == "block":
        permissions = []

    locale = None
    extra_http_headers = None
    if profile.get("language_mode") == "custom" and profile.get("languages"):
        try:
            languages = json.loads(profile.get("languages"))
        except Exception:
            languages = []
        if languages:
            locale = languages[0]
            extra_http_headers = {"Accept-Language": ",".join(languages)}

    return {
        "user_agent": profile.get("user_agent") or None,
        "locale": locale,
        "timezone_id": timezone_id,
        "geolocation": geolocation,
        "permissions": permissions,
        "extra_http_headers": extra_http_headers,
    }
