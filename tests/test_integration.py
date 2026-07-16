"""
Integration tests for the MCP server.

These tests require real Google credentials (credentials.json + token.json)
and will make actual API calls. They are marked with @pytest.mark.integration
so they can be excluded from CI/CD runs.

Run with:
    pytest tests/test_integration.py -v -m integration

Prerequisites:
    1. Place credentials.json in the project root
    2. Run `python server.py` once to complete the OAuth flow and generate token.json
    3. Set TEST_DOCUMENT_ID environment variable to a Google Doc you have write access to
    4. Set TEST_EMAIL_RECIPIENT to the email address for test drafts
"""

import os
# pyrefly: ignore [missing-import]
import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def test_document_id():
    """Get the test Google Doc ID from environment."""
    doc_id = os.getenv("TEST_DOCUMENT_ID")
    if not doc_id:
        pytest.skip("TEST_DOCUMENT_ID environment variable not set")
    return doc_id


@pytest.fixture
def test_email_recipient():
    """Get the test email recipient from environment."""
    email = os.getenv("TEST_EMAIL_RECIPIENT")
    if not email:
        pytest.skip("TEST_EMAIL_RECIPIENT environment variable not set")
    return email


class TestGmailIntegration:
    """Integration tests for Gmail tool (creates real drafts)."""

    def test_create_draft_email(self, test_email_recipient):
        """Create a real draft email in the authenticated user's Gmail."""
        from tools.gmail_tool import send_email

        result = send_email(
            to=[test_email_recipient],
            subject="[MCP Server Test] Integration Test Draft",
            body=(
                "<h2>MCP Server Integration Test</h2>"
                "<p>This draft was created by the MCP server integration test.</p>"
                "<p>If you see this, the Gmail tool is working correctly.</p>"
            ),
            is_draft=True,  # Always draft in tests — never send real emails
        )

        assert result["status"] == "drafted"
        assert result["draft_id"] is not None
        assert result["message_id"] is not None
        print(f"\n✅ Draft created successfully: draft_id={result['draft_id']}")


class TestGoogleDocsIntegration:
    """Integration tests for Google Docs tool (appends to real doc)."""

    def test_append_plain_text(self, test_document_id):
        """Append plain text to a real Google Doc."""
        from tools.google_docs_tool import append_content

        result = append_content(
            document_id=test_document_id,
            content="[Integration Test] This plain text was appended by the MCP server.",
            format="plain",
        )

        assert result["status"] == "appended"
        assert result["document_id"] == test_document_id
        assert result["characters_added"] > 0
        print(f"\n✅ Plain text appended: {result['characters_added']} chars")

    def test_append_markdown_content(self, test_document_id):
        """Append markdown-formatted content to a real Google Doc."""
        from tools.google_docs_tool import append_content

        markdown_content = (
            "## Weekly Pulse — Integration Test\n"
            "\n"
            "### Top Themes\n"
            "1. **Onboarding** — Users struggle with KYC flow\n"
            "2. **Payments** — UPI timeout issues reported\n"
            "3. **Performance** — App feels sluggish on older devices\n"
            "\n"
            "### User Quotes\n"
            "- *\"KYC took forever, almost gave up\"*\n"
            "- *\"Payments fail during peak hours\"*\n"
            "- *\"Great app but needs speed improvements\"*\n"
        )

        result = append_content(
            document_id=test_document_id,
            content=markdown_content,
            format="markdown",
        )

        assert result["status"] == "appended"
        assert result["characters_added"] > 0
        print(f"\n✅ Markdown appended: {result['characters_added']} chars")


class TestEndToEnd:
    """Full end-to-end test: append to doc, then draft an email linking to it."""

    def test_pulse_workflow(self, test_document_id, test_email_recipient):
        """Simulate the weekly pulse workflow: append to doc + draft email."""
        from tools.google_docs_tool import append_content
        from tools.gmail_tool import send_email

        # Step 1: Append pulse to Google Doc
        pulse_content = (
            "## Weekly Pulse — E2E Test\n"
            "\n"
            "**Top theme:** Onboarding friction\n"
            "**Key quote:** *\"The signup process is confusing\"*\n"
            "**Action:** Simplify the KYC flow\n"
        )

        doc_result = append_content(
            document_id=test_document_id,
            content=pulse_content,
            format="markdown",
        )
        assert doc_result["status"] == "appended"

        # Step 2: Draft email with link to the doc
        doc_url = f"https://docs.google.com/document/d/{test_document_id}/edit"
        email_result = send_email(
            to=[test_email_recipient],
            subject="[Weekly Pulse] New pulse available",
            body=(
                f"<h2>Weekly Pulse Updated</h2>"
                f"<p>The latest weekly pulse has been appended to the shared doc.</p>"
                f"<p><a href='{doc_url}'>View the pulse document</a></p>"
            ),
            is_draft=True,
        )
        assert email_result["status"] == "drafted"

        print(f"\n✅ E2E workflow complete:")
        print(f"   Doc: {doc_result['characters_added']} chars appended")
        print(f"   Email draft: {email_result['draft_id']}")
