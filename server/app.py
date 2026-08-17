from server.mcp_server import mcp
import server.tools.datetime

import server.tools.calendar

import server.tools.weather
import server.tools.email
import server.tools.notetaker
import server.tools.meeting
import server.tools.test_calendar

if __name__ == "__main__":
    
    mcp.run(transport="streamable-http")
