"""Core app services."""

import logging

from django.conf import settings
from django.template.loader import render_to_string

from .mailer import AcorussMailerError, Email
from .mailer import send as mailer_send
from .models import ContactSubmission

logger = logging.getLogger(__name__)


async def send_contact_notification(submission: ContactSubmission) -> None:
    """Send email notification to team when a contact form is submitted."""
    recipients: list[str] = getattr(
        settings,
        "CONTACT_NOTIFICATION_EMAILS",
        ["musale@acoruss.com", "andia@acoruss.com"],
    )

    if not recipients:
        logger.warning("No CONTACT_NOTIFICATION_EMAILS configured, skipping notification.")
        return

    project_type_display = (
        submission.project_type.replace("_", " ").title() if submission.project_type else "Not specified"
    )

    subject = f"New Contact Submission from {submission.name}"

    # Plain text version
    text_body = (
        f"New contact form submission received:\n\n"
        f"Name: {submission.name}\n"
        f"Email: {submission.email}\n"
        f"Company: {submission.company or 'Not provided'}\n"
        f"Phone: {submission.phone or 'Not provided'}\n"
        f"Project Type: {project_type_display}\n"
        f"Message:\n{submission.message}\n\n"
        f"Submitted: {submission.created_at:%Y-%m-%d %H:%M}\n\n"
        f"View in dashboard: {settings.SITE_URL}/dashboard/contacts/{submission.pk}/\n"
    )

    # HTML version
    html_body = render_to_string(
        "emails/contact_notification.html",
        {
            "submission": submission,
            "project_type_display": project_type_display,
            "dashboard_url": f"{settings.SITE_URL}/dashboard/contacts/{submission.pk}/",
        },
    )

    email = Email(
        to=recipients,
        subject=subject,
        html=html_body,
        text=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL_ADDRESS,
        from_name=f"{submission.name} via Acoruss",
        reply_to=submission.email,
        tags=["contact-form"],
        metadata={"submission_id": str(submission.pk)},
    )

    try:
        message_id = await mailer_send(email)
        logger.info(
            "Contact notification queued (%s) for submission #%d → %s",
            message_id,
            submission.pk,
            recipients,
        )
    except AcorussMailerError:
        logger.exception("Failed to send contact notification for submission #%d", submission.pk)
