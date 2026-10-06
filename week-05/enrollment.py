"""Enrollment: decides whether a student may enroll, records it, and triggers the reactions."""


class EnrollmentError(Exception):
    """An enrollment request that breaks a business rule."""


class EnrollmentService:
    def __init__(self, students, courses, mailer, audit, stats):
        self.students = students
        self.courses = courses
        self.enrollments = set()        # (student_id, course_id)
        self.mailer = mailer
        self.audit = audit
        self.stats = stats

    def enroll(self, student_id, course_id):
        student = self.students.get(student_id)
        course = self.courses.get(course_id)
        if student is None or course is None:
            raise EnrollmentError("Unknown student or course")
        if (student_id, course_id) in self.enrollments:
            raise EnrollmentError("Student is already enrolled in this course")
        taken = sum(1 for _, c in self.enrollments if c == course_id)
        if taken >= course["capacity"]:
            raise EnrollmentError(f"{course['code']} is full")

        self.enrollments.add((student_id, course_id))

        # Reactions to a new enrollment — every new team adds a line here.
        self.mailer.send(student["email"], f"Enrolled in {course['code']}",
                         f"Dear {student['name']}, you are enrolled in {course['title']}.")
        self.audit.record("student.enrolled", student_id=student_id, course_id=course_id)
        self.stats.increment(course_id)
