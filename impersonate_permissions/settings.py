from os import getenv
from typing import Any, Callable

from django.conf import settings


def _setting(key: str, default: Any, cast: Callable) -> Any:
    key = f"IMPERSONATE_PERMISSIONS_{key}"
    return cast(getenv(key) or getattr(settings, key, default))


# Default expiry, in minutes
DEFAULT_EXPIRY_MINS: int = _setting("DEFAULT_EXPIRY", 60, int)

DISPLAY_MESSAGES: bool = _setting("DISPLAY_MESSAGES", True, bool)

EXPIRY_WARNING_THRESHOLD_MINS: int = _setting("EXPIRY_WARNING_THRESHOLD_MINS", 10, int)
