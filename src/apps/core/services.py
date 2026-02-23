"""Core app services."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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

    # Use customer name in display, reply-to their email so "Reply" goes to them
    from_email = f"{submission.name} via Acoruss <{settings.DEFAULT_FROM_EMAIL_ADDRESS}>"

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=recipients,
            reply_to=[f"{submission.name} <{submission.email}>"],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("Contact notification sent to %s for submission #%d", recipients, submission.pk)
    except Exception:
        logger.exception("Failed to send contact notification for submission #%d", submission.pk)
