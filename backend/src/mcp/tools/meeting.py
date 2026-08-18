from backend.src.core.dependencies import (
    meeting_service,
)

from backend.src.mcp.mcp_server import (
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