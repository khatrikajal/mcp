from nylas import Client

from server.config import NYLAS_API_KEY, NYLAS_GRANT_ID


print("API key loaded:", bool(NYLAS_API_KEY))
print("Grant ID loaded:", bool(NYLAS_GRANT_ID))

try:
    client = Client(
        NYLAS_API_KEY
    )

    print("Nylas client created")

    response = client.messages.list(
        NYLAS_GRANT_ID,
        query_params={
            "limit": 5,
        },
    )

    print("Nylas request successful")
    print("Response:", response)

    print("\nEmails:")

    for message in response.data:
        print("-" * 50)
        print("ID:", message.id)
        print("Subject:", message.subject)
        print("From:", message.from_)
        print("Date:", message.date)

except Exception as e:
    print("\n========== REAL ERROR ==========")
    print("Type:", type(e).__name__)
    print("Error:", str(e))
    print("================================")
    raise