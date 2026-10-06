"""The Catalogue Service's OWN database: catalog_service/data/catalog.db (provided)."""
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "data" / "catalog.db"

COURSES = [
    (1, "SA101", "Software Architecture", "Prof. Stoyanova", 3),
    (2, "AI201", "Artificial Intelligence", "Prof. Kolev", 2),
    (3, "DB150", "Databases", "Dr. Marinov", 30),
    (4, "PR102", "Programming 2", "Dr. Petkova", 30),
]


def connect() -> sqlite3.Connection:
    """Open catalog.db (CATALOG_DB env var overrides the path); seed it on first use."""
    path = os.environ.get("CATALOG_DB") or DEFAULT_DB
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, code TEXT, "
                 "title TEXT, teacher TEXT, capacity INTEGER)")
    if conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        conn.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?)", COURSES)
        conn.commit()
    return conn
