"""Data access for courses. SQL about courses lives only here."""


class CourseRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, course_id):
        row = self.conn.execute(
            "SELECT id, code, title, teacher, capacity FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_all(self):
        rows = self.conn.execute("SELECT id, code, title, teacher, capacity FROM courses ORDER BY id")
        return [dict(r) for r in rows]
