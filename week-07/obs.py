"""Observability helpers (provided): request ids and one-line JSON logs.

    rid = new_request_id()
    log("catalog_call", request_id=rid, op="get_course", attempt=1, latency_ms=12, outcome="ok")

Logs go to the file in OBS_LOG (env var or obs.LOG_PATH), otherwise to stderr.
"""
import json
import os
import sys
import threading
import time
import uuid

LOG_PATH = os.environ.get("OBS_LOG")
_lock = threading.Lock()


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def log(event, **fields):
    line = json.dumps({"ts": round(time.time(), 3), "event": event, **fields})
    with _lock:
        if LOG_PATH:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        else:
            print(line, file=sys.stderr)


def read(path):
    """Read a log file back as a list of dicts (used by verify.py)."""
    try:
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        return []
