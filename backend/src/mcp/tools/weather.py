from backend.src.mcp.mcp_server import mcp

from backend.src.core.dependencies import weather_service

@mcp.tool()
def get_weather(city:str):
    """Get the current live weather and temperature for a city."""
    
    return weather_service.get_weather(city)

