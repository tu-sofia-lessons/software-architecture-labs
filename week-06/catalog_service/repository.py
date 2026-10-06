"""Data access for courses. SQL about courses lives only here."""

COLUMNS = "id, code, title, teacher, capacity"


class CatalogRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, course_id):
        row = self.conn.execute(f"SELECT {COLUMNS} FROM courses WHERE id = ?", (course_id,)).fetchone()
        return dict(row) if row else None

    def list_all(self):
        return [dict(r) for r in self.conn.execute(f"SELECT {COLUMNS} FROM courses ORDER BY id")]
