from mcp.server.fastmcp import FastMCP

from server.config import HOST, PORT


mcp = FastMCP(
    "Nylas MCP Server - Calendar, Email & Meeting Notetaker",
    host=HOST,
    port=PORT,
)
