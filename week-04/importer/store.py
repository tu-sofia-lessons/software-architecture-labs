"""The student store the import writes into (provided — stands in for the Students module)."""


class DuplicateStudent(Exception):
    """A student with this e-mail already exists."""


class StudentStore:
    def __init__(self):
        self.students = []

    def add(self, name, email, source):
        if any(s["email"] == email for s in self.students):
            raise DuplicateStudent(email)
        student = {"id": len(self.students) + 1, "name": name, "email": email, "source": source}
        self.students.append(student)
        return student

    def list_all(self):
        return list(self.students)
