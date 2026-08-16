from server.mcp_server import mcp

from server.dependencies import calendar_service


@mcp.tool()
def list_calendar_events(
    calendar_id: str = "primary",
    limit: int = 10,
):
    """List events from the user's calendar."""

    return calendar_service.list_events(
        calendar_id=calendar_id,
        limit=limit,
    )


@mcp.tool()
def create_calendar_event(
    title: str,
    start_time: int,
    end_time: int,
    description: str = "",
    location: str = "",
):
    """Create a calendar event with a title, start time, and end time."""

    return calendar_service.create_event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
    )