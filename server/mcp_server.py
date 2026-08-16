import os
from mcp.server.fastmcp import FastMCP

# Railway injects PORT automatically; we must bind 0.0.0.0 for external traffic
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

mcp = FastMCP(
    "MCP Assistant Server",
    host=HOST,        # MUST be 0.0.0.0, not 127.0.0.1
    port=PORT,
)
