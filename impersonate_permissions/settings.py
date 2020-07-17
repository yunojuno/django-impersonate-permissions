from os import getenv
from typing import Any

from django.conf import settings


def _env_or_setting(key: str, default: Any) -> Any:
    return getenv(key) or getattr(settings, key, default)


# Default expiry, in minutes
DEFAULT_EXPIRY: int = int(_env_or_setting("IMPERSONATE_PERMISSIONS_DEFAULT_EXPIRY", 60))
