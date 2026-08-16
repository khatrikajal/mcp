from nylas import Client

from server.config import (
    NYLAS_API_KEY,
    NYLAS_GRANT_ID,
)


class CalendarService:

    def __init__(self):
        self.client = Client(
            NYLAS_API_KEY
        )

        self.grant_id = NYLAS_GRANT_ID

    def list_calendars(self):

        response = self.client.calendars.list(
            self.grant_id
        )

        return [
            {
                "id": calendar.id,
                "name": calendar.name,
                "description": calendar.description,
                "is_primary": calendar.is_primary,
                "timezone": calendar.timezone,
                "read_only": calendar.read_only,
            }
            for calendar in response.data
        ]

    def list_events(
        self,
        calendar_id="primary",
        limit=10,
    ):

        response = self.client.events.list(
            self.grant_id,
            query_params={
                "calendar_id": calendar_id,
                "limit": limit,
            },
        )

        return [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "location": event.location,
                "when": event.when,
            }
            for event in response.data
        ]

    def create_event(
        self,
        title: str,
        start_time: int,
        end_time: int,
        description: str = "",
        location: str = "",
    ):

        response = self.client.events.create(
            self.grant_id,
            request_body={
                "title": title,
                "description": description,
                "when": {
                    "start_time": start_time,
                    "end_time": end_time,
                },
                "location": location,
            },
            query_params={
                "calendar_id": "primary",
            },
        )

        event = response.data

        return {
            "success": True,
            "event_id": event.id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "when": event.when,
            "calendar_id": event.calendar_id,
        }