from server.mcp_server import mcp
from server.dependencies import email_service
import json

from server.mcp_server import mcp
from server.dependencies import email_service


@mcp.tool()
def list_emails(limit: int = 5):
    """List the latest emails from the user's inbox."""

    emails = email_service.list_emails(limit=limit)

    print("\n========== EMAIL TOOL RESULT ==========")
    print(emails)
    print("=======================================\n")

    return {
        "count": len(emails),
        "emails": emails,
    }

@mcp.tool()
def analyze_emails(limit: int = 5):
    """Analyze the latest emails."""

    emails = email_service.list_emails(limit=limit)

    analysis = []

    for email in emails:

        category = "General"

        sender = email["from_name"].lower()
        subject = email["subject"].lower()

        if "security" in subject:
            category = "Security"

        elif "google" in sender:
            category = "Google"

        elif "groq" in sender:
            category = "AI"

        elif "kaggle" in sender:
            category = "Machine Learning"

        analysis.append(
            {
                "sender": email["from_name"],
                "subject": email["subject"],
                "category": category,
                "unread": email["unread"],
                "summary": email["snippet"],
            }
        )

    return analysis

@mcp.tool()
def send_email(
    to_email: str,
    subject: str,
    body: str,
):
    """Send an email to a recipient."""

    return email_service.send_email(
        to_email=to_email,
        subject=subject,
        body=body,
    )