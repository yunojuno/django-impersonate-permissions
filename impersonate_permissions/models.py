import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .settings import DEFAULT_EXPIRY

User = get_user_model()


def default_expiry() -> datetime.datetime:
    """Return a timestamp based on DEFAULT_EXPIRY."""
    return timezone.now() + datetime.timedelta(minutes=DEFAULT_EXPIRY)


def permitted_users(request: HttpRequest) -> models.QuerySet:
    """Return users who can be impersonated."""
    now = timezone.now()
    user_ids = PermissionWindow.objects.filter(
        windows_starts_at__lte=now, window_ends_at__gte=now, is_enabled=True
    ).values_list("user_id", flat=True)
    return User.objects.filter(id__in=user_ids).order_by("first_name", "last_name")


class PermissionWindow(models.Model):
    """
    Maintain user permission for impersonation.

    This class stores a time-based window within which a user has granted
    permission for a staff member to access their account via impersonation.

    The window has a start and end date, and impersonation can begin at any
    point within this window. The window_type field is used to determine how
    the impersonation session is ended. If the window_type is 'OPEN', then
    so long as the impersonation session starts within the window, it will
    continue to exist until the staff user ends the session (stops
    impersonating). If the window_type is 'CLOSED', then the associated
    middleware will forcibly end the impersonation session at the window end
    by redirecting the request to the impersonate-stop URL.

    NB In order to have the 'CLOSED' session functionality you must install
    the middleware after the django-impersonate middleware.

    """

    class WindowTypeChoices(models.TextChoices):
        OPEN = "OPEN", _("Open-ended")
        CLOSED = "CLOSED", _("Hard-stop")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="impersonate_permissions",
    )
    windows_starts_at = models.DateTimeField(
        default=timezone.now, help_text=_("When the permission window begins.")
    )
    window_ends_at = models.DateTimeField(
        default=default_expiry, help_text=_("When the permission window ends.")
    )
    window_type = models.CharField(
        max_length=10,
        choices=WindowTypeChoices.choices,
        default=WindowTypeChoices.OPEN,
        help_text=_("How the window end timestamp should be treated."),
    )
    is_enabled = models.BooleanField(
        default=True, help_text=_("Kill switch for permission window.")
    )
    created_at = models.DateTimeField(
        default=timezone.now, help_text=_("When the database record was created.")
    )

    def __str__(self) -> str:
        return f"Impersonate permissions window [{self.id}] for {self.user}"

    def __repr__(self) -> str:
        return f"<PermisssionWindow id={self.id} user_id={self.user_id}>"

    @property
    def is_active(self) -> bool:
        """Return True if the window is open and permission is enabled."""
        return self.is_enabled and (
            self.windows_starts_at < timezone.now() < self.window_ends_at
        )

    def disable(self) -> None:
        """Disable the window by setting enabled to False."""
        self.is_enabled = False
        self.save()
