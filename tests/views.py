from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from impersonate_permissions.models import users_impersonable


def test_view(request: HttpRequest) -> HttpResponse:
    users = users_impersonable(request)
    return render(request, template_name="index.html", context={"users": users})
