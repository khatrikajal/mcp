from server.mcp_server import mcp

from server.dependencies import (
    notetaker_service
)


@mcp.tool()
def join_meeting(
    meeting_url: str,
):
    """
    Join a Zoom, Google Meet, or Teams meeting with Nylas Notetaker.

    The notetaker will:
    1. Join the meeting
    2. Record the audio
    3. Transcribe the speech
    4. Generate AI meeting notes

    Returns the notetaker ID which can be used to check status and retrieve notes.
    """

    return notetaker_service.create_notetaker(
        meeting_url
    )


@mcp.tool()
def get_notetaker_status(
    notetaker_id: str,
):
    """
    Get the status of a notetaker session.

    Returns information about:
    - Current status (recording, transcribing, completed)
    - Meeting details
    - Recording progress
    """

    return notetaker_service.get_notetaker(
        notetaker_id
    )


@mcp.tool()
def list_notetakers(
    limit: int = 10,
):
    """
    List all notetaker sessions.
    """

    return notetaker_service.list_notetakers(
        limit=limit
    )


@mcp.tool()
def get_meeting_transcript(
    notetaker_id: str,
):
    """
    Get the full transcript of a meeting.

    This returns the complete transcription of the meeting audio,
    including speaker identification and timestamps.

    Note: Only available after the meeting has ended and transcription is complete.
    """

    return notetaker_service.get_transcript(
        notetaker_id
    )


@mcp.tool()
def get_meeting_summary(
    notetaker_id: str,
):
    """
    Get AI-generated meeting notes and summary.

    Returns structured meeting notes including:
    - Key discussion points
    - Action items
    - Decisions made
    - Executive summary

    Note: Only available after the meeting has ended and AI processing is complete.
    """

    return notetaker_service.get_summary(
        notetaker_id
    )