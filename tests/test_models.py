import datetime
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.utils import timezone

from impersonate_permissions.models import PermissionWindow, permitted_users

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "start,end,enabled,exists",
    (
        (-1, 1, True, True),
        (-1, 1, False, False),
        (0, 1, True, True),
        (1, 2, True, False),
        (-2, -1, True, False),
    ),
)
def test_permitted_users(start, end, enabled, exists):
    """Check that permitted_users honours start, end and enabled values."""
    now = timezone.now()
    user = User.objects.create(username="Max")
    PermissionWindow.objects.create(
        user=user,
        windows_starts_at=now + datetime.timedelta(hours=start),
        window_ends_at=now + datetime.timedelta(hours=end),
        is_enabled=enabled,
    )
    request = mock.Mock(spec=HttpRequest)
    assert permitted_users(request).exists() == exists


class TestPermissionWindow:
    @pytest.mark.django_db
    def test_disable(self):
        user = User.objects.create(username="Max")
        pw = PermissionWindow.objects.create(user=user,)
        assert pw.is_active
        pw.disable()
        assert not pw.is_active
        pw.refresh_from_db()
        assert not pw.is_active
