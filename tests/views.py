from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from impersonate_permissions.models import permitted_users


def test_view(request: HttpRequest) -> HttpResponse:
    users = permitted_users(request)
    return render(request, template_name="index.html", context={"users": users})
