"""Business operations on students."""
from students.repository import StudentRepository


class StudentService:
    def __init__(self, repository: StudentRepository):
        self.repository = repository

    def get_student(self, student_id):
        return self.repository.get(student_id)

    def list_students(self):
        return self.repository.list_all()
