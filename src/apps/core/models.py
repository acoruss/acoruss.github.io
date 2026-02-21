"""Core app models."""

from typing import ClassVar

from django.db import models


class ContactSubmission(models.Model):
    """Stores contact form submissions."""

    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = "contact submission"
        verbose_name_plural = "contact submissions"

    def __str__(self) -> str:
        return f"{self.name} - {self.email} ({self.created_at:%Y-%m-%d})"
