"""Acoruss Mailer API client.

Thin async wrapper around https://mailer.acoruss.com/api/v1/messages
for transactional email delivery.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

ACORUSS_MAILER_API_URL = "https://mailer.acoruss.com/api/v1/messages"
REQUEST_TIMEOUT = 15  # seconds


@dataclass(slots=True)
class Email:
    """Represents a single outbound email."""

    to: list[str]
    subject: str
    html: str
    text: str = ""
    from_email: str = ""
    from_name: str = ""
    reply_to: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def to_payload(self) -> dict:
        """Serialise to the Acoruss Mailer API request body."""
        payload: dict = {
            "to": self.to,
            "subject": self.subject,
            "html": self.html,
        }
        if self.text:
            payload["text"] = self.text
        if self.from_email:
            payload["from_email"] = self.from_email
        if self.from_name:
            payload["from_name"] = self.from_name
        if self.reply_to:
            payload["reply_to"] = self.reply_to
        if self.tags:
            payload["tags"] = self.tags
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


class AcorussMailerError(Exception):
    """Raised when the Acoruss Mailer API returns an error."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Acoruss Mailer {status_code}: {detail}")


async def send(email: Email) -> str:
    """Send a single email via the Acoruss Mailer API.

    Returns the queued message ID on success.
    Raises ``AcorussMailerError`` on failure.
    """
    api_key: str = getattr(settings, "ACORUSS_MAILER_KEY", "")
    if not api_key:
        raise AcorussMailerError(0, "ACORUSS_MAILER_KEY is not configured")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            ACORUSS_MAILER_API_URL,
            headers=headers,
            json=email.to_payload(),
        )

    if response.status_code == 202:
        data = response.json()
        message_id = data.get("data", {}).get("id", "unknown")
        logger.info("Email queued via Acoruss Mailer: %s (subject=%r)", message_id, email.subject)
        return message_id

    # Error path
    try:
        body = response.json()
        detail = body.get("error", {}).get("message", response.text)
    except Exception:
        detail = response.text

    raise AcorussMailerError(response.status_code, detail)
