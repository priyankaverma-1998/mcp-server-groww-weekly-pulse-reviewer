"""
MCP Server for Google Workspace — Gmail & Google Docs.

This is the main entry point. It creates a FastMCP server and registers
two tools that any MCP-compatible AI agent can discover and invoke:

  1. gmail_send_email     — Send or draft emails via Gmail
  2. google_docs_append   — Append content to a Google Doc

Run locally:
    python server.py

Test with MCP Inspector:
    mcp dev server.py

Connect to Claude Desktop:
    Add to claude_desktop_config.json:
    {
      "mcpServers": {
        "google-workspace": {
          "command": "python",
          "args": ["path/to/server.py"]
        }
      }
    }
"""

import sys
import logging

# pyrefly: ignore [missing-import]
from mcp.server.fastmcp import FastMCP

from tools.gmail_tool import send_email
from tools.google_docs_tool import append_content

# ---------------------------------------------------------------------------
# Logging — must go to stderr (stdout is the JSON-RPC transport for stdio)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Create the MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "google-workspace-mcp",
    instructions=(
        "MCP server that provides Gmail and Google Docs tools. "
        "Send/draft emails and append content to Google Docs."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1: Gmail — Send or Draft Email
# ---------------------------------------------------------------------------
@mcp.tool()
def gmail_send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    is_draft: bool = False,
) -> dict:
    """Send an email or create a draft via the authenticated Gmail account.

    Use this tool to send emails to recipients or save drafts for later review.
    The body can be plain text or HTML. Set is_draft=True to save as a draft
    instead of sending immediately.

    Args:
        to: List of recipient email addresses (required).
        subject: Email subject line (required).
        body: Email body — plain text or HTML (required).
        cc: Optional list of CC recipient email addresses.
        bcc: Optional list of BCC recipient email addresses.
        is_draft: If True, saves as a draft instead of sending. Default: False.

    Returns:
        A dict with:
          - status: "sent" or "drafted"
          - message_id: Gmail message ID
          - thread_id: Gmail thread ID
          - draft_id: (only when is_draft=True) Gmail draft ID
    """
    logger.info(
        "gmail_send_email called: to=%s, subject='%s', is_draft=%s",
        to,
        subject,
        is_draft,
    )

    try:
        result = send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            is_draft=is_draft,
        )
        logger.info("gmail_send_email result: %s", result)
        return result

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise
    except RuntimeError as e:
        logger.error("Gmail API error: %s", str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error in gmail_send_email: %s", str(e))
        raise RuntimeError(f"Unexpected error: {str(e)}") from e


# ---------------------------------------------------------------------------
# Tool 2: Google Docs — Append Content
# ---------------------------------------------------------------------------
@mcp.tool()
def google_docs_append(
    document_id: str,
    content: str,
    format: str = "plain",
) -> dict:
    """Append content to an existing Google Doc.

    Use this tool to add text to the end of a Google Doc. The document must
    already exist and be accessible by the authenticated user. Supports
    plain text and basic markdown formatting (headings, bold, italic).

    Args:
        document_id: The Google Doc ID (found in the document URL).
        content: The text content to append.
        format: "plain" for plain text (default), or "markdown" for basic
                markdown formatting support (headings, bold, italic).

    Returns:
        A dict with:
          - status: "appended"
          - document_id: The document ID
          - characters_added: Number of characters inserted
    """
    logger.info(
        "google_docs_append called: document_id='%s', format='%s', content_length=%d",
        document_id,
        format,
        len(content),
    )

    try:
        result = append_content(
            document_id=document_id,
            content=content,
            format=format,
        )
        logger.info("google_docs_append result: %s", result)
        return result

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise
    except RuntimeError as e:
        logger.error("Google Docs API error: %s", str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error in google_docs_append: %s", str(e))
        raise RuntimeError(f"Unexpected error: {str(e)}") from e


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    
    logger.info("Starting Google Workspace MCP Server...")
    
    # Railway automatically sets the PORT environment variable.
    # If it's set, we use SSE transport for remote connections.
    port = os.environ.get("PORT")
    
    if port:
        logger.info(f"PORT environment variable found ({port}). Starting with SSE transport...")
        mcp.run(transport="sse", port=int(port))
    else:
        logger.info("No PORT environment variable found. Starting with stdio transport...")
        mcp.run()
