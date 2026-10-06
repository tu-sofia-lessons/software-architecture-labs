"""Composition root + a tiny demo CLI.

Usage:
    python app.py enroll <student_id> <course_id> [<student_id> <course_id> ...]
    MAIL_DOWN=1 python app.py enroll 1 3          # the mail server is down
    python app.py enroll 1 3 --async               # handlers run on a worker thread
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass


from types import SimpleNamespace

import data
from audit import AuditLog
from enrollment import EnrollmentService
from eventbus import EventBus
from mailer import Mailer
from stats import Statistics


def build(mode="sync"):
    """Create and wire all components. Returns them in one namespace."""
    bus = EventBus(mode)
    mailer, audit, stats = Mailer(), AuditLog(), Statistics()
    service = EnrollmentService(data.STUDENTS, data.COURSES, mailer, audit, stats)
    return SimpleNamespace(service=service, bus=bus, mailer=mailer, audit=audit, stats=stats)


def main(argv):
    mode = "async" if "--async" in argv else "sync"
    argv = [a for a in argv if a != "--async"]
    if len(argv) < 3 or argv[0] != "enroll" or len(argv) % 2 == 0:
        print(__doc__)
        return 1
    app = build(mode)
    pairs = [(int(argv[i]), int(argv[i + 1])) for i in range(1, len(argv), 2)]
    for student_id, course_id in pairs:
        try:
            app.service.enroll(student_id, course_id)
            print(f"OK       student {student_id} -> course {course_id}")
        except Exception as e:
            print(f"FAILED   student {student_id} -> course {course_id}: {type(e).__name__}: {e}")
    app.bus.drain()
    print(f"\nenrollments : {sorted(app.service.enrollments)}")
    print(f"mails sent  : {len(app.mailer.outbox)}")
    print(f"audit       : {len(app.audit.records)} records")
    print(f"statistics  : {app.stats.enrollments_per_course}")
    print(f"bus errors  : {[(name, type(exc).__name__) for name, _, exc in app.bus.errors]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
