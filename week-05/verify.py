"""Acceptance scenarios for Week 5.  Run:  python verify.py   (add --punch after the Second Punch is released)

Keep app.build(mode) returning a namespace with service, bus, mailer, audit, stats:
these scenarios call it.
REQ lines ([PASS]/[FAIL]) are graded. [path] lines are hints along the reference path only.
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass


import dataclasses
import io
import traceback
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import app  # noqa: E402
import events  # noqa: E402


def enrolled_event_type():
    assert hasattr(events, "StudentEnrolled"), "events.StudentEnrolled is not defined yet"
    return events.StudentEnrolled


# ---------------------------------------------------------------- baseline (REQ)
def s1_enroll_triggers_all_reactions():
    a = app.build()
    a.service.enroll(1, 3)
    a.bus.drain()
    assert (1, 3) in a.service.enrollments, "enrollment not stored"
    assert len(a.mailer.outbox) == 1, "the student should get one e-mail"
    assert len(a.audit.records) == 1, "one audit record expected"
    assert a.stats.enrollments_per_course.get(3) == 1, "statistics not updated"


def s2_duplicate_rejected():
    a = app.build()
    a.service.enroll(1, 3)
    try:
        a.service.enroll(1, 3)
    except Exception:
        return
    raise AssertionError("a duplicate enrollment must be rejected")


# ---------------------------------------------------------------- target (REQ)
def s3_mail_down_does_not_block_enrollment():
    a = app.build()
    a.mailer.down = True
    try:
        a.service.enroll(1, 3)
    except Exception as e:
        raise AssertionError(f"enrollment failed because the mail server is down ({type(e).__name__})")
    a.bus.drain()
    assert (1, 3) in a.service.enrollments, "enrollment not stored"
    assert len(a.audit.records) == 1, "the audit record must still be written"


def s4_no_enrollment_without_audit():           # the legal constraint
    a = app.build()
    a.audit.down = True
    try:
        a.service.enroll(1, 3)
    except Exception:
        pass
    assert (1, 3) not in a.service.enrollments, \
        "an enrollment was stored without an audit record (compliance violation)"


def s5_producer_reaches_mail_only_through_events():   # behavioural decoupling probe
    a = app.build()
    a.bus.handlers.clear()                    # nobody is listening any more
    a.service.enroll(1, 3)
    a.bus.drain()
    assert a.mailer.outbox == [], ("with no subscribers the student still got an e-mail: "
                                   "the enrollment code reaches the mailer directly")


def s6_new_subscriber_needs_no_producer_change():
    event_type = enrolled_event_type()
    a = app.build()
    received = []
    a.bus.subscribe(event_type, received.append)
    a.service.enroll(2, 4)
    a.bus.drain()
    assert len(received) == 1, "a new subscriber did not receive StudentEnrolled"
    assert (received[0].student_id, received[0].course_id) == (2, 4), "event carries the wrong ids"


# ---------------------------------------------------------------- reference path (guidance, not graded)
def s7_event_is_immutable():
    event_type = enrolled_event_type()
    a = app.build()
    a.service.enroll(1, 3)
    event = a.bus.published[-1]
    assert isinstance(event, event_type), "publish a StudentEnrolled event"
    try:
        event.course_id = 99
    except (dataclasses.FrozenInstanceError, AttributeError):
        return
    raise AssertionError("reference path: events describe facts that happened — a frozen dataclass")


def s8_failure_visible_in_bus_errors():
    a = app.build()
    a.mailer.down = True
    a.service.enroll(1, 3)
    a.bus.drain()
    assert a.bus.errors, "reference path: a failed reaction is recorded in bus.errors"


def s9_stats_is_a_subscriber():
    a = app.build()
    a.bus.handlers.clear()
    a.service.enroll(1, 3)
    a.bus.drain()
    assert not a.stats.enrollments_per_course, \
        "reference path: statistics reacts to the event (you kept it direct — fine if your ADR argues it)"


SCENARIOS = [
    ("S1", "baseline", "An enrollment triggers mail, audit and statistics", s1_enroll_triggers_all_reactions),
    ("S2", "baseline", "A duplicate enrollment is rejected", s2_duplicate_rejected),
    ("S3", "target", "Mail server down: enrollment still succeeds and the audit record is written", s3_mail_down_does_not_block_enrollment),
    ("S4", "target", "Audit store down: no enrollment is stored without an audit record", s4_no_enrollment_without_audit),
    ("S5", "target", "With no subscribers, the enrollment sends no e-mail (the producer does not call the mailer)", s5_producer_reaches_mail_only_through_events),
    ("S6", "target", "A new subscriber receives StudentEnrolled without changing the producer", s6_new_subscriber_needs_no_producer_change),
    ("S7", "path", "The StudentEnrolled event is immutable", s7_event_is_immutable),
    ("S8", "path", "A failed reaction is visible in bus.errors", s8_failure_visible_in_bus_errors),
    ("S9", "path", "Statistics reacts to the event instead of a direct call", s9_stats_is_a_subscriber),
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
