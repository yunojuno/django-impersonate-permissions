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

from .settings import DISPLAY_MESSAGES, EXPIRY_WARNING_THRESHOLD_MINS

logger = logging.getLogger(__name__)


def add_message_impersonating(request: HttpRequest, window: PermissionWindow) -> None:
    if not DISPLAY_MESSAGES:
        return
    if window.ttl.total_seconds() < (EXPIRY_WARNING_THRESHOLD_MINS * 60):
        level = messages.WARNING
    else:
        level = messages.INFO
    message = render_to_string(
        "impersonate_permissions/impersonating.tpl", context={"window": window}
    )
    messages.add_message(request, level, message)


def add_message_expired(request: HttpRequest, window: PermissionWindow) -> None:
    if not DISPLAY_MESSAGES:
        return
    message = render_to_string(
        "impersonate_permissions/expired.tpl", context={"window": window}
    )
    messages.add_message(request, messages.INFO, message)


class ImpersonatePermissionsMiddleware:
    """
    Extract and verify request tokens from incoming GET requests.

    This middleware is used to perform initial JWT verfication of
    link tokens.

    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:  # noqa: C901
        """
        Verify impersonation permissions.

        This call will fail hard if the request has no user attribute.
        """
        if not request.user.is_impersonate:
            return self.get_response(request)

        # don't interfere with this page, otherwise we get into loop
        if request.path == reverse("impersonate-stop"):
            return self.get_response(request)

        # the user being impersonated is in the permitted_users
        window = request.user.permission_windows.active().last()
        if window:
            add_message_impersonating(request, window)
            return self.get_response(request)

        add_message_expired(request, window)
        return redirect(reverse("impersonate-stop"))
