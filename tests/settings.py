from distutils.version import StrictVersion
from os import path

import django

DJANGO_VERSION = StrictVersion(django.get_version())

DEBUG = True
TEMPLATE_DEBUG = True
USE_TZ = True
USE_L10N = True

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "test.db"}}

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
    "tests",
)

MIDDLEWARE = [
    # default django middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "impersonate.middleware.ImpersonateMiddleware",
    "impersonate_permissions.middleware.ImpersonatePermissionsMiddleware",
]

PROJECT_DIR = path.abspath(path.join(path.dirname(__file__)))

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [path.join(PROJECT_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.contrib.auth.context_processors.auth",
                "impersonate_permissions.context_processors.impersonation",
            ]
        },
    }
]

AUTH_USER_MODEL = "tests.User"

STATIC_URL = "/static/"

SECRET_KEY = "secret"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(levelname)s %(message)s"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    },
    "loggers": {
        "": {"handlers": ["console"], "propagate": True, "level": "DEBUG"},
        # 'django': {
        #     'handlers': ['console'],
        #     'propagate': True,
        #     'level': 'WARNING',
        # },
    },
}

ROOT_URLCONF = "tests.urls"

###################################################
# django_coverage overrides

# Specify a list of regular expressions of module paths to exclude
# from the coverage analysis. Examples are ``'tests$'`` and ``'urls$'``.
# This setting is optional.
COVERAGE_MODULE_EXCLUDES = [
    "tests$",
    "settings$",
    "urls$",
    "locale$",
    "common.views.test",
    "__init__",
    "django",
    "migrations",
]


# app settings
IMPERSONATE = {
    "LOGIN_REDIRECT_URL": "/test",
    "CUSTOM_USER_QUERYSET": "impersonate_permissions.models.users_impersonable",
    "DEFAULT_PERMISSION_EXPIRY": 60,
    "DISPLAY_PERMISSION_MESSAGES": True,
    "PERMISSION_PERMISSION_EXPIRY_WARNING_INTERVAL": 10,
}

assert DEBUG, "This settings file can only be used with DEBUG=True"
