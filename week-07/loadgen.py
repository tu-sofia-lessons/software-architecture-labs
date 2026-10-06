"""Load generator (provided): many users validate a course at the same time.

    python loadgen.py [--users 50] [--naive] [--url http://127.0.0.1:8101]

Each user performs ONE operation: catalog.get_course(1) — what every enrollment does.
--naive uses a textbook-bad client (timeout 1 s, 5 retries, no backoff) instead of yours.
Start the service yourself first, e.g.  python catalog_service/run.py --delay 1.5
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import argparse
import os
import statistics
import threading
import time

import obs
from catalog.client import CatalogClient
from httpkit import HttpError, ServiceUnavailable, get_json


class NaiveCatalogClient:
    """Retries everything, immediately, with a timeout shorter than the service's latency."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def get_course(self, course_id):
        for attempt in range(6):
            try:
                return get_json(f"{self.base_url}/courses/{course_id}", timeout=1.0)
            except (ServiceUnavailable, HttpError):
                if attempt == 5:
                    raise


def run(users=50, naive=False, url="http://127.0.0.1:8101"):
    """Run the load; returns a summary dict."""
    calls_before = get_json(f"{url}/stats", timeout=5)["calls"]
    results = []
    lock = threading.Lock()

    def one_user():
        client = NaiveCatalogClient(url) if naive else CatalogClient(url)
        start = time.monotonic()
        try:
            client.get_course(1)
            ok = True
        except Exception:
            ok = False
        with lock:
            results.append((ok, time.monotonic() - start))

    threads = [threading.Thread(target=one_user) for _ in range(users)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    time.sleep(0.2)
    calls = get_json(f"{url}/stats", timeout=10)["calls"] - calls_before
    latencies = sorted(lat for _, lat in results)
    return {
        "ops": users,
        "ok": sum(1 for ok, _ in results if ok),
        "p50_s": round(statistics.median(latencies), 2),
        "p95_s": round(latencies[int(0.95 * (len(latencies) - 1))], 2),
        "service_calls": calls,
        "calls_per_op": round(calls / users, 2),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=50)
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--url", default="http://127.0.0.1:8101")
    a = ap.parse_args()
    obs.LOG_PATH = obs.LOG_PATH or os.devnull     # keep the console readable; set OBS_LOG to keep logs
    summary = run(a.users, a.naive, a.url)
    print(("NAIVE client" if a.naive else "YOUR client") + ": " +
          "  ".join(f"{k}={v}" for k, v in summary.items()))
