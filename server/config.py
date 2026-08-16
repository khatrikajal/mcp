from dotenv import load_dotenv
import os 

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")

PORT = int(os.getenv("PORT", 8000))

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NYLAS_API_KEY = os.getenv("NYLAS_API_KEY")
NYLAS_GRANT_ID = os.getenv("NYLAS_GRANT_ID")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
