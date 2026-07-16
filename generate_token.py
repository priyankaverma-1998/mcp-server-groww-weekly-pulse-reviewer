"""
Generate token.json by running the Google OAuth 2.0 consent flow.

This script starts a local server, prints the auth URL for you to open
in your browser, and saves the resulting token to token.json.

Usage:
    python generate_token.py
"""

import sys
import os

# IMPORTANT: Must be set BEFORE importing oauthlib/google_auth_oauthlib
# This allows the token to be accepted even if Google grants fewer
# scopes than requested (e.g., Gmail API not yet enabled).
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
from config.scopes import ALL_SCOPES

load_dotenv()

CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "./token.json")


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ credentials.json not found at: {os.path.abspath(CREDENTIALS_PATH)}")
        print("   Download it from Google Cloud Console > APIs & Services > Credentials")
        sys.exit(1)

    print("=" * 60)
    print("  Google OAuth 2.0 - Token Generator")
    print("=" * 60)
    print()
    print("Requesting scopes:")
    for scope in ALL_SCOPES:
        print(f"  - {scope}")
    print()
    print("Starting local auth server on port 8090...")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH, ALL_SCOPES
    )

    # Force re-consent to ensure ALL scopes are granted
    # (including Gmail scopes that may have been skipped before)
    creds = flow.run_local_server(
        port=8090,
        open_browser=False,
        prompt="consent",
        success_message="Authentication successful! You can close this tab.",
    )

    # Save the token
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    # Check which scopes were actually granted
    granted_scopes = creds.scopes or []
    requested_scopes = set(ALL_SCOPES)
    granted_set = set(granted_scopes)
    missing_scopes = requested_scopes - granted_set

    print()
    print("=" * 60)
    print("  SUCCESS! Authentication complete.")
    print(f"  Token saved to: {os.path.abspath(TOKEN_PATH)}")
    print()
    print("  Scopes granted:")
    for scope in granted_scopes:
        print(f"    [OK] {scope}")

    if missing_scopes:
        print()
        print("  WARNING - Missing scopes (API may not be enabled):")
        for scope in missing_scopes:
            print(f"    [MISSING] {scope}")
        print()
        print("  To fix: Go to Google Cloud Console > APIs & Services > Library")
        print("  and enable the missing APIs, then re-run this script.")

    print("=" * 60)


if __name__ == "__main__":
    main()
