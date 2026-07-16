"""
Centralised Google API scopes for the MCP server.

All scopes used across tools are defined here as a single source of truth.
Adding a new Google Workspace integration? Add its scopes here.
"""

# Gmail scopes
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"

# Google Docs scopes
DOCS_SCOPE = "https://www.googleapis.com/auth/documents"

# Combined scopes — used during OAuth consent to request all permissions at once
ALL_SCOPES = [
    GMAIL_SEND_SCOPE,
    GMAIL_COMPOSE_SCOPE,
    DOCS_SCOPE,
]
