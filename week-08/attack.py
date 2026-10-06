"""Scripted attacks + legitimate requests against the running API (provided).

Usage:  python api.py   (in one terminal)
        python attack.py
Every ATTACK should end DENIED (401/403); every LEGIT request should end ALLOWED.
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import base64
import json

import config
from client import call, login_headers


def tampered(headers):
    """Keep the signature, but rewrite the payload to claim role=admin."""
    token = headers["Authorization"].split(" ", 1)[1]
    payload, signature = token.split(".")
    data = json.loads(base64.urlsafe_b64decode(payload))
    data["role"] = "admin"
    forged = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    return {"Authorization": f"Bearer {forged}.{signature}", "X-User": data["user"]}


def cases(secret):
    """(id, kind, description, method, path, headers, body) for every scripted request."""
    as_ = lambda user, ttl=3600: login_headers(user, secret, ttl)  # noqa: E731
    return [
        ("A1", "attack", "forged X-User: registrar, no token", "GET", "/students/2/grades", {"X-User": "registrar"}, None),
        ("A2", "attack", "maria's token edited to role=admin", "GET", "/students/2/grades", tampered(as_("maria")), None),
        ("A3", "attack", "maria reads Ivan's grades", "GET", "/students/2/grades", as_("maria"), None),
        ("A4", "attack", "maria gives herself a 6.00", "POST", "/grades", as_("maria"), {"student_id": 1, "course_id": 1, "grade": 6.0}),
        ("A5", "attack", "prof.stoyanova grades AI201 (not her course)", "POST", "/grades", as_("prof.stoyanova"), {"student_id": 2, "course_id": 2, "grade": 6.0}),
        ("A6", "attack", "expired token", "GET", "/students/1/grades", as_("maria", ttl=-60), None),
        ("A7", "attack", "maria enrolls Ivan in Databases", "POST", "/enrollments", as_("maria"), {"student_id": 2, "course_id": 3}),
        ("A8", "attack", "registrar grades Ivan in AI201 (the Registrar does not grade)", "POST", "/grades", as_("registrar"), {"student_id": 2, "course_id": 2, "grade": 6.0}),
        ("A9", "attack", "prof.stoyanova reads maria's transcript", "GET", "/students/1/grades", as_("prof.stoyanova"), None),
        ("A10", "attack", "maria opens the SA101 gradebook", "GET", "/courses/1/grades", as_("maria"), None),
        ("L1", "legit", "maria reads her own grades", "GET", "/students/1/grades", as_("maria"), None),
        ("L2", "legit", "prof.stoyanova grades Ivan in SA101", "POST", "/grades", as_("prof.stoyanova"), {"student_id": 2, "course_id": 1, "grade": 5.0}),
        ("L3", "legit", "prof.stoyanova opens the SA101 gradebook", "GET", "/courses/1/grades", as_("prof.stoyanova"), None),
        ("L4", "legit", "registrar enrolls Georgi in Databases", "POST", "/enrollments", as_("registrar"), {"student_id": 3, "course_id": 3}),
        ("L5", "legit", "maria enrolls herself in Databases", "POST", "/enrollments", as_("maria"), {"student_id": 1, "course_id": 3}),
    ]


def run_all(secret, base_url=None):
    """Send every case. Returns a list of (id, kind, description, status, outcome)."""
    results = []
    for cid, kind, text, method, path, headers, body in cases(secret):
        kwargs = {"base_url": base_url} if base_url else {}
        status, _ = call(method, path, headers, body, **kwargs)
        outcome = "DENIED" if status in (401, 403) else "ALLOWED"
        results.append((cid, kind, text, status, outcome))
    return results


if __name__ == "__main__":
    for cid, kind, text, status, outcome in run_all(config.secret()):
        expected = "DENIED" if kind == "attack" else "ALLOWED"
        mark = "ok " if outcome == expected else "!! "
        print(f"{mark}{cid} {kind:<6} {outcome:<7} ({status})  {text}")
