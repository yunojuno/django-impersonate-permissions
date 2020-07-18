from __future__ import annotations

import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .settings import DEFAULT_PERMISSION_EXPIRY

User = get_user_model()


def default_expiry() -> datetime.datetime:
    """Return a timestamp based on DEFAULT_EXPIRY."""
    return timezone.now() + datetime.timedelta(minutes=DEFAULT_PERMISSION_EXPIRY)


def users_impersonable(request: HttpRequest) -> models.QuerySet:
    """Return users who can be impersonated."""
    user_ids = PermissionWindow.objects.active().values_list("user_id", flat=True)
    return User.objects.filter(id__in=user_ids).order_by("first_name", "last_name")


class PermissionWindowQuerySet(models.QuerySet):
    def active(self) -> PermissionWindowQuerySet:
        """Return active and enabled PermissionWindows."""
        now = timezone.now()
        return self.filter(
            window_starts_at__lte=now, window_ends_at__gte=now, is_enabled=True
        ).order_by("window_starts_at", "window_ends_at")

    def disable(self) -> None:
        """Disable all objects in queryset."""
        self.update(is_enabled=False)


class PermissionWindowManager(models.Manager):
    @transaction.atomic
    def create(self, user: settings.AUTH_USER_MODEL, **kwargs: str) -> PermissionWindow:
        """Create new PermissionWindow and disable any existing windows."""
        user.permission_windows.active().disable()
        return super().create(user=user, **kwargs)


class PermissionWindow(models.Model):
    """
    Maintain user permission for impersonation.

    This class stores a time-based window within which a user has granted
    permission for a staff member to access their account via impersonation.

    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permission_windows",
    )
    window_starts_at = models.DateTimeField(
        default=timezone.now, help_text=_("When the permission window begins.")
    )
    window_ends_at = models.DateTimeField(
        default=default_expiry, help_text=_("When the permission window ends.")
    )
    is_enabled = models.BooleanField(
        default=True, help_text=_("Kill switch for permission window.")
    )
    created_at = models.DateTimeField(
        default=timezone.now, help_text=_("When the database record was created.")
    )

    objects = PermissionWindowManager.from_queryset(PermissionWindowQuerySet)()

    def __str__(self) -> str:
        return f"Impersonate permissions window [{self.id}] for {self.user}"

    def __repr__(self) -> str:
        return f"<PermisssionWindow id={self.id} user_id={self.user_id}>"

    @property
    def is_active(self) -> bool:
        """Return True if the window is open and permission is enabled."""
        return self.is_enabled and (
            self.window_starts_at < timezone.now() < self.window_ends_at
        )

    @property
    def ttl(self) -> datetime.timedelta:
        """Return time to expiry."""
        return self.window_ends_at - timezone.now()

    def disable(self) -> None:
        """Disable the window by setting enabled to False."""
        self.is_enabled = False
        self.save()
