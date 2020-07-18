from __future__ import annotations

from django.contrib import admin

from .models import PermissionWindow


class PermissionWindowAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "window_starts_at",
        "window_ends_at",
        "is_enabled",
        "is_active_",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__username",
    )
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)

    def is_active_(self, obj: PermissionWindow) -> bool:
        return obj.is_active

    is_active_.boolean = True  # type: ignore


admin.site.register(PermissionWindow, PermissionWindowAdmin)
