"""Data access for students. SQL about students lives only here."""


class StudentRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, student_id):
        row = self.conn.execute(
            "SELECT id, name, email FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_all(self):
        rows = self.conn.execute("SELECT id, name, email FROM students ORDER BY id")
        return [dict(r) for r in rows]
