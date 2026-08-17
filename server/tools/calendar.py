from datetime import (
    datetime,
    timedelta,
)

from server.dependencies import (
    calendar_service,
)

from server.mcp_server import (
    mcp,
)


@mcp.tool()
def get_calendars():

    """
    List all calendars.
    """

    return (
        calendar_service.list_calendars()
    )


@mcp.tool()
def list_calendar_events(
    calendar_id: str = "",
    limit: int = 10,
):

    """
    List events from the calendar.
    """

    events = (
        calendar_service.list_events(
            calendar_id=(
                calendar_id
                or None
            ),
            limit=limit,
        )
    )

    return events


@mcp.tool()
def create_calendar_event(
    title: str,
    date: str,
    hour: int,
    description: str = "",
):

    """
    Create a calendar event.
    """

    start = datetime.strptime(
        f"{date} {hour}",
        "%Y-%m-%d %H",
    )

    end = (
        start
        + timedelta(hours=1)
    )

    return (
        calendar_service.create_event(
            title=title,
            start_time=int(
                start.timestamp()
            ),
            end_time=int(
                end.timestamp()
            ),
            description=description,
        )
    )