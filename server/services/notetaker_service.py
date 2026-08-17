import requests

from server.config import (
    NYLAS_API_KEY,
    NYLAS_GRANT_ID,
)


class NotetakerService:

    def __init__(self):
        self.api_key = NYLAS_API_KEY
        self.grant_id = NYLAS_GRANT_ID
        self.base_url = "https://api.us.nylas.com"

    def create_notetaker(
        self,
        meeting_url: str,
    ) -> dict:
        """
        Send a Nylas Notetaker bot to the given meeting URL.

        The Nylas Python SDK v6 has a bug where notetakers.create(grant_id, body)
        concatenates grant_id directly onto the hostname string instead of the
        URL path, producing host='api.us.nylas.com<grant_id>' and a DNS failure.
        We call the REST API directly with requests to avoid this entirely.
        """
        url = (
            f"{self.base_url}"
            f"/v3/grants/{self.grant_id}/notetakers"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "meeting_link": meeting_url,
        }

        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            # Nylas wraps the result in a "data" key
            return data.get("data", data)

        except requests.HTTPError as exc:
            try:
                error_body = exc.response.json()
                msg = (
                    error_body.get("message")
                    or error_body.get("error")
                    or exc.response.text
                )
            except Exception:
                msg = exc.response.text

            raise RuntimeError(
                f"Nylas API error {exc.response.status_code}: {msg}"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error contacting Nylas: {exc}"
            ) from exc

    def get_notetaker(
        self,
        notetaker_id: str,
    ) -> dict:
        """
        Get the status and details of a specific notetaker.

        Returns information about the notetaker including:
        - status (e.g., "recording", "transcribing", "completed")
        - meeting details
        - recording status
        """
        url = (
            f"{self.base_url}"
            f"/v3/grants/{self.grant_id}/notetakers/{notetaker_id}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", data)

        except requests.HTTPError as exc:
            try:
                error_body = exc.response.json()
                msg = (
                    error_body.get("message")
                    or error_body.get("error")
                    or exc.response.text
                )
            except Exception:
                msg = exc.response.text

            raise RuntimeError(
                f"Nylas API error {exc.response.status_code}: {msg}"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error contacting Nylas: {exc}"
            ) from exc

    def list_notetakers(
        self,
        limit: int = 10,
    ) -> list:
        """
        List all notetakers for this grant.
        """
        url = (
            f"{self.base_url}"
            f"/v3/grants/{self.grant_id}/notetakers"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        params = {
            "limit": limit,
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])

        except requests.HTTPError as exc:
            try:
                error_body = exc.response.json()
                msg = (
                    error_body.get("message")
                    or error_body.get("error")
                    or exc.response.text
                )
            except Exception:
                msg = exc.response.text

            raise RuntimeError(
                f"Nylas API error {exc.response.status_code}: {msg}"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error contacting Nylas: {exc}"
            ) from exc

    def get_transcript(
        self,
        notetaker_id: str,
    ) -> dict:
        """
        Get the transcript for a completed notetaker session.

        Returns the full transcript of the meeting.
        """
        url = (
            f"{self.base_url}"
            f"/v3/grants/{self.grant_id}/notetakers/{notetaker_id}/transcript"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", data)

        except requests.HTTPError as exc:
            try:
                error_body = exc.response.json()
                msg = (
                    error_body.get("message")
                    or error_body.get("error")
                    or exc.response.text
                )
            except Exception:
                msg = exc.response.text

            raise RuntimeError(
                f"Nylas API error {exc.response.status_code}: {msg}"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error contacting Nylas: {exc}"
            ) from exc

    def get_summary(
        self,
        notetaker_id: str,
    ) -> dict:
        """
        Get the AI-generated summary and notes for a completed notetaker session.

        Returns structured meeting notes including:
        - Key discussion points
        - Action items
        - Decisions made
        - Summary
        """
        url = (
            f"{self.base_url}"
            f"/v3/grants/{self.grant_id}/notetakers/{notetaker_id}/summary"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", data)

        except requests.HTTPError as exc:
            try:
                error_body = exc.response.json()
                msg = (
                    error_body.get("message")
                    or error_body.get("error")
                    or exc.response.text
                )
            except Exception:
                msg = exc.response.text

            raise RuntimeError(
                f"Nylas API error {exc.response.status_code}: {msg}"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Network error contacting Nylas: {exc}"
            ) from exc