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

        self.grant_id = (
            NYLAS_GRANT_ID
        )

    def list_calendars(self):

        response = (
            self.client.calendars.list(
                self.grant_id
            )
        )

        return [
            {
                "id": calendar.id,
                "name": calendar.name,
                "description": (
                    calendar.description
                ),
                "is_primary": (
                    calendar.is_primary
                ),
            }
            for calendar in response.data
        ]

    def get_default_calendar_id(
        self,
    ):

        calendars = (
            self.list_calendars()
        )

        if not calendars:

            raise Exception(
                "No calendars found."
            )

        for calendar in calendars:

            if calendar.get(
                "is_primary"
            ):

                return calendar["id"]

        return calendars[0]["id"]

    def list_events(
        self,
        calendar_id=None,
        limit=10,
    ):

        if calendar_id is None:

            calendar_id = (
                self.get_default_calendar_id()
            )

        response = (
            self.client.events.list(
                self.grant_id,
                query_params={
                    "calendar_id": (
                        calendar_id
                    ),
                    "limit": limit,
                },
            )
        )

        return [
            {
                "id": event.id,
                "title": event.title,
                "description": (
                    event.description
                ),
                "location": (
                    event.location
                ),
                "when": event.when,
                "conferencing": getattr(
                    event,
                    "conferencing",
                    None,
                ),
            }
            for event in response.data
        ]

    def create_event(
        self,
        title,
        start_time,
        end_time,
        description="",
    ):

        calendar_id = (
            self.get_default_calendar_id()
        )

        response = (
            self.client.events.create(
                self.grant_id,
                request_body={
                    "title": title,
                    "description": (
                        description
                    ),
                    "when": {
                        "start_time": (
                            start_time
                        ),
                        "end_time": (
                            end_time
                        ),
                    },
                    "conferencing": {
                        "provider": (
                            "Google Meet"
                        ),
                        "autocreate": {},
                    },
                },
                query_params={
                    "calendar_id": (
                        calendar_id
                    ),
                },
            )
        )

        event = response.data

        return {
            "success": True,
            "event_id": event.id,
            "title": event.title,
            "when": event.when,
            "conferencing": getattr(
                event,
                "conferencing",
                None,
            ),
        }