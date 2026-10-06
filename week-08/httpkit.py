"""Tiny JSON-over-HTTP server helper (provided — plumbing, not the lesson)."""
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HttpError(Exception):
    """Raise from a handler to return an error status with a JSON message."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class Request:
    def __init__(self, method, path, headers, body, params):
        self.method = method
        self.path = path
        self.headers = headers          # case-insensitive mapping
        self.body = body                # parsed JSON (dict) or None
        self.params = params            # values captured from the route pattern


def serve(routes, port, host="127.0.0.1"):
    """routes: list of (METHOD, regex, handler). handler(request) -> (status, dict)."""
    compiled = [(m, re.compile(f"^{p}$"), h) for m, p, h in routes]

    class Handler(BaseHTTPRequestHandler):
        def _dispatch(self, method):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw) if raw else None
                for m, pattern, handler in compiled:
                    match = pattern.match(self.path)
                    if m == method and match:
                        status, payload = handler(Request(method, self.path, self.headers, body, match.groups()))
                        break
                else:
                    status, payload = 404, {"error": "no such endpoint"}
            except HttpError as e:
                status, payload = e.status, {"error": e.message}
            except json.JSONDecodeError:
                status, payload = 400, {"error": "body must be JSON"}
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self._dispatch("GET")

        def do_POST(self):
            self._dispatch("POST")

        def log_message(self, fmt, *args):       # one short line per request
            print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
