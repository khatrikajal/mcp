import os
from mcp.server.fastmcp import FastMCP

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

mcp = FastMCP(
    "MCP Assistant Server",
    host=HOST,
    port=PORT,
)
