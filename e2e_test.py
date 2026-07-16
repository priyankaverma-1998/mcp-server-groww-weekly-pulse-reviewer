"""End-to-end test: Append pulse to doc + draft email with doc link."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from tools.gmail_tool import send_email
from tools.google_docs_tool import append_content

doc_id = "1AirbbmJI986hgaxxCsSFZ9guhVkzLIExavs6Tm4t0XI"
doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

# Step 1: Append weekly pulse to the doc
print("Step 1: Appending weekly pulse to Google Doc...")
doc_result = append_content(
    document_id=doc_id,
    content=(
        "## Weekly Pulse - July 16, 2026\n\n"
        "### Top Themes\n"
        "1. **Onboarding** - Users struggle with KYC flow\n"
        "2. **Payments** - UPI timeout issues reported\n"
        "3. **Performance** - App feels sluggish on older devices\n\n"
        "### User Quotes\n"
        "- *KYC took forever, almost gave up*\n"
        "- *Payments fail during peak hours*\n"
        "- *Great app but needs speed improvements*\n\n"
        "### Action Items\n"
        "1. Simplify KYC to 3 steps\n"
        "2. Add UPI retry with exponential backoff\n"
        "3. Optimize image loading on low-end devices\n"
    ),
    format="markdown",
)
print(f"  [OK] Appended {doc_result['characters_added']} chars to doc")

# Step 2: Draft email WITH link to the doc
print()
print("Step 2: Creating draft email with doc link...")
email_result = send_email(
    to=["priyankaverma81298@gmail.com"],
    subject="Weekly Pulse - July 16, 2026",
    body=(
        f"<h2>Weekly Pulse Ready</h2>"
        f"<p>Hi team,</p>"
        f"<p>The latest weekly pulse has been published to the shared Google Doc.</p>"
        f"<p><strong>Key highlights:</strong></p>"
        f"<ul>"
        f"<li>Top theme: <strong>Onboarding friction</strong> - KYC flow needs simplification</li>"
        f"<li>Critical: UPI payment timeouts during peak hours</li>"
        f"<li>3 action items identified</li>"
        f"</ul>"
        f'<p>View the full pulse here: <a href="{doc_url}">Weekly Pulse Document</a></p>'
        f"<br>"
        f"<p>Best regards,<br>MCP Server</p>"
    ),
    is_draft=True,
)
print(f"  [OK] Draft created: {email_result['draft_id']}")

print()
print("=" * 50)
print("  END-TO-END TEST COMPLETE!")
print(f"  Doc:   {doc_url}")
print(f"  Email: Check Gmail Drafts")
print("=" * 50)
