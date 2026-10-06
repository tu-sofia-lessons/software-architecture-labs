"""Catalogue Service with chaos flags (provided).

    python catalog_service/run.py [--port 8101] [--delay SECONDS] [--fail-rate 0.0-1.0] [--seed N]

--delay      every course request sleeps this long before answering (a slow service)
--fail-rate  this fraction of course requests answer 500 immediately (a flaky service)
GET /stats   -> {"calls": n}  how many course requests reached the service
Every request is logged with its X-Request-Id (see obs.py).
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import argparse
import random
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))   # httpkit, obs
sys.path.insert(0, str(Path(__file__).parent))

import httpkit  # noqa: E402
import obs  # noqa: E402
from db import connect  # noqa: E402
from repository import CatalogRepository  # noqa: E402

STATS = {"calls": 0}
_lock = threading.Lock()


def list_courses(request):
    return 200, {"courses": CatalogRepository(connect()).list_all()}


def get_course(request):
    course = CatalogRepository(connect()).get(int(request.params["id"]))
    return (200, course) if course else (404, {"error": "course not found"})


def with_chaos(handler, delay, fail_rate, rng):
    """Wrap a route: count it, maybe fail it, maybe slow it down, log it."""
    def wrapped(request):
        start = time.monotonic()
        with _lock:
            STATS["calls"] += 1
            fail = rng.random() < fail_rate
        if fail:
            status, body = 500, {"error": "injected failure"}
        else:
            time.sleep(delay)
            status, body = handler(request)
        obs.log("served", service="catalog", request_id=request.headers.get("x-request-id", "-"),
                path=request.path, status=status, latency_ms=round((time.monotonic() - start) * 1000))
        return status, body
    return wrapped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8101)
    ap.add_argument("--delay", type=float, default=0.0)
    ap.add_argument("--fail-rate", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    routes = [
        ("GET", r"^/courses$", with_chaos(list_courses, a.delay, a.fail_rate, rng)),
        ("GET", r"^/courses/(?P<id>\d+)$", with_chaos(get_course, a.delay, a.fail_rate, rng)),
        ("GET", r"^/stats$", lambda request: (200, dict(STATS))),
    ]
    print(f"Catalogue Service delay={a.delay}s fail-rate={a.fail_rate}", flush=True)
    httpkit.serve(routes, a.port)


if __name__ == "__main__":
    main()
