"""
client/ui.py  –  Enhanced MCP Chat UI server
  • /api/health            – connection health check
  • /api/tools             – list all registered MCP tools
  • /api/chat              – chat with active_tools filtering
  • /api/confirm-action    – execute a previously-proposed sensitive action
                              (send_email / create_calendar_event) after the
                              user has explicitly confirmed it in the UI
  • Serves the professional frontend from client/web/index.html
"""

import asyncio
import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from client.chat_service import chat, confirm_action

UI_FILE = Path(__file__).with_name("web") / "index.html"


class ChatHandler(BaseHTTPRequestHandler):

    # ── utilities ──────────────────────────────────────────────
    def _send(self, status: int, content_type: str, body: str):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data):
        self._send(status, "application/json", json.dumps(data))

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw) if raw else {}

    # ── routing ────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                html = UI_FILE.read_text(encoding="utf-8")
                self._send(200, "text/html", html)
            except FileNotFoundError:
                self._json(404, {"error": "UI file not found"})

        elif self.path == "/api/health":
            self._json(200, {"status": "ok", "server": "MCP Platform"})

        elif self.path == "/api/tools":
            # Return the list of all registered tools from the MCP server
            try:
                result = asyncio.run(_list_tools())
                self._json(200, result)
            except Exception as exc:
                traceback.print_exc()
                self._json(500, {"error": str(exc)})

        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/api/chat":
            self._handle_chat()
        elif self.path == "/api/confirm-action":
            self._handle_confirm_action()
        else:
            self._json(404, {"error": "Not found"})

    def _handle_chat(self):
        try:
            data = self._read_body()
            history = data.get("history", [])
            active_tools = data.get("active_tools", None)  # list of tool IDs or None = all

            if not history or history[-1].get("role") != "user":
                raise ValueError("A user message is required.")

            result = asyncio.run(chat(history, active_tools=active_tools))
            self._json(200, result)

        except Exception as exc:
            traceback.print_exc()
            self._json(500, {"error": str(exc)})

    def _handle_confirm_action(self):
        """
        Body: {"tool": "send_email", "arguments": {...}}
        This is the ONLY route that actually executes a sensitive action.
        The tool/arguments pair must be exactly what chat() previously
        returned in `pending_action` — the frontend should not let the user
        free-edit these into something arbitrary without re-confirming, but
        even if it did, confirm_action() re-validates the tool exists before
        calling it.
        """
        try:
            data = self._read_body()
            tool_name = data.get("tool")
            arguments = data.get("arguments", {})

            if not tool_name:
                raise ValueError("A 'tool' name is required.")

            result = asyncio.run(confirm_action(tool_name, arguments))
            status = 200 if result.get("success") else 400
            self._json(status, result)

        except Exception as exc:
            traceback.print_exc()
            self._json(500, {"error": str(exc)})

    def log_message(self, format, *args):  # suppress default logging
        return


# ── helper: list tools from MCP server ────────────────────────
async def _list_tools():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    from client.config import MCP_SERVER_URL

    tools = []
    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (r, w, _):
            async with ClientSession(r, w) as session:
                await session.initialize()
                available = await session.list_tools()
                for t in available.tools:
                    tools.append({
                        "name": t.name,
                        "description": t.description or "",
                        "schema": t.inputSchema,
                    })
    except Exception:
        pass
    return {"tools": tools}


# ── entrypoint ────────────────────────────────────────────────
def main():
    address = ("127.0.0.1", 8080)
    server = ThreadingHTTPServer(address, ChatHandler)
    print("=" * 52)
    print("  MCP Platform  →  http://localhost:8080")
    print("=" * 52)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()