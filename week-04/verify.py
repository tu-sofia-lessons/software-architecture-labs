"""Acceptance scenarios for Week 4.  Run:  python verify.py   (add --punch after the Second Punch is released)

Keep the signatures of import_cli.run_import(source, store) and
importer.pipelines.<source>_pipeline(store): they are what these scenarios call.
REQ lines ([PASS]/[FAIL]) are graded. [path] lines are hints along the reference path only.
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass


import io
import traceback
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import import_cli  # noqa: E402
from importer import pipelines  # noqa: E402
from importer.sources import read_csv  # noqa: E402
from importer.store import DuplicateStudent, StudentStore  # noqa: E402


def names(fs):
    return [getattr(f, "__name__", type(f).__name__) for f in fs]


def emails(store):
    return sorted(s["email"] for s in store.list_all())


def run_logged(source):
    """Run one import, return (store, log lines)."""
    store, out = StudentStore(), io.StringIO()
    with redirect_stdout(out):
        import_cli.run_import(source, store)
    return store, out.getvalue().splitlines()


# ---------------------------------------------------------------- baseline (REQ)
def s1_admissions_import_stores_three():
    store = StudentStore()
    import_cli.run_import("admissions", store)
    assert emails(store) == ["georgi.georgiev@tu-sofia.bg", "ivan.petrov@tu-sofia.bg",
                             "maria.ivanova@tu-sofia.bg"], f"unexpected students: {emails(store)}"


def s7_right_people_with_right_names():
    """Order property: the first record of each person wins, cleaned. A clean e-mail alone is not enough."""
    store = StudentStore()
    import_cli.run_import("admissions", store)
    got = sorted((s["name"], s["email"]) for s in store.list_all())
    assert got == [("Georgi Georgiev", "georgi.georgiev@tu-sofia.bg"),
                   ("Ivan Petrov", "ivan.petrov@tu-sofia.bg"),
                   ("Maria Ivanova", "maria.ivanova@tu-sofia.bg")], f"wrong people or names stored: {got}"


# ---------------------------------------------------------------- target (REQ)
def s3_erasmus_import_works():
    store = StudentStore()
    import_cli.run_import("erasmus", store)
    got = {(s["name"], s["email"], s["source"]) for s in store.list_all()}
    assert got == {("Giulia Rossi", "giulia.rossi@unibo.example.it", "erasmus"),
                   ("Lukas Weber", "lukas.weber@tum.example.de", "erasmus")}, f"unexpected Erasmus students: {sorted(got)}"


def s4_every_dropped_record_is_accounted_for():
    """Traceability: the stage log shows where records were dropped, and the drops add up."""
    for source, delimiter, filename in (("admissions", ",", "admissions.csv"), ("erasmus", ";", "erasmus.csv")):
        rows = read_csv(HERE / "data" / filename, delimiter)
        store, log = run_logged(source)
        stages = [l for l in log if "→" in l and "dropped" in l]
        assert len(stages) >= 2, f"{source}: the log should show each stage as 'in → out (dropped n)' (use importer.pipeline.run)"
        dropped = sum(int(l.rsplit("dropped", 1)[1].strip(" )")) for l in stages)
        assert dropped == len(rows) - len(store.list_all()), \
            f"{source}: {len(rows)} rows in, {len(store.list_all())} stored, but the log accounts for {dropped} dropped"


# ---------------------------------------------------------------- reference path (guidance, not graded)
def s2_pipelines_are_lists_of_filters():
    for build in (pipelines.admissions_pipeline, pipelines.erasmus_pipeline):
        filters = build(StudentStore())
        assert isinstance(filters, list) and len(filters) >= 4, f"{build.__name__}: reference path has one filter per step (>= 4)"
        for f in filters:
            assert callable(f) and f([]) == [], f"filter {names([f])[0]} should accept and return a list"


def s5_order_normalize_before_dedupe():
    order = names(pipelines.admissions_pipeline(StudentStore()))
    norm = next((i for i, n in enumerate(order) if "normal" in n), None)
    dedupe = next((i for i, n in enumerate(order) if "dedup" in n or "duplicate" in n), None)
    assert norm is not None and dedupe is not None, f"reference path names a normalize and a dedupe filter, got {order}"
    assert norm < dedupe, f"dedupe runs before normalize: {order}"


def s6_erasmus_composition_and_no_legacy():
    order = names(pipelines.erasmus_pipeline(StudentStore()))
    assert not any("university" in n for n in order), f"reference path: the Erasmus pipeline simply leaves the rule out: {order}"
    source = (HERE / "import_cli.py").read_text(encoding="utf-8")
    assert "legacy_import" not in source, "reference path: import_cli.py uses the pipelines, not the legacy function"


def s8_duplicate_reaching_the_store_is_loud():
    last = pipelines.admissions_pipeline(StudentStore())[-1]
    try:
        last([{"name": "A", "email": "a@tu-sofia.bg", "source": "t"}, {"name": "B", "email": "a@tu-sofia.bg", "source": "t"}])
    except DuplicateStudent:
        return
    raise AssertionError("reference path: the store filter does not swallow DuplicateStudent — a duplicate here is a bug in the order")


SCENARIOS = [
    ("S1", "baseline", "Admissions import stores the 3 valid, unique students", s1_admissions_import_stores_three),
    ("S7", "baseline", "Admissions keeps the right people with the right names (order property)", s7_right_people_with_right_names),
    ("S3", "target", "Erasmus import stores the 2 partner students", s3_erasmus_import_works),
    ("S4", "target", "The stage log accounts for every dropped record", s4_every_dropped_record_is_accounted_for),
    ("S2", "path", "Each pipeline is a list of >= 4 small filters with the same signature", s2_pipelines_are_lists_of_filters),
    ("S5", "path", "Admissions pipeline names normalize before dedupe", s5_order_normalize_before_dedupe),
    ("S6", "path", "Erasmus pipeline omits the university-email filter; CLI no longer uses legacy code", s6_erasmus_composition_and_no_legacy),
    ("S8", "path", "The store filter lets DuplicateStudent through (loud, not silent)", s8_duplicate_reaching_the_store_is_loud),
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
        except NotImplementedError as e:
            ok, msg = False, f"not built yet ({e})"
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
