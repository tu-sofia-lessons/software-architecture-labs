"""Faculty IT's Course Materials File Server (provided — you don't change this; it is 'their' system).

API (v1):
    GET /courses/<id>/materials          -> 200 {"files": ["lecture01.txt", ...]}
    GET /courses/<id>/materials/<name>   -> 200 <bytes>   | 404
    PUT /courses/<id>/materials/<name>   -> 201           (body = file bytes)
API v2 (--v2):  GET /courses/<id>/materials -> {"files": [{"name": "...", "size": 123}, ...]}

Usage:
    python file_server.py [--port 8102] [--root server_files] [--delay SECONDS] [--v2]
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import argparse
import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LIST = re.compile(r"^/courses/(\d+)/materials$")
FILE = re.compile(r"^/courses/(\d+)/materials/([A-Za-z0-9_.\-]+)$")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    root = Path("server_files")
    delay = 0.0
    v2 = False

    def _send(self, status, body=b"", content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, course_id, name):
        if ".." in name:
            return None
        return self.root / f"course_{course_id}" / name

    def do_GET(self):
        time.sleep(self.delay)
        if m := LIST.match(self.path):
            folder = self.root / f"course_{m[1]}"
            files = sorted(p for p in folder.iterdir() if p.is_file()) if folder.exists() else []
            if self.v2:
                payload = {"files": [{"name": p.name, "size": p.stat().st_size} for p in files]}
            else:
                payload = {"files": [p.name for p in files]}
            return self._send(200, json.dumps(payload).encode())
        if (m := FILE.match(self.path)) and (path := self._file(m[1], m[2])) and path.is_file():
            return self._send(200, path.read_bytes(), "application/octet-stream")
        self._send(404, b'{"error": "not found"}')

    def do_PUT(self):
        time.sleep(self.delay)
        m = FILE.match(self.path)
        path = self._file(m[1], m[2]) if m else None
        if path is None:
            return self._send(400, b'{"error": "bad path"}')
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self._send(201, b'{"stored": true}')

    def log_message(self, fmt, *args):
        print(f"[file-server] {self.command} {self.path}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8102)
    parser.add_argument("--root", default=str(Path(__file__).parent / "server_files"))
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--v2", action="store_true")
    args = parser.parse_args()
    Handler.root, Handler.delay, Handler.v2 = Path(args.root), args.delay, args.v2
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"File server on http://127.0.0.1:{args.port}  root={args.root}  "
          f"api={'v2' if args.v2 else 'v1'}  delay={args.delay}s", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
