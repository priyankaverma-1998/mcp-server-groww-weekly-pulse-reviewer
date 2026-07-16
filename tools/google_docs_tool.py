"""
Google Docs tool for the MCP server.

Provides a function to append content to an existing Google Doc
via the Google Docs API batchUpdate endpoint.

Usage (called by the MCP server, not directly):
    from tools.google_docs_tool import append_content

    result = append_content(
        document_id="1BxiMVs0XRA5nFMdKvBdBZjgmUii3Op3Rp6mLbKd",
        content="## Weekly Pulse\\nHere are the top themes...",
        format="markdown",
    )
"""

import logging
import re

from auth.google_auth import get_docs_service

logger = logging.getLogger(__name__)


def _get_document_end_index(service, document_id: str) -> int:
    """
    Fetch the document and return the end-of-body index.

    The Google Docs API requires an insertion index for batchUpdate.
    The end of the body is `body.content[-1].endIndex - 1`.

    Args:
        service: Authenticated Google Docs API service.
        document_id: The ID of the Google Doc.

    Returns:
        int: The index at the end of the document body.

    Raises:
        RuntimeError: If the document cannot be fetched.
    """
    try:
        doc = service.documents().get(documentId=document_id).execute()
        body_content = doc.get("body", {}).get("content", [])

        if not body_content:
            return 1  # Empty doc, start at index 1

        # The endIndex of the last structural element minus 1
        end_index = body_content[-1].get("endIndex", 1) - 1
        return max(end_index, 1)

    except Exception as e:
        logger.error("Failed to fetch document %s: %s", document_id, str(e))
        raise RuntimeError(
            f"Failed to fetch Google Doc '{document_id}': {str(e)}"
        ) from e


def _parse_markdown_to_requests(content: str, start_index: int) -> list[dict]:
    """
    Parse markdown content into Google Docs API batchUpdate requests.

    Supports:
        - # Heading 1, ## Heading 2, ### Heading 3
        - **bold** text
        - *italic* text
        - Plain text paragraphs

    Args:
        content: Markdown-formatted string.
        start_index: The document index where text will be inserted.

    Returns:
        List of Google Docs API request dicts (insertText + style updates).
    """
    requests = []
    style_updates = []
    current_index = start_index

    # Split content into lines for processing
    lines = content.split("\n")

    for line in lines:
        text_to_insert = ""
        heading_level = None

        # Detect heading levels
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            heading_level = len(heading_match.group(1))
            text_to_insert = heading_match.group(2) + "\n"
        else:
            text_to_insert = line + "\n"

        # Insert the raw text first
        requests.append(
            {
                "insertText": {
                    "location": {"index": current_index},
                    "text": text_to_insert,
                }
            }
        )

        # Apply heading style if detected
        if heading_level:
            heading_map = {
                1: "HEADING_1",
                2: "HEADING_2",
                3: "HEADING_3",
                4: "HEADING_4",
                5: "HEADING_5",
                6: "HEADING_6",
            }
            named_style = heading_map.get(heading_level, "NORMAL_TEXT")
            style_updates.append(
                {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": current_index,
                            "endIndex": current_index + len(text_to_insert),
                        },
                        "paragraphStyle": {"namedStyleType": named_style},
                        "fields": "namedStyleType",
                    }
                }
            )

        # Detect and apply bold (**text**)
        stripped_line = text_to_insert
        for bold_match in re.finditer(r"\*\*(.+?)\*\*", stripped_line):
            bold_start = current_index + bold_match.start()
            bold_end = current_index + bold_match.end()
            style_updates.append(
                {
                    "updateTextStyle": {
                        "range": {
                            "startIndex": bold_start,
                            "endIndex": bold_end,
                        },
                        "textStyle": {"bold": True},
                        "fields": "bold",
                    }
                }
            )

        # Detect and apply italic (*text* but not **text**)
        for italic_match in re.finditer(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", stripped_line):
            italic_start = current_index + italic_match.start()
            italic_end = current_index + italic_match.end()
            style_updates.append(
                {
                    "updateTextStyle": {
                        "range": {
                            "startIndex": italic_start,
                            "endIndex": italic_end,
                        },
                        "textStyle": {"italic": True},
                        "fields": "italic",
                    }
                }
            )

        current_index += len(text_to_insert)

    # Style updates must come after text insertions (and in reverse order)
    # to avoid index shifting issues
    requests.extend(reversed(style_updates))

    return requests


def append_content(
    document_id: str,
    content: str,
    format: str = "plain",
) -> dict:
    """
    Append content to an existing Google Doc.

    Args:
        document_id: The Google Doc ID (from the URL or API).
        content: The text content to append.
        format: "plain" for plain text, "markdown" for basic markdown
                formatting (headings, bold, italic).

    Returns:
        dict with keys:
            - status: "appended"
            - document_id: The document ID
            - characters_added: Number of characters inserted

    Raises:
        ValueError: If document_id or content is empty.
        RuntimeError: If the Google Docs API call fails.
    """
    # --- Input validation ---
    if not document_id or not isinstance(document_id, str):
        raise ValueError("'document_id' must be a non-empty string.")

    if not content or not isinstance(content, str):
        raise ValueError("'content' must be a non-empty string.")

    valid_formats = ("plain", "markdown")
    if format not in valid_formats:
        raise ValueError(f"'format' must be one of {valid_formats}, got '{format}'.")

    # --- Get Docs service and document end index ---
    service = get_docs_service()
    end_index = _get_document_end_index(service, document_id)

    # --- Build batchUpdate requests ---
    try:
        if format == "markdown":
            # Parse markdown into structured requests
            requests = _parse_markdown_to_requests(content, end_index)
        else:
            # Simple plain text insertion at end of document
            # Prepend a newline separator so appended content doesn't
            # merge with existing last paragraph
            text_to_insert = "\n" + content
            requests = [
                {
                    "insertText": {
                        "location": {"index": end_index},
                        "text": text_to_insert,
                    }
                }
            ]

        # --- Execute batchUpdate ---
        result = (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )

        logger.info(
            "Content appended to doc %s (%d characters)",
            document_id,
            len(content),
        )

        return {
            "status": "appended",
            "document_id": document_id,
            "characters_added": len(content),
        }

    except Exception as e:
        logger.error("Google Docs API error: %s", str(e))
        raise RuntimeError(f"Google Docs API error: {str(e)}") from e
