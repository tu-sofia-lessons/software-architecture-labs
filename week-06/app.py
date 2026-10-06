"""University Platform (modular monolith) — command line.

Usage:
    python app.py list-students | list-courses | fill-report | reset
    python app.py enroll <student_id> <course_id>

Environment:
    CATALOG=local|remote   where course data comes from (default local)
    CATALOG_URL            Catalogue Service address (default http://127.0.0.1:8101)
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
import reports
from catalog.repository import CatalogRepository
from catalog.service import CatalogService
from enrollment.service import EnrollmentError, EnrollmentRepository, EnrollmentService
from httpkit import HttpError, ServiceUnavailable
from students.service import StudentService


class Platform:
    """Composition root: holds the wired components."""

    def __init__(self, mode, conn, catalog):
        self.mode = mode
        self.conn = conn
        self.catalog = catalog
        self.students = StudentService(conn)
        self.enrollments = EnrollmentRepository(conn)
        self.enrollment = EnrollmentService(self.enrollments, self.students, catalog)


def build(mode=None, db_path=None, catalog_url=None) -> Platform:
    mode = mode or os.environ.get("CATALOG", "local")
    catalog_url = catalog_url or os.environ.get("CATALOG_URL", "http://127.0.0.1:8101")
    if mode == "local":
        conn = db.connect(db_path, with_courses=True)
        return Platform(mode, conn, CatalogService(CatalogRepository(conn)))
    # WEEK 06 BUILD: remote mode — the monolith no longer owns course data.
    raise NotImplementedError("Week 06 Build: wire CATALOG=remote")


def enroll_command(p, student_id, course_id):
    """Returns (ok, message)."""
    try:
        course = p.enrollment.enroll(student_id, course_id)
    except EnrollmentError as e:
        return False, str(e)
    except (ServiceUnavailable, HttpError) as e:
        return False, f"Catalogue unavailable, try again later ({e})"
    return True, f"Enrolled student {student_id} in {course['code']}"


def main(argv, p=None):
    if not argv:
        print(__doc__)
        return 1
    p = p or build()
    command, args = argv[0], argv[1:]
    if command == "list-students":
        for s in p.students.list_students():
            print(f"{s['id']:>3}  {s['name']}")
    elif command == "list-courses":
        for c in p.catalog.list_courses():
            print(f"{c['id']:>3}  {c['code']}  {c['title']:<25} cap {c['capacity']}")
    elif command == "enroll" and len(args) == 2:
        ok, message = enroll_command(p, int(args[0]), int(args[1]))
        print(("OK: " if ok else "REJECTED: ") + message)
        return 0 if ok else 2
    elif command == "fill-report":
        for line in reports.fill_report(p):
            print(line)
    elif command == "reset":
        db.seed(p.conn)
        print("Monolith database reset.")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
