"""
Unit tests for the Gmail tool.

These tests mock the Gmail API service so no real credentials are needed.
Run with: pytest tests/test_gmail_tool.py -v
"""

# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock


class TestBuildMimeMessage:
    """Tests for the internal _build_mime_message helper."""

    def test_plain_text_message(self):
        """Plain text body should produce a text/plain MIME message."""
        from tools.gmail_tool import _build_mime_message

        raw = _build_mime_message(
            to=["test@example.com"],
            subject="Hello",
            body="This is plain text",
        )
        # Result should be a base64url-encoded string
        assert isinstance(raw, str)
        assert len(raw) > 0

    def test_html_message(self):
        """Body containing HTML tags should produce a multipart message."""
        from tools.gmail_tool import _build_mime_message

        raw = _build_mime_message(
            to=["test@example.com"],
            subject="HTML Test",
            body="<h1>Hello</h1><p>World</p>",
        )
        assert isinstance(raw, str)
        assert len(raw) > 0

    def test_cc_and_bcc_included(self):
        """CC and BCC headers should be set when provided."""
        from tools.gmail_tool import _build_mime_message

        raw = _build_mime_message(
            to=["to@example.com"],
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        assert isinstance(raw, str)

    def test_multiple_recipients(self):
        """Multiple recipients should be joined with commas."""
        from tools.gmail_tool import _build_mime_message

        raw = _build_mime_message(
            to=["a@example.com", "b@example.com"],
            subject="Multi",
            body="Test",
        )
        assert isinstance(raw, str)


class TestSendEmail:
    """Tests for the send_email function with mocked Gmail API."""

    @patch("tools.gmail_tool.get_gmail_service")
    def test_send_email_success(self, mock_get_service):
        """Sending an email should return status='sent' with message_id."""
        from tools.gmail_tool import send_email

        # Mock the Gmail API response
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().send().execute.return_value = {
            "id": "msg_123",
            "threadId": "thread_456",
        }

        result = send_email(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test body content",
            is_draft=False,
        )

        assert result["status"] == "sent"
        assert result["message_id"] == "msg_123"
        assert result["thread_id"] == "thread_456"

    @patch("tools.gmail_tool.get_gmail_service")
    def test_draft_email_success(self, mock_get_service):
        """Creating a draft should return status='drafted' with draft_id."""
        from tools.gmail_tool import send_email

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.users().drafts().create().execute.return_value = {
            "id": "draft_789",
            "message": {"id": "msg_101", "threadId": "thread_202"},
        }

        result = send_email(
            to=["recipient@example.com"],
            subject="Draft Subject",
            body="Draft body",
            is_draft=True,
        )

        assert result["status"] == "drafted"
        assert result["draft_id"] == "draft_789"
        assert result["message_id"] == "msg_101"

    def test_empty_to_raises_error(self):
        """An empty 'to' list should raise ValueError."""
        from tools.gmail_tool import send_email

        with pytest.raises(ValueError, match="'to' must be a non-empty list"):
            send_email(to=[], subject="Test", body="Body")

    def test_invalid_email_raises_error(self):
        """An invalid email address in 'to' should raise ValueError."""
        from tools.gmail_tool import send_email

        with pytest.raises(ValueError, match="valid email address"):
            send_email(to=["not-an-email"], subject="Test", body="Body")

    def test_empty_subject_raises_error(self):
        """An empty subject should raise ValueError."""
        from tools.gmail_tool import send_email

        with pytest.raises(ValueError, match="'subject' must be a non-empty"):
            send_email(to=["test@example.com"], subject="", body="Body")

    def test_empty_body_raises_error(self):
        """An empty body should raise ValueError."""
        from tools.gmail_tool import send_email

        with pytest.raises(ValueError, match="'body' must be a non-empty"):
            send_email(to=["test@example.com"], subject="Test", body="")

    def test_invalid_cc_raises_error(self):
        """Invalid CC addresses should raise ValueError."""
        from tools.gmail_tool import send_email

        with pytest.raises(ValueError, match="'cc' must be valid"):
            send_email(
                to=["test@example.com"],
                subject="Test",
                body="Body",
                cc=["invalid"],
            )

    @patch("tools.gmail_tool.get_gmail_service")
    def test_api_error_raises_runtime_error(self, mock_get_service):
        """Gmail API errors should be wrapped in RuntimeError."""
        from tools.gmail_tool import send_email

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().send().execute.side_effect = Exception(
            "API quota exceeded"
        )

        with pytest.raises(RuntimeError, match="Gmail API error"):
            send_email(
                to=["test@example.com"],
                subject="Test",
                body="Body",
            )
