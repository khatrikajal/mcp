from server.dependencies import (
    meeting_service,
)

from server.mcp_server import (
    mcp,
)


@mcp.tool()
def join_next_meeting():

    """
    Join the next scheduled meeting.
    """

    return (
        meeting_service.join_next_meeting()
    )