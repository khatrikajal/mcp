from mcp.server.fastmcp import FastMCP

from backend.src.core.config import HOST, PORT


mcp = FastMCP(
    "Nylas MCP Server - Calendar, Email & Meeting Notetaker",
    host=HOST,
    port=PORT,
)
