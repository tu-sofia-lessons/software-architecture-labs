"""Start-of-semester bulk enrollment from a CSV file (student_id,course_id).

Usage:
    python bulk_enroll.py data/bulk.csv
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import csv
import sys

import db


def run(conn, rows):
    """Enroll every row. Returns a list of (row, ok, message)."""
    report = []
    for row in rows:
        student_id, course_id = int(row["student_id"]), int(row["course_id"])

        student = conn.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
        course = conn.execute("SELECT id, code FROM courses WHERE id = ?", (course_id,)).fetchone()
        if student is None or course is None:
            report.append((row, False, "Unknown student or course"))
            continue

        duplicate = conn.execute(
            "SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?",
            (student_id, course_id),
        ).fetchone()
        if duplicate:
            report.append((row, False, "Already enrolled"))
            continue

        conn.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id, course_id))
        report.append((row, True, f"Enrolled student {student_id} in {course['code']}"))
    conn.commit()
    return report


def main(argv, conn=None):
    if len(argv) != 1:
        print(__doc__)
        return 1
    conn = conn or db.connect()
    with open(argv[0], newline="", encoding="utf-8") as f:
        report = run(conn, list(csv.DictReader(f)))
    for row, ok, message in report:
        print(("OK       " if ok else "REJECTED ") + f"{row['student_id']},{row['course_id']}: {message}")
    accepted = sum(1 for _, ok, _ in report if ok)
    print(f"{accepted} accepted, {len(report) - accepted} rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
