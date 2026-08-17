from server.mcp_server import mcp
from server.dependencies import calendar_service


@mcp.tool()
def get_calendars():

    return calendar_service.list_calendars()