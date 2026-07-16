"""
Quick smoke test for the MCP server tools.
Tests Gmail (draft) and optionally Google Docs (append).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from tools.gmail_tool import send_email
from tools.google_docs_tool import append_content


def test_gmail_draft():
    """Create a test draft email."""
    print("=" * 50)
    print("TEST 1: Gmail — Create Draft Email")
    print("=" * 50)

    try:
        result = send_email(
            to=["test@example.com"],
            subject="[MCP Server Test] Hello from MCP!",
            body=(
                "<h2>MCP Server Test</h2>"
                "<p>This draft was created by the Google Workspace MCP Server.</p>"
                "<p>If you see this in your Gmail Drafts, the Gmail tool is working!</p>"
                "<br>"
                "<p><em>Sent at: test run</em></p>"
            ),
            is_draft=True,
        )
        print(f"  Status:   {result['status']}")
        print(f"  Draft ID: {result.get('draft_id')}")
        print(f"  Msg ID:   {result.get('message_id')}")
        print()
        print("  [OK] Check your Gmail Drafts folder!")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_google_docs(document_id):
    """Append test content to a Google Doc."""
    print()
    print("=" * 50)
    print("TEST 2: Google Docs — Append Content")
    print("=" * 50)

    try:
        result = append_content(
            document_id=document_id,
            content=(
                "\n\n## MCP Server Test\n"
                "This content was appended by the Google Workspace MCP Server.\n"
                "**Status:** Working!\n"
            ),
            format="markdown",
        )
        print(f"  Status:     {result['status']}")
        print(f"  Doc ID:     {result['document_id']}")
        print(f"  Chars added: {result['characters_added']}")
        print()
        print("  [OK] Check your Google Doc!")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


if __name__ == "__main__":
    print()
    
    # Test 1: Gmail
    gmail_ok = test_gmail_draft()
    
    # Test 2: Google Docs (optional — pass doc ID as argument)
    docs_ok = None
    if len(sys.argv) > 1:
        docs_ok = test_google_docs(sys.argv[1])
    else:
        print()
        print("=" * 50)
        print("TEST 2: Google Docs — SKIPPED")
        print("  Pass a document ID as argument to test:")
        print("  python smoke_test.py <DOCUMENT_ID>")
        print("=" * 50)

    print()
    print("-" * 50)
    print("RESULTS:")
    print(f"  Gmail:  {'PASS' if gmail_ok else 'FAIL'}")
    print(f"  Docs:   {'PASS' if docs_ok else 'SKIPPED' if docs_ok is None else 'FAIL'}")
    print("-" * 50)
