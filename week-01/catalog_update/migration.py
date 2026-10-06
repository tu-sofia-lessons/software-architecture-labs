"""Catalogue team, release 2: migration of the courses table (runs once on every database)."""


def migrate(conn):
    columns = [r[1] for r in conn.execute("PRAGMA table_info(courses)")]
    if "code" in columns:
        conn.execute("ALTER TABLE courses RENAME COLUMN code TO course_code")
        conn.commit()
