"""
Gmail tool for the MCP server.

Provides functions to send emails and create drafts via the Gmail API.

Usage (called by the MCP server, not directly):
    from tools.gmail_tool import send_email

    result = send_email(
        to=["recipient@example.com"],
        subject="Weekly Pulse",
        body="<h1>This week's highlights</h1>...",
        is_draft=False,
    )
"""

import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from auth.google_auth import get_gmail_service

logger = logging.getLogger(__name__)


def _build_mime_message(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> str:
    """
    Build a MIME message and return it as a base64url-encoded string.

    Automatically detects HTML content (if body contains '<' tags) and sets
    the appropriate MIME subtype.

    Args:
        to: List of recipient email addresses.
        subject: Email subject line.
        body: Email body (plain text or HTML).
        cc: Optional list of CC recipients.
        bcc: Optional list of BCC recipients.

    Returns:
        Base64url-encoded string of the MIME message.
    """
    # Detect if body contains HTML
    is_html = "<" in body and ">" in body

    if is_html:
        # Create multipart message with both plain text and HTML
        message = MIMEMultipart("alternative")
        # Add plain text fallback (strip tags naively for fallback)
        plain_body = body.replace("<br>", "\n").replace("<br/>", "\n")
        message.attach(MIMEText(plain_body, "plain"))
        message.attach(MIMEText(body, "html"))
    else:
        message = MIMEText(body, "plain")

    message["To"] = ", ".join(to)
    message["Subject"] = subject

    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)

    # Encode to base64url format as required by Gmail API
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw


def send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    is_draft: bool = False,
) -> dict:
    """
    Send an email or create a draft via Gmail API.

    Args:
        to: List of recipient email addresses.
        subject: Email subject line.
        body: Email body content (plain text or HTML).
        cc: Optional list of CC recipients.
        bcc: Optional list of BCC recipients.
        is_draft: If True, creates a draft instead of sending.

    Returns:
        dict with keys:
            - status: "sent" or "drafted"
            - message_id: Gmail message ID
            - thread_id: Gmail thread ID (if available)
            - draft_id: Gmail draft ID (only when is_draft=True)

    Raises:
        ValueError: If 'to' is empty or contains invalid entries.
        Exception: If the Gmail API call fails.
    """
    # --- Input validation ---
    if not to or not isinstance(to, list):
        raise ValueError("'to' must be a non-empty list of email addresses.")

    if not all(isinstance(addr, str) and "@" in addr for addr in to):
        raise ValueError("All entries in 'to' must be valid email address strings.")

    if not subject or not isinstance(subject, str):
        raise ValueError("'subject' must be a non-empty string.")

    if not body or not isinstance(body, str):
        raise ValueError("'body' must be a non-empty string.")

    # Validate optional fields
    if cc and not all(isinstance(addr, str) and "@" in addr for addr in cc):
        raise ValueError("All entries in 'cc' must be valid email address strings.")

    if bcc and not all(isinstance(addr, str) and "@" in addr for addr in bcc):
        raise ValueError("All entries in 'bcc' must be valid email address strings.")

    # --- Build MIME message ---
    raw_message = _build_mime_message(to, subject, body, cc, bcc)

    # --- Get Gmail service ---
    service = get_gmail_service()

    try:
        if is_draft:
            # Create a draft
            draft_body = {"message": {"raw": raw_message}}
            result = (
                service.users()
                .drafts()
                .create(userId="me", body=draft_body)
                .execute()
            )
            logger.info("Draft created: draft_id=%s", result.get("id"))
            return {
                "status": "drafted",
                "draft_id": result.get("id"),
                "message_id": result.get("message", {}).get("id"),
                "thread_id": result.get("message", {}).get("threadId"),
            }
        else:
            # Send the email
            send_body = {"raw": raw_message}
            result = (
                service.users()
                .messages()
                .send(userId="me", body=send_body)
                .execute()
            )
            logger.info("Email sent: message_id=%s", result.get("id"))
            return {
                "status": "sent",
                "message_id": result.get("id"),
                "thread_id": result.get("threadId"),
            }
    except Exception as e:
        logger.error("Gmail API error: %s", str(e))
        raise RuntimeError(f"Gmail API error: {str(e)}") from e
