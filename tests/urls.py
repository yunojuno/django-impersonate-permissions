from django.contrib import admin
from django.urls import include, path

from .views import test_view

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("impersonate/", include("impersonate.urls")),
    path("test/", test_view, name="test_view"),
]
