"""Registrar's command-line tool.

Usage:
    python cli.py list-students
    python cli.py list-courses
    python cli.py enroll <student_id> <course_id>
    python cli.py roster <course_id>
    python cli.py reset
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import sys

import db
from courses.repository import CourseRepository
from courses.service import CourseService
from students.repository import StudentRepository
from students.service import StudentService


def enroll_command(conn, student_id, course_id):
    """Enroll one student. Returns (ok, message)."""
    students = StudentService(StudentRepository(conn))
    courses = CourseService(CourseRepository(conn))

    if students.get_student(student_id) is None:
        return False, f"Unknown student {student_id}"
    course = courses.get_course(course_id)
    if course is None:
        return False, f"Unknown course {course_id}"

    already = conn.execute(
        "SELECT COUNT(*) FROM enrollments WHERE student_id = ? AND course_id = ?",
        (student_id, course_id),
    ).fetchone()[0]
    if already:
        return False, "Student is already enrolled in this course"

    taken = conn.execute(
        "SELECT COUNT(*) FROM enrollments WHERE course_id = ?", (course_id,)
    ).fetchone()[0]
    if taken >= course["capacity"]:
        return False, f"{course['code']} is full ({taken}/{course['capacity']})"

    conn.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id, course_id))
    conn.commit()
    return True, f"Enrolled student {student_id} in {course['code']}"


def roster_command(conn, course_id):
    """Return the names of the students enrolled in a course."""
    rows = conn.execute(
        "SELECT s.name FROM enrollments e JOIN students s ON s.id = e.student_id "
        "WHERE e.course_id = ? ORDER BY s.name",
        (course_id,),
    )
    return [r["name"] for r in rows]


def main(argv, conn=None):
    conn = conn or db.connect()
    if not argv:
        print(__doc__)
        return 1
    command, args = argv[0], argv[1:]

    if command == "list-students":
        for s in StudentService(StudentRepository(conn)).list_students():
            print(f"{s['id']:>3}  {s['name']:<18} {s['email']}")
    elif command == "list-courses":
        for c in CourseService(CourseRepository(conn)).list_courses():
            print(f"{c['id']:>3}  {c['code']}  {c['title']:<25} cap {c['capacity']}")
    elif command == "enroll" and len(args) == 2:
        ok, message = enroll_command(conn, int(args[0]), int(args[1]))
        print(("OK: " if ok else "REJECTED: ") + message)
        return 0 if ok else 2
    elif command == "roster" and len(args) == 1:
        for name in roster_command(conn, int(args[0])):
            print(name)
    elif command == "reset":
        db.seed(conn)
        print("Database reset to seed data.")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
