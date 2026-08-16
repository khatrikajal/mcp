from nylas import Client

from server.config import (
    NYLAS_API_KEY,
    NYLAS_GRANT_ID,
)


class EmailService:

    def __init__(self):
        self.client = Client(
            NYLAS_API_KEY
        )

        self.grant_id = NYLAS_GRANT_ID

    def list_emails(self, limit: int = 10):

        response = self.client.messages.list(
            self.grant_id,
            query_params={
                "limit": limit,
            },
        )

        emails = []

        for message in response.data:

            sender_name = ""
            sender_email = ""

            if message.from_:

                sender = message.from_[0]

                if isinstance(sender, dict):

                    sender_name = sender.get(
                        "name",
                        ""
                    )

                    sender_email = sender.get(
                        "email",
                        ""
                    )

                else:

                    sender_name = getattr(
                        sender,
                        "name",
                        ""
                    )

                    sender_email = getattr(
                        sender,
                        "email",
                        ""
                    )

            emails.append({
                "id": message.id,
                "subject": message.subject or "",
                "from_name": sender_name,
                "from_email": sender_email,
                "date": message.date,
                "unread": message.unread,
                "snippet": getattr(
                    message,
                    "snippet",
                    "",
                ),
            })

        return emails

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ):

        response = self.client.messages.send(
            self.grant_id,
            request_body={
                "to": [
                    {
                        "email": to_email,
                    }
                ],
                "subject": subject,
                "body": body,
            },
        )

        message = response.data

        return {
            "success": True,
            "message_id": message.id,
            "subject": message.subject,
            "to": to_email,
        }