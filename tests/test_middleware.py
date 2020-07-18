import datetime
from unittest import mock

import pytest
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone

from impersonate_permissions.models import PermissionWindow
from impersonate_permissions.settings import PERMISSION_EXPIRY_WARNING_INTERVAL

from impersonate_permissions.middleware import (  # add_message_expired,; add_message_impersonating,
    ImpersonatePermissionsMiddleware,
    add_message,
)

User = get_user_model()


@pytest.mark.django_db
class TestMiddlewareFunctions:
    @mock.patch("impersonate_permissions.middleware.DISPLAY_PERMISSION_MESSAGES", False)
    @mock.patch("impersonate_permissions.middleware.messages")
    def test_add_message__disabled(self, mock_messages):
        user = User.objects.create(username="user")
        window = PermissionWindow.objects.create(user=user)
        request = mock.Mock(spec=HttpRequest, path="/", user=user)
        add_message(request, window, messages.INFO, "does_not_exist")
        assert mock_messages.add_message.call_count == 0

    @mock.patch("impersonate_permissions.middleware.DISPLAY_PERMISSION_MESSAGES", True)
    @mock.patch("impersonate_permissions.middleware.messages")
    def test_add_message(self, mock_messages):
        user = User.objects.create(username="user")
        window = PermissionWindow.objects.create(user=user)
        request = mock.Mock(spec=HttpRequest, path="/", user=user)
        add_message(request, window, messages.INFO, "impersonating")
        mock_messages.add_message.assert_called_once_with(
            request, messages.INFO, mock.ANY
        )


@pytest.mark.django_db
class TestImpersonatePermissionsMiddleware:
    def test_middleware__not_impersonating(self):
        user = User.objects.create(username="user")
        user.is_impersonate = False
        request = mock.Mock(spec=HttpRequest, path="/", user=user)
        middleware = ImpersonatePermissionsMiddleware(lambda r: HttpResponse())
        response = middleware(request)
        assert response.status_code == 200

    def test_middleware__impersonate_stop(self):
        user = User.objects.create(username="user")
        user.is_impersonate = True
        request = mock.Mock(spec=HttpRequest, user=user)
        request.path = reverse("impersonate-stop")
        middleware = ImpersonatePermissionsMiddleware(lambda r: HttpResponse())
        response = middleware(request)
        assert response.status_code == 200

    @mock.patch("impersonate_permissions.middleware.add_message")
    def test_middleware__impersonating(self, mock_msg):
        user1 = User.objects.create(username="impersonator")
        user2 = User.objects.create(username="impersonating")
        user2.is_impersonate = True
        window = PermissionWindow.objects.create(user=user2)
        request = mock.Mock(spec=HttpRequest, path="/", user=user2, real_user=user1)
        middleware = ImpersonatePermissionsMiddleware(lambda r: HttpResponse())
        assert window.is_active
        assert window.ttl > PERMISSION_EXPIRY_WARNING_INTERVAL
        response = middleware(request)
        assert response.status_code == 200
        mock_msg.assert_called_once_with(
            request, window, messages.INFO, "impersonating"
        )

    @mock.patch("impersonate_permissions.middleware.add_message")
    def test_middleware__expired(self, mock_msg):
        user1 = User.objects.create(username="impersonator")
        user2 = User.objects.create(username="impersonating")
        user2.is_impersonate = True
        window = PermissionWindow.objects.create(user=user2)
        window.disable()
        request = mock.Mock(spec=HttpRequest, path="/", user=user2, real_user=user1)
        middleware = ImpersonatePermissionsMiddleware(lambda r: HttpResponse())
        assert not window.is_active
        response = middleware(request)
        assert response.status_code == 302
        assert response.url == reverse("impersonate-stop")
        mock_msg.assert_called_once_with(request, None, messages.INFO, "expired")
