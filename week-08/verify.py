"""Acceptance scenarios for Week 8.  Run:  python verify.py   (add --punch for the Second Punch)

verify.py starts and stops the API (port 8103) by itself for every scenario.
Keep attack.py, client.py and identity.py unchanged: the scenarios use them.
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
import time
import traceback
from contextlib import contextmanager, redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
os.environ["PLATFORM_SECRET"] = "verify-secret"   # this process and the API share it
os.environ.pop("PLATFORM_ENV", None)

import attack  # noqa: E402
import config  # noqa: E402
from client import call, login_headers  # noqa: E402

PORT = 8103


def port_open():
    with socket.socket() as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


@contextmanager
def api_server(env_overrides=None):
    """Start a fresh API process (fresh data), wait until it answers, stop it afterwards."""
    assert not port_open(), f"port {PORT} is already in use - stop your own api.py first"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    proc = subprocess.Popen([sys.executable, "api.py"], cwd=HERE, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(50):
            if proc.poll() is not None:
                raise AssertionError(f"api.py exited: {proc.stderr.read().strip()[-300:]}")
            if port_open():
                break
            time.sleep(0.1)
        else:
            raise AssertionError("api.py did not start within 5 s")
        yield proc
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)


def statuses(ids):
    """Run attack.py's cases against a fresh API; return {id: status} for the given ids."""
    with api_server():
        results = attack.run_all(config.secret())
    return {cid: status for cid, _, _, status, _ in results if cid in ids}


def as_(user, ttl=3600):
    return login_headers(user, config.secret(), ttl)


# ---------------------------------------------------------------- baseline
def s1_legitimate_requests_allowed():
    got = statuses({"L1", "L2", "L3", "L4", "L5"})
    expected = {"L1": 200, "L2": 201, "L3": 200, "L4": 201, "L5": 201}
    assert got == expected, f"legitimate requests must succeed: expected {expected}, got {got}"


def s2_dev_mode_starts_without_secret():
    with api_server({"PLATFORM_SECRET": None, "PLATFORM_ENV": "dev"}):
        status, _ = call("GET", "/health")
    assert status == 200, "with PLATFORM_ENV=dev the API must start for local development"


# ---------------------------------------------------------------- target
def s3_unauthenticated_get_401():
    got = statuses({"A1", "A2", "A6"})
    with api_server():
        got["no credentials"], _ = call("GET", "/students/1/grades")
    wrong = {k: v for k, v in got.items() if v != 401}
    assert not wrong, f"missing/forged/tampered/expired credentials must give 401, got {wrong}"


def s4_forbidden_get_403_and_change_nothing():
    got = statuses({"A3", "A4", "A5", "A7", "A8", "A9", "A10"})
    wrong = {k: v for k, v in got.items() if v != 403}
    assert not wrong, f"authenticated but not allowed must give 403, got {wrong}"
    with api_server():
        call("POST", "/grades", as_("maria"), {"student_id": 1, "course_id": 1, "grade": 6.0})
        _, body = call("GET", "/students/1/grades", as_("maria"))
    assert body.get("grades") == [{"course": "SA101", "grade": 5.5}], "a denied request must not change data"


def s5_x_user_header_ignored():
    headers = dict(as_("maria"), **{"X-User": "registrar"})
    with api_server():
        status, _ = call("GET", "/students/2/grades", headers)
    assert status == 403, f"identity must come from the token, not from X-User (got {status})"


def s6_no_secret_in_source():
    old_secret = "uni-platform-" + "secret-2026"
    offenders = [p.name for p in HERE.glob("*.py")
                 if p.name != "verify.py" and old_secret in p.read_text(encoding="utf-8")]
    assert not offenders, f"hard-coded secret still in: {', '.join(offenders)}"


def s7_refuses_to_start_without_secret():
    assert not port_open(), f"port {PORT} is already in use - stop your own api.py first"
    env = {k: v for k, v in os.environ.items() if k not in ("PLATFORM_SECRET", "PLATFORM_ENV")}
    proc = subprocess.Popen([sys.executable, "api.py"], cwd=HERE, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        raise AssertionError("without PLATFORM_SECRET (and not in dev) the API must refuse to start")
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
    assert proc.returncode != 0, "refusing to start must exit with a non-zero code"


# ---------------------------------------------------------------- reference path (guidance, not graded)
def s8_rules_live_in_one_policy_place():
    policy = HERE / "policy.py"
    assert policy.exists(), ("reference path keeps every 'who may do what' rule in one module (policy.py); "
                             "if your rules live elsewhere, name that place in your ADR")
    text = policy.read_text(encoding="utf-8")
    assert "def can_" in text, "reference path: one small can_...() function per rule"


SCENARIOS = [
    ("S1", "baseline", "Legitimate requests are allowed", s1_legitimate_requests_allowed),
    ("S2", "baseline", "API starts for local development (PLATFORM_ENV=dev)", s2_dev_mode_starts_without_secret),
    ("S3", "target", "Missing, forged, tampered or expired credentials -> 401", s3_unauthenticated_get_401),
    ("S4", "target", "Authenticated but not allowed -> 403, and nothing changes", s4_forbidden_get_403_and_change_nothing),
    ("S5", "target", "The X-User header is ignored; identity comes from the token", s5_x_user_header_ignored),
    ("S6", "target", "No hard-coded secret in the source code", s6_no_secret_in_source),
    ("S7", "target", "API refuses to start without PLATFORM_SECRET outside dev", s7_refuses_to_start_without_secret),
    ("S8", "path", "Authorization rules live in one policy module (reference path)", s8_rules_live_in_one_policy_place),
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
        print(f"Портът {PORT} е зает: спри своя api.py (Ctrl+C) и пусни verify.py отново.\n"
              f"Port {PORT} is busy (in use): stop your own api.py (Ctrl+C), then run verify.py again.")
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
        print(f"[PASS] {sid} {title}" if ok else f"[FAIL] {sid} {title} -> {msg}")
    note = "All graded (REQ) scenarios pass." if passed == graded else "Target scenarios fail until you complete the Build."
    print(f"\nREQ {passed}/{graded} passed. {note}  PATH hints: {hints_ok}/{hints}."
          + ("" if run_punch else "  (Second Punch: python verify.py --punch)"))
    return 0 if passed == graded else 1


if __name__ == "__main__":
    sys.exit(main())
