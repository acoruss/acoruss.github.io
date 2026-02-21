"""Custom user model for Acoruss."""

from typing import ClassVar

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class AcorussUserManager(UserManager):
    """Custom user manager with email-based user creation."""

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        """Create a superuser with email as username if username not provided."""
        if not username and email:
            username = email
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model for Acoruss web application."""

    email = models.EmailField("email address", unique=True)
    is_admin = models.BooleanField(
        "admin status",
        default=False,
        help_text="Designates whether the user can access the admin dashboard.",
    )

    objects = AcorussUserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering: ClassVar[list[str]] = ["-date_joined"]

    def __str__(self) -> str:
        return self.email or self.username

    @property
    def is_acoruss_member(self) -> bool:
        """Check if the user has an @acoruss.com email."""
        return self.email.endswith("@acoruss.com") if self.email else False
