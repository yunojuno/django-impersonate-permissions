import datetime

from django.conf import settings

# Default permission window expiry, in minutes
DEFAULT_PERMISSION_EXPIRY: int = settings.IMPERSONATE.get(
    "DEFAULT_PERMISSION_EXPIRY", 60
)

# Set to True to display flash messages when impersonating
DISPLAY_PERMISSION_MESSAGES: bool = settings.IMPERSONATE.get(
    "DISPLAY_PERMISSION_MESSAGES", True
)

# Interval within which to display flash messages as warnings
PERMISSION_EXPIRY_WARNING_INTERVAL = datetime.timedelta(
    minutes=settings.IMPERSONATE.get("PERMISSION_EXPIRY_WARNING_INTERVAL", 10)
)
