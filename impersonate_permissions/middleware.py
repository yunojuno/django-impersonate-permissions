from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from django.conf import settings as django_settings
from django.contrib import messages
from django.db.models import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .settings import PERMISSION_EXPIRY_WARNING_INTERVAL

logger = logging.getLogger(__name__)


def add_message(
    request: HttpRequest, level: int, template_name: str, context: Dict[str, Any] = None
) -> None:
    """Add templated message using messages app."""
    template = f"impersonate_permissions/{template_name}.tpl"
    message = render_to_string(template, context=context)
    messages.add_message(request, level, message)


class EnforcePermissionWindowMiddleware:
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
            context = {"window": window}
            add_message(request, level, "impersonating", context=context)
            return self.get_response(request)

        add_message(request, messages.INFO, "expired")
        return redirect(reverse("impersonate-stop"))


class ImpersonationAlertMiddleware:
    """Display flash message to user if their account is being impersonated."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:  # noqa: C901

        if request.user.is_anonymous:
            return self.get_response(request)

        if request.user.is_impersonate:
            return self.get_response(request)

        for session in self.open_impersonation_sessions(request.user):
            context = {"impersonator": session.impersonator}
            add_message(request, messages.INFO, "impersonated", context=context)
        return self.get_response(request)

    def open_impersonation_sessions(
        self, user: django_settings.AUTH_USER_MODEL
    ) -> QuerySet:
        """Return any impersonation sessions that are still open."""
        return user.impersonated_by.filter(
            session_started_at__lte=timezone.now(), session_ended_at__isnull=True,
        )
