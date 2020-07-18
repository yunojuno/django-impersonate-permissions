from __future__ import annotations

import logging
from typing import Callable

from django.contrib import messages
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse

from impersonate_permissions.models import PermissionWindow

from .settings import DISPLAY_PERMISSION_MESSAGES, PERMISSION_EXPIRY_WARNING_INTERVAL

logger = logging.getLogger(__name__)


def add_message(
    request: HttpRequest, window: PermissionWindow, level: int, template_name: str
) -> None:
    if not DISPLAY_PERMISSION_MESSAGES:
        return
    template = f"impersonate_permissions/{template_name}.tpl"
    message = render_to_string(template, context={"window": window})
    messages.add_message(request, level, message)


class ImpersonatePermissionsMiddleware:
    """Verify impersonation permissions, and log user out if none exists."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:  # noqa: C901
        if not request.user.is_impersonate:
            return self.get_response(request)

        # don't interfere with this page, otherwise we get into loop
        if request.path == reverse("impersonate-stop"):
            return self.get_response(request)

        # the user being impersonated is in the users_impersonable
        window = request.user.permission_windows.active().last()
        if window:
            level = (
                messages.INFO
                if window.ttl > PERMISSION_EXPIRY_WARNING_INTERVAL
                else messages.WARNING
            )
            add_message(request, window, level, "impersonating")
            return self.get_response(request)

        add_message(request, window, messages.INFO, "expired")
        return redirect(reverse("impersonate-stop"))
