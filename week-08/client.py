"""Simulates the mobile app / admin tool: logs in as a user and calls the API (provided).

Usage:
    python client.py maria GET /students/1/grades
    python client.py prof.stoyanova POST /grades '{"student_id": 2, "course_id": 1, "grade": 5.5}'

The new app version sends BOTH the old X-User header and a login token (Authorization: Bearer ...).
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import json
import urllib.error
import urllib.request

import config
import identity

BASE_URL = f"http://127.0.0.1:{config.PORT}"


def call(method, path, headers=None, body=None, base_url=BASE_URL):
    """Send one request. Returns (status, parsed JSON body)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(base_url + path, data=data, method=method, headers=headers or {})
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def login_headers(user, secret, ttl_seconds=3600):
    token = identity.issue_token(user, secret, ttl_seconds)
    return {"Authorization": f"Bearer {token}", "X-User": user}


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    user, method, path = sys.argv[1:4]
    body = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
    status, payload = call(method, path, login_headers(user, config.secret()), body)
    print(status, json.dumps(payload, indent=2))
