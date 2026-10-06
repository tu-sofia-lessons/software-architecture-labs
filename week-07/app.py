"""University Platform — monolith using the remote Catalogue Service.

Usage:
    python app.py browse                         # course list (what the public website shows)
    python app.py enroll <student_id> <course_id>
    python app.py list-students | reset
Environment: CATALOG_URL (default http://127.0.0.1:8101), OBS_LOG (log file)
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import os

import db
from catalog.client import CatalogClient
from enrollment.service import EnrollmentError, EnrollmentRepository, EnrollmentService
from httpkit import HttpError, ServiceUnavailable
from students.service import StudentService


class Platform:
    def __init__(self, conn, catalog):
        self.conn = conn
        self.catalog = catalog
        self.students = StudentService(conn)
        self.enrollments = EnrollmentRepository(conn)
        self.enrollment = EnrollmentService(self.enrollments, self.students, catalog)


def build(db_path=None, catalog_url=None) -> Platform:
    url = catalog_url or os.environ.get("CATALOG_URL", "http://127.0.0.1:8101")
    return Platform(db.connect(db_path), CatalogClient(url))


def browse_command(p):
    """Returns (courses, stale). Errors propagate to the caller."""
    return p.catalog.list_courses()


def enroll_command(p, student_id, course_id):
    """Returns (ok, message)."""
    try:
        course = p.enrollment.enroll(student_id, course_id)
    except EnrollmentError as e:
        return False, str(e)
    except (ServiceUnavailable, HttpError) as e:
        return False, f"Catalogue unavailable, enrollment not possible right now ({e})"
    return True, f"Enrolled student {student_id} in {course['code']}"


def main(argv, p=None):
    if not argv:
        print(__doc__)
        return 1
    p = p or build()
    command, args = argv[0], argv[1:]
    if command == "browse":
        try:
            courses, stale = browse_command(p)
        except (ServiceUnavailable, HttpError) as e:
            print(f"Catalogue unavailable and nothing cached in THIS run ({type(e).__name__}).")
            print("Note: every `python app.py ...` is a new process, so an in-memory cache starts empty.")
            return 3
        if stale:
            print("(catalogue unavailable — showing the last known list)")
        for c in courses:
            print(f"{c['id']:>3}  {c['code']}  {c['title']:<25} cap {c['capacity']}")
    elif command == "enroll" and len(args) == 2:
        ok, message = enroll_command(p, int(args[0]), int(args[1]))
        print(("OK: " if ok else "REJECTED: ") + message)
        return 0 if ok else 2
    elif command == "list-students":
        for s in p.students.list_students():
            print(f"{s['id']:>3}  {s['name']}")
    elif command == "reset":
        db.seed(p.conn)
        print("Monolith database reset.")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
