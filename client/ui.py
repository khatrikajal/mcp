import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from client.chat_service import chat

UI_FILE = Path(__file__).with_name("web") / "index.html"


class ChatHandler(BaseHTTPRequestHandler):
    def _send(self, status, content_type, body):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html", UI_FILE.read_text(encoding="utf-8"))
        else:
            self._send(404, "application/json", '{"error":"Not found"}')

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, "application/json", '{"error":"Not found"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length))
            history = data.get("history", [])
            if not history or history[-1].get("role") != "user":
                raise ValueError("A user message is required.")
            result = asyncio.run(chat(history))
            self._send(200, "application/json", json.dumps(result))
        except Exception as exc:
            self._send(500, "application/json", json.dumps({"error": str(exc)}))

    def log_message(self, format, *args):
        return


def main():
    port = int(os.getenv("PORT", 8080))
    address = ("0.0.0.0", port)   # bind 0.0.0.0 for Railway
    server = ThreadingHTTPServer(address, ChatHandler)
    print(f"Chat UI is running at http://0.0.0.0:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
