"""Enrollment rules. Course data (capacity) comes from the Catalogue interface."""


class EnrollmentError(Exception):
    """An enrollment request that breaks a business rule."""


class EnrollmentRepository:
    def __init__(self, conn):
        self.conn = conn

    def exists(self, student_id, course_id):
        return self.conn.execute("SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?",
                                 (student_id, course_id)).fetchone() is not None

    def count_for_course(self, course_id):
        return self.conn.execute("SELECT COUNT(*) FROM enrollments WHERE course_id = ?", (course_id,)).fetchone()[0]

    def counts_by_course(self):
        rows = self.conn.execute("SELECT course_id, COUNT(*) AS n FROM enrollments GROUP BY course_id")
        return {r["course_id"]: r["n"] for r in rows}

    def add(self, student_id, course_id):
        self.conn.execute("INSERT INTO enrollments VALUES (?, ?)", (student_id, course_id))
        self.conn.commit()


class EnrollmentService:
    def __init__(self, repository, students, catalog):
        self.repository = repository
        self.students = students
        self.catalog = catalog          # CatalogService or CatalogClient — same interface

    def enroll(self, student_id, course_id):
        if self.students.get_student(student_id) is None:
            raise EnrollmentError(f"Unknown student {student_id}")
        course = self.catalog.get_course(course_id)
        if course is None:
            raise EnrollmentError(f"Unknown course {course_id}")
        if self.repository.exists(student_id, course_id):
            raise EnrollmentError("Student is already enrolled in this course")
        taken = self.repository.count_for_course(course_id)
        if taken >= course["capacity"]:
            raise EnrollmentError(f"{course['code']} is full ({taken}/{course['capacity']})")
        self.repository.add(student_id, course_id)
        return course
