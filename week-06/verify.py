"""Acceptance scenarios for Week 6.  Run:  python verify.py   (add --punch for the Second Punch)

The scenarios start and stop the Catalogue Service (port 8101) themselves.
STOP YOUR OWN catalog_service/run.py (Ctrl+C) BEFORE running this file.
Keep app.build(mode, db_path, catalog_url), app.enroll_command(p, sid, cid) and
reports.fill_report(p): these scenarios call them.
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import io
import json
import os
import socket
import sqlite3
import subprocess
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import app  # noqa: E402
import reports  # noqa: E402

PORT = 8101
URL = f"http://127.0.0.1:{PORT}"
TMP = Path(tempfile.mkdtemp())
STALENESS_BOUND_S = 2.0      # from the brief: course data seen by the monolith is at most 2 s stale
BUSY = (f"Портът {PORT} е зает — спри своя catalog_service/run.py с Ctrl+C и пусни verify.py пак.\n"
        f"Port {PORT} is busy — stop your own server with Ctrl+C and run verify.py again.")


def port_open():
    with socket.socket() as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


class CatalogueService:
    """Starts catalog_service/run.py as a separate process with its own catalog.db."""

    def __init__(self):
        self.db_path = TMP / f"catalog-{time.time_ns()}.db"
        self.proc = None

    def __enter__(self):
        assert not port_open(), BUSY
        env = dict(os.environ, CATALOG_DB=str(self.db_path))
        self.proc = subprocess.Popen([sys.executable, str(HERE / "catalog_service" / "run.py"), "--port", str(PORT)],
                                     env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
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


def http_get(path):
    try:
        with urllib.request.urlopen(URL + path, timeout=3) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


def local():
    return app.build("local", TMP / f"mono-{time.time_ns()}.db")


def remote():
    return app.build("remote", TMP / f"mono-{time.time_ns()}.db", URL)


# ---------------------------------------------------------------- baseline
def s1_local_monolith_works():
    p = local()
    ok, msg = app.enroll_command(p, 1, 1)
    assert ok, msg
    assert any("SA101" in line and "1/3" in line for line in reports.fill_report(p)), "fill report should show SA101 1/3"


def s2_local_capacity_rule():
    p = local()
    app.enroll_command(p, 1, 2)
    app.enroll_command(p, 2, 2)
    ok, msg = app.enroll_command(p, 3, 2)
    assert not ok and "full" in msg, "AI201 (capacity 2) must reject the third student"


# ---------------------------------------------------------------- target (REQ)
def s3_service_serves_own_data():
    with CatalogueService():
        status, body = http_get("/courses")
        assert status == 200 and body and len(body.get("courses", [])) == 4, f"GET /courses -> {status} {body}"
        status, body = http_get("/courses/1")
        assert status == 200 and body.get("code") == "SA101", f"GET /courses/1 -> {status} {body}"
        status, _ = http_get("/courses/99")
        assert status == 404, f"GET /courses/99 should be 404, got {status}"
        status, _ = http_get("/courses/1/extra")
        assert status == 404, f"GET /courses/1/extra must not match /courses/<id> (got {status})"


def s4_monolith_does_not_own_courses_in_remote_mode():
    with CatalogueService():
        path = TMP / f"mono-{time.time_ns()}.db"
        app.build("local", path)                       # a monolith DB that still has a courses table ...
        p = app.build("remote", path, URL)             # ... is switched to remote mode
        tables = {r[0] for r in p.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "courses" not in tables, "in remote mode the monolith database must not have a courses table"
        codes = [c["code"] for c in p.catalog.list_courses()]
        assert codes == ["SA101", "AI201", "DB150", "PR102"], f"list_courses via the service returned {codes}"


def s5_enrollment_end_to_end_over_http():
    with CatalogueService():
        p = remote()
        assert app.enroll_command(p, 1, 2)[0], "student 1 -> AI201 should succeed"
        assert app.enroll_command(p, 2, 2)[0], "student 2 -> AI201 should succeed"
        ok, msg = app.enroll_command(p, 3, 2)
        assert not ok and "full" in msg, f"capacity from the service must be enforced, got {msg!r}"
        ok, msg = app.enroll_command(p, 1, 99)
        assert not ok and "Unknown course" in msg, f"unknown course must be rejected, got {msg!r}"


def s6_owner_changes_visible_within_staleness_bound():
    with CatalogueService() as svc:
        p = remote()
        p.catalog.get_course(1)
        with sqlite3.connect(svc.db_path) as c:        # the Curriculum team edits THEIR data
            c.execute("UPDATE courses SET title = 'Software Architecture II' WHERE id = 1")
        deadline = time.monotonic() + STALENESS_BOUND_S + 0.5
        title = None
        while time.monotonic() < deadline:
            title = p.catalog.get_course(1)["title"]
            if title == "Software Architecture II":
                return
            time.sleep(0.2)
        raise AssertionError(f"after {STALENESS_BOUND_S:.0f} s the monolith still shows {title!r}: "
                             "course data must come from its owner (a cache is fine, but at most 2 s stale)")


# ---------------------------------------------------------------- reference path (guidance, not graded)
def s7_remote_calls_have_a_timeout():
    with CatalogueService():
        p = remote()
        assert getattr(p.catalog, "timeout", None), \
            "the reference path gives CatalogClient a timeout (a network call must not wait forever — Week 7)"


SCENARIOS = [
    ("S1", "baseline", "Local monolith: enroll + fill report", s1_local_monolith_works),
    ("S2", "baseline", "Local monolith: capacity rule", s2_local_capacity_rule),
    ("S3", "target", "Catalogue Service answers GET /courses, /courses/<id>, 404 from its own DB", s3_service_serves_own_data),
    ("S4", "target", "Remote mode: monolith has no courses table, lists courses via the service", s4_monolith_does_not_own_courses_in_remote_mode),
    ("S5", "target", "Remote mode: enrollment rules work end-to-end over HTTP", s5_enrollment_end_to_end_over_http),
    ("S6", "target", "A change in catalog.db reaches the monolith within 2 s, no restart", s6_owner_changes_visible_within_staleness_bound),
    ("S7", "path", "CatalogClient uses a timeout", s7_remote_calls_have_a_timeout),
]


def load_punch():
    """The Second Punch is released in class (punch_scenarios.py). Before that it is not in your folder."""
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
            print(f"[PASS] {sid} (path) {title}" if ok else f"[path] {sid} {title} -> насока/guidance: {msg}")
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
