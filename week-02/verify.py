"""Acceptance scenarios for Week 2.  Run:  python verify.py   (add --punch for the Second Punch)

The scenarios run `python cli.py ...` as a user would, and temporarily drop test
plug-ins into plugins/ (they are always removed again).
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import io
import re
import shutil
import subprocess
import traceback
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
PLUGINS = HERE / "plugins"

PROBE = '''NAME = "probe"
def generate(data):
    return "PROBE OK " + str(len(data.students)) + "\\n"
'''
NO_GENERATE = '''NAME = "half-done"
'''
EXPLODES = '''NAME = "boom"
def generate(data):
    raise RuntimeError("faculty bug")
'''
MUTATES = '''NAME = "mutator"
import data as _core


def generate(snapshot):
    for attempt in (lambda: snapshot.students[0].__setitem__("name", "HACKED"),
                    lambda: snapshot.students.append({"id": 0, "name": "HACKED", "email": "-"})):
        try:
            attempt()
        except Exception:
            pass
    return "core sees: " + _core.STUDENTS[0]["name"] + " / " + str(len(_core.STUDENTS)) + " students\\n"
'''
def cli(*args):
    """Run the CLI like a user. Returns (exit_code, stdout, stderr)."""
    r = subprocess.run([sys.executable, "cli.py", *args], cwd=HERE, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr


class dropped_plugin:
    """Temporarily place a plug-in file in plugins/ (or copy one from punch/).

    A file of the same name that was already there (e.g. one you copied yourself) is put back afterwards."""

    def __init__(self, filename, source=None, copy_from=None):
        self.path = PLUGINS / filename
        self.source, self.copy_from = source, copy_from
        self.previous = None

    def __enter__(self):
        self.previous = self.path.read_bytes() if self.path.exists() else None
        if self.copy_from:
            shutil.copy(self.copy_from, self.path)
        else:
            self.path.write_text(self.source, encoding="utf-8")
        return self.path

    def __exit__(self, *exc):
        if self.previous is None:
            self.path.unlink(missing_ok=True)
        else:
            self.path.write_bytes(self.previous)


def report_names():
    code, out, _ = cli("reports")
    assert code == 0, "`python cli.py reports` must not fail"
    return out


# ---------------------------------------------------------------- baseline
def s1_csv_report():
    code, out, _ = cli("report", "csv")
    assert code == 0 and out.startswith("id,name,email") and "Maria Ivanova" in out, "csv report broken"


def s2_txt_report():
    code, out, _ = cli("report", "txt")
    assert code == 0 and "Ivan Petrov" in out, "txt report broken"


def s3_unknown_report_is_a_message():
    code, out, err = cli("report", "does-not-exist")
    assert code != 0 and "Traceback" not in err, "unknown report must give a message, not a crash"


# ---------------------------------------------------------------- target
def s4_course_fill_report():
    assert "course-fill" in report_names(), "a 'course-fill' report should be listed"
    code, out, _ = cli("report", "course-fill")
    assert code == 0 and "SA101" in out and "2/3" in out, f"course-fill should show SA101 2/3, got:\n{out}"


def s5_no_report_names_in_core():
    pattern = re.compile(r"""["'](csv|txt|course-fill)["']""")
    core_files = [HERE / "cli.py", *sorted((HERE / "core").glob("*.py"))]
    if (HERE / "reports.py").exists():
        core_files.append(HERE / "reports.py")
    offenders = [f.name for f in core_files if pattern.search(f.read_text(encoding="utf-8"))]
    assert not offenders, f"report names are hard-coded in the core: {', '.join(offenders)}"


def s6_drop_in_plugin_appears():
    with dropped_plugin("probe_report.py", PROBE):
        assert "probe" in report_names(), "a new file in plugins/ should appear without core changes"
        code, out, _ = cli("report", "probe")
        assert code == 0 and "PROBE OK 4" in out, "the new plug-in should run on the core's data"


def s7_invalid_plugin_is_skipped():
    with dropped_plugin("half_done.py", NO_GENERATE), dropped_plugin("probe_report.py", PROBE):
        names = report_names()
        assert "probe" in names, "plug-ins must be discovered from plugins/ (see S6)"
        assert "half-done" not in names, "a file without generate(data) must not be offered as a report"
        assert "csv" in names, "valid plug-ins must still load"


def s8_crashing_plugin_does_not_crash_core():
    with dropped_plugin("boom.py", EXPLODES):
        assert "boom" in report_names(), "a plug-in that fulfils the contract must be listed"
        code, out, err = cli("report", "boom")
        assert "Traceback" not in err, "a failing plug-in must not crash the CLI"
        assert "boom" in out + err, "the user should see which report failed (its NAME in the message)"
        assert code != 0, "a failed report must end with a non-zero exit code (return 2 from main)"
        assert cli("report", "csv")[0] == 0, "other reports must keep working"


def s9_plugins_cannot_change_core_data():
    with dropped_plugin("mutator.py", MUTATES):
        assert "mutator" in report_names(), "a plug-in that fulfils the contract must be listed"
        code, out, err = cli("report", "mutator")
        assert "Traceback" not in err, "a plug-in that tries to change data must not crash the CLI"
        assert "HACKED" not in out and "/ 4 students" in out, \
            f"the plug-in changed the core's data -- give plug-ins a copy or a read-only view: {out.strip()}"


SCENARIOS = [
    ("S1", "baseline", "csv report works", s1_csv_report),
    ("S2", "baseline", "txt report works", s2_txt_report),
    ("S3", "baseline", "Unknown report name gives a message, not a crash", s3_unknown_report_is_a_message),
    ("S4", "target", "Course-fill statistics report is available", s4_course_fill_report),
    ("S5", "path", "No report names hard-coded in the core (cli.py, core/)", s5_no_report_names_in_core),
    ("S6", "target", "Dropping a file into plugins/ adds a report with zero core changes", s6_drop_in_plugin_appears),
    ("S7", "target", "A file that breaks the contract is skipped", s7_invalid_plugin_is_skipped),
    ("S8", "target", "A plug-in that raises does not crash the core", s8_crashing_plugin_does_not_crash_core),
    ("S9", "target", "A plug-in cannot change the core's data", s9_plugins_cannot_change_core_data),
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
