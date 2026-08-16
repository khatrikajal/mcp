from datetime import datetime
from zoneinfo import ZoneInfo

from server.mcp_server import mcp


@mcp.tool()
def get_current_datetime():
    """Get the current date and time in India Standard Time."""

    now = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A"),
        "timezone": "Asia/Kolkata",
        "datetime": now.isoformat(),
    }