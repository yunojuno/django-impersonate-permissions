import datetime
from unittest import mock

import freezegun
import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.utils import timezone

from impersonate_permissions.models import PermissionWindow, users_impersonable

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
def test_users_impersonable(start, end, enabled, exists):
    """Check that users_impersonable honours start, end and enabled values."""
    now = timezone.now()
    user = User.objects.create(username="Max")
    PermissionWindow.objects.create(
        user=user,
        window_starts_at=now + datetime.timedelta(hours=start),
        window_ends_at=now + datetime.timedelta(hours=end),
        is_enabled=enabled,
    )
    request = mock.Mock(spec=HttpRequest)
    assert users_impersonable(request).exists() == exists


@pytest.mark.django_db
class TestPermissionWindowQuerySet:
    def test_active(self):
        user = User.objects.create(username="Max")
        PermissionWindow(user=user).save()
        assert PermissionWindow.objects.active().count() == 1
        PermissionWindow(user=user).save()
        assert PermissionWindow.objects.active().count() == 2

    def test_disable(self):
        user = User.objects.create(username="Max")
        PermissionWindow(user=user).save()
        PermissionWindow(user=user).save()
        assert PermissionWindow.objects.active().count() == 2
        PermissionWindow.objects.all().disable()
        assert PermissionWindow.objects.active().count() == 0


@pytest.mark.django_db
class TestPermissionWindowManager:
    def test_create(self):
        """Test that create method disables existing windows."""
        user = User.objects.create(username="Max")
        pw1 = PermissionWindow.objects.create(user=user)
        assert pw1.is_active
        pw2 = PermissionWindow.objects.create(user=user)
        pw1.refresh_from_db()
        assert not pw1.is_active


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

    def test_ttl(self):
        pw = PermissionWindow()
        now = timezone.now()
        with freezegun.freeze_time(now):
            assert pw.ttl == pw.window_ends_at - now
