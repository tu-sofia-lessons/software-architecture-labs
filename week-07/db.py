"""Monolith database (provided): students + enrollments. Courses live in the Catalogue Service."""
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


def connect(path=None) -> sqlite3.Connection:
    path = path or os.environ.get("UNI_DB") or DEFAULT_DB
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS enrollments (student_id INTEGER, course_id INTEGER)")
    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        seed(conn)
    return conn


def seed(conn) -> None:
    conn.execute("DELETE FROM students")
    conn.execute("DELETE FROM enrollments")
    conn.executemany("INSERT INTO students VALUES (?, ?, ?)", STUDENTS)
    conn.commit()
