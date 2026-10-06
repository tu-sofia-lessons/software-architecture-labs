"""Database access helpers and seed data (provided — not part of the lesson)."""
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "data" / "university.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
    teacher TEXT NOT NULL, capacity INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS enrollments (
    student_id INTEGER NOT NULL, course_id INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS completed_courses (
    student_id INTEGER NOT NULL, course_id INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS prerequisites (
    course_id INTEGER NOT NULL, required_course_id INTEGER NOT NULL);
"""

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
COMPLETED = [(1, 4), (2, 4)]          # Maria and Ivan completed Programming 2
PREREQUISITES = [(1, 4)]              # SA101 requires PR102


def connect(path=None) -> sqlite3.Connection:
    """Open the database (UNI_DB env var or data/university.db)."""
    path = path or os.environ.get("UNI_DB") or DEFAULT_DB
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        seed(conn)
    return conn


def seed(conn: sqlite3.Connection) -> None:
    """Reset all tables to the reference seed data."""
    for table in ("students", "courses", "enrollments", "completed_courses", "prerequisites"):
        conn.execute(f"DELETE FROM {table}")
    conn.executemany("INSERT INTO students VALUES (?, ?, ?)", STUDENTS)
    conn.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?)", COURSES)
    conn.executemany("INSERT INTO completed_courses VALUES (?, ?)", COMPLETED)
    conn.executemany("INSERT INTO prerequisites VALUES (?, ?)", PREREQUISITES)
    conn.commit()
