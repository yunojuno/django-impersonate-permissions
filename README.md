# Django Impersonate Permissions

Add ability to control impersonate permissions.

Impersonate is a powerful Django app that allow site admins to log in to a user's account, and take
actions on their behalf. This can be invalulable in providing technical support. However, with great
power comes great responsiblity, and operationally you should **never** impersonate a user without
their explicit consent.

This app provides a mechanism for recording user consent, and enforcing it.

## How it works

The core concept is the "permission window". This is a time period during which the user has granted
access to their account. How you determine when to ask for access is up to you - this library makes
no assumptions about that.

The starting point is saving a new `PermissionWindow` object:

```python
# views.py
def grant_permission(request):
    """Create a new PermissionWindow, allowing the user to be impersonated."""
    window = PermissionWindow.objects.create(user=request.user)
    return HttpResponse("OK")
```

Once you have an active PermissionWindow, the user will appear in the `users_impersonable` queryset.
Whilst you are impersonating a user, the middleware will check that the permissions window is still
valid. If it expires (or is disabled), the middleware will redirect the request to the
`impersonate-stop` URL, effectively logging the impersonator out of the impersonation session.

## Use

The app itself contains a model, `PermissionWindow`, that is use to record a user's permission, and
a middleware class, `ImpersonatePermissionsMiddleware` that is used to enforce it.

You will need to add the middleware to your `MIDDLEWARE` Django settings. It also contains a
function `users_impersonable` that you should set to the as the impersonate `CUSTOM_USER_QUERYSET`
function:

```python
# settings.py
INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "impersonate",
    "impersonate_permissions",
    ...
)

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "impersonate.middleware.ImpersonateMiddleware",
    "impersonate_permissions.middleware.ImpersonatePermissionsMiddleware",
    ...
)

IMPERSONATE = {
    "CUSTOM_USER_QUERYSET": "impersonate_permissions.models.users_impersonable"
}
```

## Settings

The following settings can be set in the Django settings module, as part of the `IMPERSONATE`
dictionary.

**DEFAULT_PERMISSION_EXPIRY**

An integer value that defines the default length of a permission 'window', in minutes, thereby
setting its expiry.

Default value is 60 - which equates to a one hour window.

**DISPLAY_PERMISSION_MESSAGES**

A bool value that controls whether the middleware should add messages using the Django messages
framework. If True, a message is set whilst impersonating, and another is set when a
PermissionWindow has expired, and the impersonation session cut.

Default value is `True`

**PERMISSION_EXPIRY_WARNING_INTERVAL**

An integer value which is used to turn the impersation message level from `INFO` to `WARNING`. Value
is in minutes.

Default value is 10, which means that the message will change 10 minutes before the session expires.

## License

MIT.

## Contributing

If you want to contribute, add features, fix bugs - thank you.

The project uses Poetry to handle dependencies, and it comes will a working Django project that you
can use for testing.

### Tests

To begin, it's best to install the virtualenv and check that the tests run:

```shell
$ poetry install
$ poetry run pytest
```

Once you have a working test run, you can set up the project locally (it uses SQLite), create a
superuser account, and spin up the site:

```shell
$ poetry shell
(venv) $ python manage.py migrate
(venv) $ python manage.py createsuperuser
(venv) $ python manage.py runserver
```

### Code style

The project contains a `pre-commit` config, and you should set this up before committing any code:

```shell
$ pre-commit install
```

Code must be formatted using `isort` and `black`.

All new code should use type hints.

### CI

The project contains a `.travis.yml` config, and the tests will run on any new PR. This config runs
the tests and a suite of linting / formatting tools: `isort`, `black`, `pylint`, `flake8` (with
`bandit` and `pydocstyle`) and `mypy`.
