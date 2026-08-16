import os
from server.mcp_server import mcp
import server.tools.datetime
import server.tools.calendar
import server.tools.weather
import server.tools.email

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    mcp.run(transport="streamable-http")
