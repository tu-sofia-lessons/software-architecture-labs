"""Acceptance scenarios for Week 7.  Run:  python verify.py   (add --punch for the Second Punch)

The scenarios start the Catalogue Service (port 8101) with different chaos flags.
Keep app.build(db_path, catalog_url), app.browse_command(p), app.enroll_command(p, sid, cid)
and the CatalogClient(base_url) constructor: these scenarios call them.
STOP YOUR OWN catalog_service/run.py (Ctrl+C) BEFORE running this file.
Takes about 30-40 seconds.
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import io
import os
import socket
import subprocess
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import app  # noqa: E402
import obs  # noqa: E402

PORT = 8101
URL = f"http://127.0.0.1:{PORT}"
TMP = Path(tempfile.mkdtemp())
BUSY = (f"Портът {PORT} е зает — спри своя catalog_service/run.py с Ctrl+C и пусни verify.py пак.\n"
        f"Port {PORT} is busy — stop your own server with Ctrl+C and run verify.py again.")


def port_open():
    with socket.socket() as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


class CatalogueService:
    """Runs catalog_service/run.py with chaos flags, its own catalog.db and its own log file."""

    def __init__(self, *flags):
        self.flags = [str(f) for f in flags]
        self.log_path = TMP / f"service-{time.time_ns()}.log"
        self.proc = None

    def __enter__(self):
        assert not port_open(), BUSY
        env = dict(os.environ, CATALOG_DB=str(TMP / "catalog.db"), OBS_LOG=str(self.log_path))
        cmd = [sys.executable, str(HERE / "catalog_service" / "run.py"), "--port", str(PORT), *self.flags]
        self.proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        deadline = time.time() + 5
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise AssertionError("catalog service crashed: " + self.proc.stderr.read().decode()[-300:])
            if port_open():
                return self
            time.sleep(0.05)
        raise AssertionError("catalog service did not start on port 8101")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=5)

    def __exit__(self, *exc):
        self.stop()


def platform():
    obs.LOG_PATH = str(TMP / f"client-{time.time_ns()}.log")
    return app.build(TMP / f"mono-{time.time_ns()}.db", URL)


def timed(fn, *args):
    start = time.monotonic()
    try:
        return fn(*args), time.monotonic() - start
    except Exception as e:  # report the exception together with the elapsed time
        return e, time.monotonic() - start


def service_calls():
    import json
    import urllib.request
    with urllib.request.urlopen(f"{URL}/stats", timeout=5) as r:
        return json.loads(r.read())["calls"]


# ---------------------------------------------------------------- baseline
def s1_healthy_browse():
    with CatalogueService():
        courses, stale = app.browse_command(platform())
        assert len(courses) == 4 and not stale, "healthy service: 4 fresh courses"


def s2_healthy_enroll():
    with CatalogueService():
        ok, msg = app.enroll_command(platform(), 1, 1)
        assert ok, msg


def s3_retries_are_bounded():
    with CatalogueService("--fail-rate", "1.0"):
        p = platform()
        for _ in range(5):
            timed(p.catalog.get_course, 1)
        calls = service_calls()
        assert calls <= 15, f"5 operations caused {calls} service calls (max 3 per operation)"


# ---------------------------------------------------------------- target
def s4_slow_service_does_not_hang_us():
    p = platform()
    with CatalogueService():
        app.browse_command(p)                              # a healthy call first
    with CatalogueService("--delay", "5"):
        result, elapsed = timed(app.browse_command, p)
        assert elapsed < 4.0, f"browse waited {elapsed:.1f}s for a slow service"
        assert isinstance(result, tuple) and result[1] is True and len(result[0]) == 4, \
            f"browse during an outage should return the last known list marked stale, got {result!r}"
        (ok, msg), elapsed = timed(app.enroll_command, p, 1, 1)
        assert elapsed < 4.0 and not ok, f"enroll should fail clearly and fast, took {elapsed:.1f}s ok={ok}"


def s5_flaky_service_is_masked_for_idempotent_reads():
    with CatalogueService("--fail-rate", "0.5", "--seed", "7"):
        p = platform()
        ok = sum(1 for _ in range(20) if isinstance(timed(p.catalog.get_course, 1)[0], dict))
        assert ok >= 16, f"only {ok}/20 get_course calls succeeded against a 50% flaky service"


def s6_outage_browse_stale_enroll_refused():
    p = platform()
    with CatalogueService():
        app.browse_command(p)
        assert app.enroll_command(p, 2, 1)[0], "healthy enroll should work"   # the client has seen SA101
    # the service is now down
    result, elapsed = timed(app.browse_command, p)
    assert isinstance(result, tuple) and result[1] is True, f"browse while down should be stale data, got {result!r}"
    (ok, msg), _ = timed(app.enroll_command, p, 1, 1)
    assert not ok and "unavailable" in msg.lower(), f"enroll while down must be refused clearly, got {msg!r}"
    count = p.conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]
    assert count == 1, "no enrollment may be written without a current capacity check (only the healthy one exists)"


def s7_request_id_links_client_and_service_logs():
    with CatalogueService() as svc:
        p = platform()
        app.browse_command(p)
        time.sleep(0.2)
        client = [e for e in obs.read(obs.LOG_PATH) if e.get("request_id")]
        served = {e.get("request_id") for e in obs.read(svc.log_path)}
        assert client, "the client should log each catalogue call with a request_id (obs.log)"
        assert {"op", "outcome", "latency_ms"} <= set(client[-1]), f"client log misses fields: {client[-1]}"
        assert client[-1]["request_id"] in served, "the service log must show the same request id (X-Request-Id)"


SCENARIOS = [
    ("S1", "baseline", "Healthy service: browse returns fresh courses", s1_healthy_browse),
    ("S2", "baseline", "Healthy service: enroll works", s2_healthy_enroll),
    ("S3", "baseline", "Retries stay bounded (max 3 service calls per operation)", s3_retries_are_bounded),
    ("S4", "target", "Slow service (5 s): browse answers stale in < 4 s, enroll fails fast", s4_slow_service_does_not_hang_us),
    ("S5", "target", "Flaky service (50%): >= 16/20 get_course calls succeed", s5_flaky_service_is_masked_for_idempotent_reads),
    ("S6", "target", "Service down: browse stale, enroll refused, nothing written", s6_outage_browse_stale_enroll_refused),
    ("S7", "baseline", "One request id in client log and service log", s7_request_id_links_client_and_service_logs),
]


def load_punch():
    """The Second Punch is released in class (punch_scenarios.py: P1 + the reference-path hint S8).
    Before that it is not in your folder."""
    try:
        import punch_scenarios
    except ImportError:
        return None
    return punch_scenarios.scenarios(globals())


def main():
    if port_open():
        print(BUSY)
        return 2
    run_punch = "--punch" in sys.argv
    scenarios = list(SCENARIOS)
    if run_punch:
        extra = load_punch()
        if extra is None:
            print("Вторият удар още не е пуснат (няма punch_scenarios.py). / Second Punch not released yet.\n")
        else:
            scenarios += extra
    graded = passed = hints_ok = hints = 0
    for sid, tag, title, fn in scenarios:
        try:
            with redirect_stdout(io.StringIO()):
                fn()
            ok, msg = True, ""
        except AssertionError as e:
            ok, msg = False, str(e)
        except Exception as e:  # a crash is also a failure, show where
            ok, msg = False, f"{type(e).__name__}: {e}"
        if tag == "path":                       # reference-path guidance: shown, never graded
            hints += 1
            hints_ok += ok
            print(f"[PASS] {sid} (path) {title}" if ok else f"[path] {sid} {title} -> насока/guidance: {msg}", flush=True)
            continue
        graded += 1
        passed += ok
        print(f"[PASS] {sid} {title}" if ok else f"[FAIL] {sid} {title} -> {msg}", flush=True)
    note = "All graded (REQ) scenarios pass." if passed == graded else "Target scenarios fail until you complete the Build."
    print(f"\nREQ {passed}/{graded} passed. {note}  PATH hints: {hints_ok}/{hints}."
          + ("" if run_punch else "  (Second Punch: python verify.py --punch)"))
    return 0 if passed == graded else 1


if __name__ == "__main__":
    sys.exit(main())
