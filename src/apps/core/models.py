"""Core app models."""

from typing import ClassVar

from django.db import models


class ContactSubmission(models.Model):
    """Stores contact form submissions."""

    name = models.CharField(max_length=255)
    email = models.EmailField()
    company = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    project_type = models.CharField(max_length=100, blank=True, default="")
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
