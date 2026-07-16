"""
Unit tests for the Google Docs tool.

These tests mock the Google Docs API service so no real credentials are needed.
Run with: pytest tests/test_docs_tool.py -v
"""

# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock


class TestGetDocumentEndIndex:
    """Tests for the _get_document_end_index helper."""

    @patch("tools.google_docs_tool.get_docs_service")
    def test_returns_correct_end_index(self, mock_get_service):
        """Should return endIndex - 1 of the last body element."""
        from tools.google_docs_tool import _get_document_end_index

        mock_service = MagicMock()
        mock_service.documents().get().execute.return_value = {
            "body": {
                "content": [
                    {"endIndex": 1},
                    {"endIndex": 50},
                    {"endIndex": 120},
                ]
            }
        }

        result = _get_document_end_index(mock_service, "doc_123")
        assert result == 119  # 120 - 1

    @patch("tools.google_docs_tool.get_docs_service")
    def test_empty_document_returns_1(self, mock_get_service):
        """An empty document should return index 1."""
        from tools.google_docs_tool import _get_document_end_index

        mock_service = MagicMock()
        mock_service.documents().get().execute.return_value = {
            "body": {"content": []}
        }

        result = _get_document_end_index(mock_service, "doc_123")
        assert result == 1

    @patch("tools.google_docs_tool.get_docs_service")
    def test_api_error_raises_runtime_error(self, mock_get_service):
        """API errors should be wrapped in RuntimeError."""
        from tools.google_docs_tool import _get_document_end_index

        mock_service = MagicMock()
        mock_service.documents().get().execute.side_effect = Exception("Not found")

        with pytest.raises(RuntimeError, match="Failed to fetch Google Doc"):
            _get_document_end_index(mock_service, "bad_doc")


class TestParseMarkdownToRequests:
    """Tests for the markdown parsing logic."""

    def test_plain_line_produces_insert_text(self):
        """A plain line should produce a single insertText request."""
        from tools.google_docs_tool import _parse_markdown_to_requests

        requests = _parse_markdown_to_requests("Hello world", start_index=1)
        # Should have at least one insertText request
        insert_requests = [r for r in requests if "insertText" in r]
        assert len(insert_requests) >= 1
        assert insert_requests[0]["insertText"]["text"] == "Hello world\n"

    def test_heading_produces_style_update(self):
        """A markdown heading should produce insertText + updateParagraphStyle."""
        from tools.google_docs_tool import _parse_markdown_to_requests

        requests = _parse_markdown_to_requests("# My Heading", start_index=1)
        insert_requests = [r for r in requests if "insertText" in r]
        style_requests = [r for r in requests if "updateParagraphStyle" in r]

        assert len(insert_requests) >= 1
        assert insert_requests[0]["insertText"]["text"] == "My Heading\n"
        assert len(style_requests) >= 1
        assert (
            style_requests[0]["updateParagraphStyle"]["paragraphStyle"][
                "namedStyleType"
            ]
            == "HEADING_1"
        )

    def test_h2_heading(self):
        """## should map to HEADING_2."""
        from tools.google_docs_tool import _parse_markdown_to_requests

        requests = _parse_markdown_to_requests("## Subheading", start_index=1)
        style_requests = [r for r in requests if "updateParagraphStyle" in r]
        assert style_requests[0]["updateParagraphStyle"]["paragraphStyle"][
            "namedStyleType"
        ] == "HEADING_2"

    def test_bold_produces_text_style_update(self):
        """**bold** text should produce an updateTextStyle with bold=True."""
        from tools.google_docs_tool import _parse_markdown_to_requests

        requests = _parse_markdown_to_requests("This is **bold** text", start_index=1)
        bold_requests = [
            r
            for r in requests
            if "updateTextStyle" in r and r["updateTextStyle"]["textStyle"].get("bold")
        ]
        assert len(bold_requests) >= 1

    def test_multiline_content(self):
        """Multiple lines should produce multiple insertText requests."""
        from tools.google_docs_tool import _parse_markdown_to_requests

        content = "Line one\nLine two\nLine three"
        requests = _parse_markdown_to_requests(content, start_index=1)
        insert_requests = [r for r in requests if "insertText" in r]
        assert len(insert_requests) == 3


class TestAppendContent:
    """Tests for the append_content function with mocked Docs API."""

    @patch("tools.google_docs_tool.get_docs_service")
    def test_append_plain_text_success(self, mock_get_service):
        """Appending plain text should return status='appended'."""
        from tools.google_docs_tool import append_content

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Mock document get (for end index)
        mock_service.documents().get().execute.return_value = {
            "body": {"content": [{"endIndex": 50}]}
        }

        # Mock batchUpdate
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = append_content(
            document_id="doc_123",
            content="Hello, this is appended text.",
            format="plain",
        )

        assert result["status"] == "appended"
        assert result["document_id"] == "doc_123"
        assert result["characters_added"] == len("Hello, this is appended text.")

    @patch("tools.google_docs_tool.get_docs_service")
    def test_append_markdown_success(self, mock_get_service):
        """Appending markdown content should succeed."""
        from tools.google_docs_tool import append_content

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.documents().get().execute.return_value = {
            "body": {"content": [{"endIndex": 10}]}
        }
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = append_content(
            document_id="doc_123",
            content="# Title\nSome **bold** text",
            format="markdown",
        )

        assert result["status"] == "appended"

    def test_empty_document_id_raises_error(self):
        """An empty document_id should raise ValueError."""
        from tools.google_docs_tool import append_content

        with pytest.raises(ValueError, match="'document_id' must be a non-empty"):
            append_content(document_id="", content="Some text")

    def test_empty_content_raises_error(self):
        """Empty content should raise ValueError."""
        from tools.google_docs_tool import append_content

        with pytest.raises(ValueError, match="'content' must be a non-empty"):
            append_content(document_id="doc_123", content="")

    def test_invalid_format_raises_error(self):
        """An unsupported format should raise ValueError."""
        from tools.google_docs_tool import append_content

        with pytest.raises(ValueError, match="'format' must be one of"):
            append_content(
                document_id="doc_123", content="Text", format="xml"
            )

    @patch("tools.google_docs_tool.get_docs_service")
    def test_api_error_raises_runtime_error(self, mock_get_service):
        """Docs API errors should be wrapped in RuntimeError."""
        from tools.google_docs_tool import append_content

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.documents().get().execute.return_value = {
            "body": {"content": [{"endIndex": 10}]}
        }
        mock_service.documents().batchUpdate().execute.side_effect = Exception(
            "Permission denied"
        )

        with pytest.raises(RuntimeError, match="Google Docs API error"):
            append_content(document_id="doc_123", content="Text")
