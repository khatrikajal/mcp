from backend.src.mcp.mcp_server import mcp
from backend.src.core.dependencies import calendar_service


@mcp.tool()
def get_calendars():

    return calendar_service.list_calendars()