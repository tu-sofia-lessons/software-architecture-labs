"""Students: repository and service in one small file."""


class StudentService:
    def __init__(self, conn):
        self.conn = conn

    def get_student(self, student_id):
        row = self.conn.execute("SELECT id, name, email FROM students WHERE id = ?", (student_id,)).fetchone()
        return dict(row) if row else None

    def list_students(self):
        return [dict(r) for r in self.conn.execute("SELECT id, name, email FROM students ORDER BY id")]
