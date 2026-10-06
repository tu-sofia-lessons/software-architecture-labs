"""Tiny JSON-over-HTTP kit (provided infrastructure — not the lesson).

Server:  serve(routes, port)  where routes = [(method, regex, handler), ...]
         handler(request) -> (status, dict)   request has .params, .body, .headers (lower-case keys)
Client:  get_json(url, timeout=None, headers=None) -> dict
         raises HttpError (4xx/5xx), ServiceTimeout, ServiceUnavailable
"""
import json
import re
import socket
import urllib.error
import urllib.request
from collections import namedtuple
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

Request = namedtuple("Request", "method path params body headers")


class ServiceUnavailable(Exception):
    """The remote service could not be reached (refused, reset, DNS...)."""


class ServiceTimeout(ServiceUnavailable):
    """The remote service did not answer within the timeout."""


class HttpError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


def get_json(url, timeout=None, headers=None):
    """GET a JSON document. timeout=None means: wait forever."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise HttpError(e.code, e.read().decode("utf-8", "replace")) from None
    except (socket.timeout, TimeoutError) as e:
        raise ServiceTimeout(f"{url} timed out after {timeout}s") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            raise ServiceTimeout(f"{url} timed out after {timeout}s") from e
        raise ServiceUnavailable(f"{url} unreachable: {e.reason}") from e
    except (ConnectionError, OSError) as e:
        raise ServiceUnavailable(f"{url} unreachable: {e}") from e


def serve(routes, port, host="127.0.0.1"):
    """Serve the given routes forever (one thread per request)."""
    compiled = [(m, re.compile(p), h) for m, p, h in routes]

    class Handler(BaseHTTPRequestHandler):
        def _dispatch(self, method):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw) if raw else None
            path = self.path.split("?")[0]
            for m, pattern, handler in compiled:
                match = pattern.fullmatch(path)   # the whole path must match, not a prefix
                if m == method and match:
                    headers = {k.lower(): v for k, v in self.headers.items()}
                    req = Request(method, path, match.groupdict(), body, headers)
                    try:
                        status, payload = handler(req)
                    except Exception as e:  # never leak a stack trace to the caller
                        status, payload = 500, {"error": f"{type(e).__name__}: {e}"}
                    return self._send(status, payload)
            self._send(404, {"error": f"no route for {method} {path}"})

        def _send(self, status, payload):
            data = json.dumps(payload).encode("utf-8")
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # the client gave up (e.g. timeout) — nothing to do

        def do_GET(self):
            self._dispatch("GET")

        def do_POST(self):
            self._dispatch("POST")

        def log_message(self, *args):
            pass  # keep the console quiet

    ThreadingHTTPServer.request_queue_size = 128   # many simultaneous clients in load tests
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    print(f"listening on http://{host}:{port}", flush=True)
    server.serve_forever()
