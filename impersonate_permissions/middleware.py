from __future__ import annotations

import logging
from typing import Callable

from django.contrib import messages
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)


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
        windows = request.user.permission_windows.all()
        if windows.active() | windows.open():
            return self.get_response(request)

        messages.add_message(
            request,
            messages.INFO,
            "Impersonation permission window is no longer active.",
        )

        return redirect(reverse("impersonate-stop"))
