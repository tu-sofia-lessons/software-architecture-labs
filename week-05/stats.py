"""Enrollment statistics for the Dean's Office (provided)."""


class Statistics:
    def __init__(self):
        self.enrollments_per_course = {}

    def increment(self, course_id):
        self.enrollments_per_course[course_id] = self.enrollments_per_course.get(course_id, 0) + 1
