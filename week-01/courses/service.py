"""Business operations on courses."""
from courses.repository import CourseRepository


class CourseService:
    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def get_course(self, course_id):
        return self.repository.get(course_id)

    def list_courses(self):
        return self.repository.list_all()
