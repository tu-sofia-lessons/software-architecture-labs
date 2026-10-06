"""Student portal: online enrollment (written by the portal team, handed over to us).

The portal's web page calls enroll_request(conn, student_id, course_id) and shows the message.

    python portal.py <student_id> <course_id>
"""
import sys

import db


def enroll_request(conn, student_id, course_id):
    """Enroll the logged-in student. Returns (ok, message) for the web page."""
    conn.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id, course_id))
    conn.commit()
    return True, f"Enrolled student {student_id} in course {course_id}"


if __name__ == "__main__":
    ok, message = enroll_request(db.connect(), int(sys.argv[1]), int(sys.argv[2]))
    print(("OK: " if ok else "REJECTED: ") + message)
