"""
Django test settings for Acoruss web application.
"""

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = "django-insecure-test-key-only"  # noqa: S105

ALLOWED_HOSTS = ["*"]

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use in-memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Use a separate test database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "acoruss_test",
        "USER": "acoruss",
        "PASSWORD": "acoruss",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {
            "NAME": "acoruss_test",
        },
    },
}

# Use simple static files storage in tests
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
