from datetime import datetime, timedelta

from server.mcp_server import mcp


@mcp.tool()
def get_current_datetime():
    """Get the current date and time."""

    now = datetime.utcnow() + timedelta(hours=5, minutes=30)

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A"),
        "timezone": "IST",
        "datetime": now.isoformat(),
    }