from typing import Dict, Optional, Union

from django.conf import settings
from django.http import HttpRequest


def impersonation(
    request: HttpRequest,
) -> Dict[str, Union[bool, Optional[settings.AUTH_USER_MODEL]]]:
    """Add impersonate info to template context."""
    if request.user.is_impersonate:
        return {
            "is_impersonate": True,
            "impersonator": request.real_user,
            "impersonating": request.user,
        }
    return {"is_impersonate": False, "impersonator": None, "impersonating": None}
