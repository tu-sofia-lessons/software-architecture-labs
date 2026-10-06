"""Two Registrar clerks press "Enroll" at the same moment (provided).

AI201 has 2 seats. Maria already holds one. Clerk A enrolls Ivan and clerk B enrolls Georgi,
each from their own computer (their own database connection), in the same second.

To make "the same second" repeatable, the two clerks are synchronised at one point only:
each clerk's program is held just before it writes the enrollment (INSERT INTO enrollments)
until the other clerk has reached that point too. Everything else runs normally.

    python race.py
"""
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

import cli
import db

COURSE = 2                       # AI201, capacity 2
ALREADY_ENROLLED = 1             # Maria
CLERKS = {"A": 2, "B": 3}        # clerk -> student (Ivan, Georgi)


class _HeldBeforeWrite:
    """A database connection that waits for the other clerk right before writing an enrollment."""

    def __init__(self, conn, barrier):
        self._conn = conn
        self._barrier = barrier

    def execute(self, sql, *params):
        if sql.lstrip().upper().startswith("INSERT INTO ENROLLMENTS"):
            try:
                self._barrier.wait(timeout=3)
            except threading.BrokenBarrierError:
                pass                                   # the other clerk never got this far: go on
        return self._conn.execute(sql, *params)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def run(path):
    """Run the race on the database at `path`. Returns {clerk: (ok, message)} and the seat count."""
    conn = db.connect(path)
    conn.execute("DELETE FROM enrollments")
    conn.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (ALREADY_ENROLLED, COURSE))
    conn.commit()

    barrier = threading.Barrier(len(CLERKS))
    results = {}

    def clerk(name, student_id):
        own = sqlite3.connect(path, timeout=10)
        own.row_factory = sqlite3.Row
        try:
            results[name] = cli.enroll_command(_HeldBeforeWrite(own, barrier), student_id, COURSE)
        except Exception as e:                         # a crash is also an answer the clerk sees
            results[name] = ("CRASH", f"{type(e).__name__}: {e}")
        finally:
            own.close()

    threads = [threading.Thread(target=clerk, args=item) for item in CLERKS.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    seats = conn.execute("SELECT COUNT(*) FROM enrollments WHERE course_id = ?", (COURSE,)).fetchone()[0]
    capacity = conn.execute("SELECT capacity FROM courses WHERE id = ?", (COURSE,)).fetchone()[0]
    return results, seats, capacity


if __name__ == "__main__":
    path = Path(tempfile.mkdtemp()) / "race.db"
    results, seats, capacity = run(path)
    for name in sorted(results):
        ok, message = results[name]
        print(f"clerk {name}: {'OK' if ok is True else 'REJECTED' if ok is False else ok}  {message}")
    print(f"AI201: {seats} students, capacity {capacity}" + ("   <-- OVERBOOKED" if seats > capacity else ""))
    sys.exit(0 if seats <= capacity else 1)
