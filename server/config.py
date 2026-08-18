from dotenv import load_dotenv
import os 

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")

PORT = int(os.getenv("PORT", 8000))

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NYLAS_API_KEY = os.getenv("NYLAS_API_KEY")
NYLAS_GRANT_ID = os.getenv("NYLAS_GRANT_ID")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mcp_platform.db")

# JWT Authentication
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# API Configuration
API_PORT = int(os.getenv("API_PORT", 8001))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
