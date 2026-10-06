"""Monolith database (provided). One file: data/university.db."""
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "data" / "university.db"

STUDENTS = [
    (1, "Maria Ivanova", "maria.ivanova@tu-sofia.bg"),
    (2, "Ivan Petrov", "ivan.petrov@tu-sofia.bg"),
    (3, "Georgi Georgiev", "georgi.georgiev@tu-sofia.bg"),
    (4, "Elena Dimitrova", "elena.dimitrova@tu-sofia.bg"),
]
COURSES = [
    (1, "SA101", "Software Architecture", "Prof. Stoyanova", 3),
    (2, "AI201", "Artificial Intelligence", "Prof. Kolev", 2),
    (3, "DB150", "Databases", "Dr. Marinov", 30),
    (4, "PR102", "Programming 2", "Dr. Petkova", 30),
]


def connect(path=None, with_courses=True) -> sqlite3.Connection:
    """Open the monolith DB. with_courses=False: the courses table is not ours any more."""
    path = path or os.environ.get("UNI_DB") or DEFAULT_DB
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS enrollments (student_id INTEGER, course_id INTEGER)")
    if with_courses:
        conn.execute("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, code TEXT, "
                     "title TEXT, teacher TEXT, capacity INTEGER)")
    else:
        conn.execute("DROP TABLE IF EXISTS courses")    # remote mode: a stale copy would silently be used
        conn.commit()
    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        seed(conn)
    return conn


def seed(conn) -> None:
    """Reset the tables this database has to the reference seed data."""
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for table in tables:
        conn.execute(f"DELETE FROM {table}")
    conn.executemany("INSERT INTO students VALUES (?, ?, ?)", STUDENTS)
    if "courses" in tables:
        conn.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?)", COURSES)
    conn.commit()
