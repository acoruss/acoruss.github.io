"""
Django test settings for Acoruss web application.
"""

from .base import *  # noqa: F403
from .base import env

DEBUG = False

SECRET_KEY = "django-insecure-test-key-only"  # noqa: S105

ALLOWED_HOSTS = ["*"]

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use in-memory email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Use DATABASE_URL if set (Docker), otherwise fallback to localhost
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://acoruss:acoruss@localhost:5432/acoruss_test"),
}
DATABASES["default"]["TEST"] = {"NAME": "acoruss_test"}

# Use simple static files storage in tests
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
