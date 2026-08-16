from server.mcp_server import mcp
from server.dependencies import email_service
import json

@mcp.tool()
def list_emails(limit: int = 10):
    """List the latest emails from the user's inbox."""

    result = email_service.list_emails(limit=limit)

    print("\n========== EMAIL TOOL RESULT ==========")
    print(result)
    print("=======================================\n")

    return json.dumps(
        result,
        indent=2)


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