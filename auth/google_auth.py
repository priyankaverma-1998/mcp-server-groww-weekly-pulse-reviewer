"""
Google OAuth 2.0 authentication helper for the MCP server.

Handles the full OAuth lifecycle:
  1. First run  → Opens browser for user consent, saves token.json
  2. Later runs → Loads token.json, auto-refreshes if expired

Usage:
    from auth.google_auth import get_google_credentials, get_gmail_service, get_docs_service

    creds = get_google_credentials()
    gmail = get_gmail_service()
    docs  = get_docs_service()
"""

import os
import sys
import json
import logging

# Accept partial scope grants (e.g., if Gmail API is not yet enabled)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Add project root to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.scopes import ALL_SCOPES

# Load environment variables from .env file (if present)
load_dotenv()

logger = logging.getLogger(__name__)

# Default paths (overridable via environment variables)
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "./token.json")


def get_google_credentials() -> Credentials:
    """
    Obtain valid Google OAuth 2.0 credentials.

    Credential loading priority:
      1. GOOGLE_TOKEN_JSON env var (for serverless deployment, e.g. Vercel)
      2. token.json file on disk (for local development)
      3. Full OAuth browser flow (first-run only, local dev)

    Returns:
        google.oauth2.credentials.Credentials: Valid credentials object.

    Raises:
        FileNotFoundError: If credentials.json is not found at CREDENTIALS_PATH.
        Exception: If the OAuth flow fails or the user denies consent.
    """
    creds = None

    # Priority 1: Load from GOOGLE_TOKEN_JSON env var (Vercel / serverless)
    token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json_str:
        try:
            token_data = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(token_data, ALL_SCOPES)
            logger.info("Loaded token from GOOGLE_TOKEN_JSON env var")
        except Exception as e:
            logger.warning("Failed to load token from GOOGLE_TOKEN_JSON env var: %s", e)
            creds = None

    # Priority 2: Load from token file on disk (local dev)
    if not creds and os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, ALL_SCOPES)
            logger.info("Loaded existing token from %s", TOKEN_PATH)
        except Exception as e:
            logger.warning("Failed to load existing token: %s", e)
            creds = None

    # If no valid credentials, refresh or run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed expired token successfully")
            except Exception as e:
                logger.warning("Token refresh failed: %s. Re-running OAuth flow.", e)
                creds = None

        if not creds:
            # Run full OAuth flow — requires credentials.json
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Google OAuth credentials file not found at '{CREDENTIALS_PATH}'. "
                    f"Download it from Google Cloud Console > APIs & Services > Credentials "
                    f"and place it at this path (or set GOOGLE_CREDENTIALS_PATH env var)."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, ALL_SCOPES
            )
            creds = flow.run_local_server(port=0)
            logger.info("OAuth flow completed successfully")

        # Save the token for future runs
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
            logger.info("Token saved to %s", TOKEN_PATH)

    return creds


def get_gmail_service():
    """
    Build and return an authenticated Gmail API service client.

    Returns:
        googleapiclient.discovery.Resource: Gmail API service instance.
    """
    creds = get_google_credentials()
    service = build("gmail", "v1", credentials=creds)
    logger.info("Gmail service built successfully")
    return service


def get_docs_service():
    """
    Build and return an authenticated Google Docs API service client.

    Returns:
        googleapiclient.discovery.Resource: Google Docs API service instance.
    """
    creds = get_google_credentials()
    service = build("docs", "v1", credentials=creds)
    logger.info("Google Docs service built successfully")
    return service
