from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from impersonate_permissions.context_processors import impersonation

User = get_user_model()


def test_impersonation__false():
    user = User()
    user.is_impersonate = False
    request = mock.Mock(spec=HttpRequest, user=user)
    context = impersonation(request)
    assert context["is_impersonate"] is False
    assert context["impersonator"] is None
    assert context["impersonating"] is None


def test_impersonation__true():
    user = User()
    user.is_impersonate = True
    real_user = User()
    request = mock.Mock(spec=HttpRequest, user=user, real_user=real_user)
    context = impersonation(request)
    assert context["is_impersonate"] is True
    assert context["impersonator"] == real_user
    assert context["impersonating"] == user


def test_impersonation__anonymous():
    user = AnonymousUser()
    request = mock.Mock(spec=HttpRequest, user=user)
    context = impersonation(request)
    assert context["is_impersonate"] is False
    assert context["impersonator"] is None
    assert context["impersonating"] is None
