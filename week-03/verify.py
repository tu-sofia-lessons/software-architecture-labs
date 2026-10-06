"""Acceptance scenarios for Week 3.  Run:  python verify.py   (add --punch for the Second Punch)

verify.py starts and stops its own file server on port 8102, on a temporary copy of
server_files/ -- stop any file_server.py you started yourself before running it.
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
import shutil
import socket
import subprocess
import tempfile
import time
import traceback
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
PORT = 8102
URL = f"http://127.0.0.1:{PORT}"


def port_open():
    with socket.socket() as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


class file_server:
    """Run file_server.py (with optional flags) on a fresh copy of server_files/."""

    def __init__(self, *flags):
        self.flags = flags

    def __enter__(self):
        assert not port_open(), f"port {PORT} is busy -- stop your own file_server.py first"
        self.root = Path(tempfile.mkdtemp()) / "server_files"
        shutil.copytree(HERE / "server_files", self.root)
        self.proc = subprocess.Popen(
            [sys.executable, str(HERE / "file_server.py"), "--port", str(PORT), "--root", str(self.root), *self.flags],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 5
        while not port_open():
            assert time.time() < deadline, "file server did not start"
            time.sleep(0.05)
        return self.root

    def __exit__(self, *exc):
        self.proc.terminate()
        self.proc.wait(timeout=5)


def cli(*args, backend="local", **env):
    """Run the CLI like a user. Returns (exit_code, stdout, stderr, seconds)."""
    tmp = Path(tempfile.mkdtemp())
    local_root = tmp / "local_materials"
    shutil.copytree(HERE / "local_materials", local_root)
    full_env = {**os.environ, "MATERIALS_BACKEND": backend, "MATERIALS_URL": URL,
                "MATERIALS_ROOT": str(local_root), "DOWNLOADS_DIR": str(tmp / "downloads"), **env}
    start = time.time()
    r = subprocess.run([sys.executable, "cli.py", *args], cwd=HERE, env=full_env,
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr, time.time() - start, tmp


def assert_graceful_unavailable(code, out, err):
    assert "Traceback" not in err, f"the CLI crashed instead of explaining:\n{err.strip().splitlines()[-1]}"
    assert code != 0, "a failed operation must not report success (exit code 0)"
    text = (out + err).lower()
    assert "unavailable" in text or "недостъп" in text, "tell the user that course materials are unavailable"


# ---------------------------------------------------------------- baseline
def s1_local_list():
    code, out, *_ = cli("materials", "list", "1")
    assert code == 0 and "lecture01.txt" in out and "assignment01.txt" in out, "local list broken"


def s2_local_get():
    code, out, err, _, tmp = cli("materials", "get", "1", "lecture01.txt")
    saved = tmp / "downloads" / "lecture01.txt"
    assert code == 0 and saved.read_bytes() == (HERE / "local_materials/course_1/lecture01.txt").read_bytes()


def s3_service_depends_only_on_contract():
    text = (HERE / "materials" / "service.py").read_text(encoding="utf-8")
    for word in ("local_store", "remote_store", "http", "server_files", "8102"):
        assert word not in text, f"MaterialService should know only the MaterialStore contract, found {word!r}"


def s4_students_work_while_file_server_down():
    assert not port_open(), f"port {PORT} is busy -- stop your own file_server.py first"
    code, out, *_ = cli("list-students", backend="remote")
    assert code == 0 and "Maria Ivanova" in out, "local features must not depend on the file server"


# ---------------------------------------------------------------- target
def s5_remote_round_trip():
    with file_server() as root:
        upload = Path(tempfile.mkdtemp()) / "notes.txt"
        upload.write_bytes(b"week 3 notes\n")
        code, out, err, *_ = cli("materials", "put", "1", str(upload), backend="remote")
        assert code == 0, f"remote put failed: {err.strip()[-200:]}"
        assert (root / "course_1" / "notes.txt").read_bytes() == b"week 3 notes\n", "file not on the server"
        code, out, *_ = cli("materials", "list", "1", backend="remote")
        assert "notes.txt" in out and "lecture01.txt" in out, "remote list should show server files"
        code, out, err, _, tmp = cli("materials", "get", "1", "notes.txt", backend="remote")
        assert (tmp / "downloads" / "notes.txt").read_bytes() == b"week 3 notes\n", "remote get broken"


def s6_server_down_is_explained():
    assert not port_open(), f"port {PORT} is busy -- stop your own file_server.py first"
    code, out, err, *_ = cli("materials", "list", "1", backend="remote")
    assert_graceful_unavailable(code, out, err)


def s7_contract_includes_failure():
    from materials.remote_store import RemoteMaterialStore
    from materials.store import MaterialsUnavailable
    try:
        RemoteMaterialStore(URL).list(1)
    except MaterialsUnavailable:
        return
    raise AssertionError("server down: RemoteMaterialStore.list should raise MaterialsUnavailable")


def s8_missing_file_same_error_for_both_stores():
    from materials.local_store import LocalMaterialStore
    from materials.remote_store import RemoteMaterialStore
    from materials.store import MaterialNotFound
    stores = [("local", LocalMaterialStore(HERE / "local_materials"))]
    with file_server():
        stores.append(("remote", RemoteMaterialStore(URL)))
        for kind, store in stores:
            try:
                store.read(1, "missing.txt")
                raise AssertionError(f"{kind}: reading a missing file must fail")
            except MaterialNotFound:
                pass


def s9_slow_server_fails_fast():
    with file_server("--delay", "3"):
        code, out, err, seconds, _ = cli("materials", "list", "1", backend="remote")
    assert seconds < 2.8, f"the CLI waited {seconds:.1f}s for a slow server -- use a timeout"
    assert_graceful_unavailable(code, out, err)


def s10_missing_file_same_answer_on_both_backends():
    answers = {}
    with file_server():
        for backend in ("local", "remote"):
            code, out, err, *_ = cli("materials", "get", "1", "missing.txt", backend=backend)
            assert "Traceback" not in err, f"{backend}: a missing file crashed the CLI"
            assert code != 0, f"{backend}: a missing file must not report success"
            assert "unavailable" not in (out + err).lower() and "недостъп" not in (out + err).lower(), \
                f"{backend}: a missing file is not an outage -- don't tell the user to retry later"
            answers[backend] = code
    assert answers["local"] == answers["remote"], \
        f"same situation, different answers: exit code local={answers['local']} remote={answers['remote']}"


def s11_empty_course_is_not_an_outage():
    with file_server():
        code_up, out_up, err_up, *_ = cli("materials", "list", "99", backend="remote")
    assert code_up == 0 and "unavailable" not in (out_up + err_up).lower(), \
        "a course with no files is a normal answer, not a failure"
    code_down, out_down, err_down, *_ = cli("materials", "list", "99", backend="remote")
    assert code_down != 0 and code_down != code_up, "server down must be distinguishable from an empty course"


SCENARIOS = [
    ("S1", "baseline", "Local backend lists course materials", s1_local_list),
    ("S2", "baseline", "Local backend downloads a file", s2_local_get),
    ("S3", "path", "MaterialService knows only the MaterialStore contract", s3_service_depends_only_on_contract),
    ("S4", "baseline", "Students work while the file server is down", s4_students_work_while_file_server_down),
    ("S5", "target", "Remote backend: put, list, get round trip through the file server", s5_remote_round_trip),
    ("S6", "target", "File server down: CLI explains, no crash", s6_server_down_is_explained),
    ("S7", "path", "Contract: RemoteMaterialStore raises MaterialsUnavailable when down", s7_contract_includes_failure),
    ("S8", "path", "Contract: missing file raises MaterialNotFound in BOTH stores", s8_missing_file_same_error_for_both_stores),
    ("S9", "target", "Slow file server (3 s): CLI gives up within ~2 s", s9_slow_server_fails_fast),
    ("S10", "target", "A missing file gets the same answer on both backends (not an outage)", s10_missing_file_same_answer_on_both_backends),
    ("S11", "target", "An empty course is not reported as an outage", s11_empty_course_is_not_an_outage),
]


def load_punch():
    """The Second Punch is released in class (punch_scenarios.py). Before that it is not in your folder."""
    try:
        import punch_scenarios
    except ImportError:
        return None
    return punch_scenarios.scenarios(globals())


def main():
    run_punch = "--punch" in sys.argv
    scenarios = list(SCENARIOS)
    if run_punch:
        extra = load_punch()
        if extra is None:
            print("Вторият удар още не е пуснат (няма punch_scenarios.py). / Second Punch not released yet.\n")
        else:
            scenarios += extra
    graded = passed = hints_ok = hints = 0
    failed_tags = set()
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
        if not ok:
            failed_tags.add(tag)
        print(f"[PASS] {sid} {title}" if ok else f"[FAIL] {sid} {title} -> {msg}")
    if passed == graded:
        note = "All graded (REQ) scenarios pass."
    elif failed_tags == {"punch"}:
        note = "The Second Punch scenarios fail until your code copes with the change."
    else:
        note = "Target scenarios fail until you complete the Build."
    print(f"\nREQ {passed}/{graded} passed. {note}  PATH hints: {hints_ok}/{hints}."
          + ("" if run_punch else "  (Second Punch: python verify.py --punch)"))
    return 0 if passed == graded else 1


if __name__ == "__main__":
    sys.exit(main())
