import os
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from server.mcp_server import mcp

import server.tools.datetime
import server.tools.calendar
import server.tools.weather
import server.tools.email


async def health(request: Request):
    return JSONResponse(
        {"status": "ok", "service": "MCP Assistant Server"}
    )


# Move these outside __main__
mcp_app = mcp.streamable_http_app()

app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/", app=mcp_app),
    ],
)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
