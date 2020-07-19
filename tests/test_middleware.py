import datetime
from unittest import mock

import pytest
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from impersonate.models import ImpersonationLog

from impersonate_permissions.middleware import (
    EnforcePermissionWindowMiddleware,
    ImpersonationAlertMiddleware,
    add_message,
)
from impersonate_permissions.models import PermissionWindow
from impersonate_permissions.settings import PERMISSION_EXPIRY_WARNING_INTERVAL

User = get_user_model()


@pytest.mark.django_db
class TestMiddlewareFunctions:
    @mock.patch("impersonate_permissions.middleware.messages")
    def test_add_message(self, mock_messages):
        request = mock.Mock(spec=HttpRequest, path="/")
        add_message(request, messages.INFO, "impersonating", {"foo": "bar"})
        mock_messages.add_message.assert_called_once_with(
            request, messages.INFO, mock.ANY
        )


@pytest.mark.django_db
class TestEnforcePermissionWindowMiddleware:
    def test_middleware__not_impersonating(self):
        user = User.objects.create(username="user")
        user.is_impersonate = False
        request = mock.Mock(spec=HttpRequest, path="/", user=user)
        middleware = EnforcePermissionWindowMiddleware(lambda r: HttpResponse())
        response = middleware(request)
        assert response.status_code == 200

    def test_middleware__impersonate_stop(self):
        user = User.objects.create(username="user")
        user.is_impersonate = True
        request = mock.Mock(spec=HttpRequest, user=user)
        request.path = reverse("impersonate-stop")
        middleware = EnforcePermissionWindowMiddleware(lambda r: HttpResponse())
        response = middleware(request)
        assert response.status_code == 200

    @mock.patch("impersonate_permissions.middleware.add_message")
    def test_middleware__impersonating(self, mock_msg):
        user1 = User.objects.create(username="impersonator")
        user2 = User.objects.create(username="impersonating")
        user2.is_impersonate = True
        window = PermissionWindow.objects.create(user=user2)
        request = mock.Mock(spec=HttpRequest, path="/", user=user2, real_user=user1)
        middleware = EnforcePermissionWindowMiddleware(lambda r: HttpResponse())
        assert window.is_active
        assert window.ttl > PERMISSION_EXPIRY_WARNING_INTERVAL
        response = middleware(request)
        assert response.status_code == 200
        mock_msg.assert_called_once_with(
            request, messages.INFO, "impersonating", context={"window": window}
        )

    @mock.patch("impersonate_permissions.middleware.add_message")
    def test_middleware__expired(self, mock_msg):
        user1 = User.objects.create(username="impersonator")
        user2 = User.objects.create(username="impersonating")
        user2.is_impersonate = True
        window = PermissionWindow.objects.create(user=user2)
        window.disable()
        request = mock.Mock(spec=HttpRequest, path="/", user=user2, real_user=user1)
        middleware = EnforcePermissionWindowMiddleware(lambda r: HttpResponse())
        assert not window.is_active
        response = middleware(request)
        assert response.status_code == 302
        assert response.url == reverse("impersonate-stop")
        mock_msg.assert_called_once_with(request, messages.INFO, "expired")


@pytest.mark.django_db
class TestImpersonationAlertMiddleware:
    @mock.patch("impersonate_permissions.middleware.add_message")
    def test_middleware__not_impersonating(self, mock_msg):
        user = User.objects.create(username="user")
        user.is_impersonate = False
        request = mock.Mock(spec=HttpRequest, path="/", user=user)
        middleware = ImpersonationAlertMiddleware(lambda r: HttpResponse())
        response = middleware(request)
        assert response.status_code == 200
        assert mock_msg.call_count == 0

    @mock.patch("impersonate_permissions.middleware.add_message")
    def test_middleware__anonymous(self, mock_msg):
        request = mock.Mock(spec=HttpRequest, path="/", user=AnonymousUser())
        middleware = ImpersonationAlertMiddleware(lambda r: HttpResponse())
        response = middleware(request)
        assert response.status_code == 200
        assert mock_msg.call_count == 0

    @mock.patch("impersonate_permissions.middleware.add_message")
    def test_middleware(self, mock_msg):
        from django.utils import timezone

        admin = User.objects.create(username="admin", is_staff=True)
        user = User.objects.create(username="user")
        user.is_impersonate = False
        _ = ImpersonationLog.objects.create(
            impersonating=user,
            impersonator=admin,
            session_started_at=timezone.now() - datetime.timedelta(hours=1),
        )
        request = mock.Mock(spec=HttpRequest, path="/", user=user)
        middleware = ImpersonationAlertMiddleware(lambda r: HttpResponse())
        response = middleware(request)
        assert response.status_code == 200
        mock_msg.assert_called_once_with(
            request, messages.INFO, "impersonated", context={"impersonator": admin}
        )
