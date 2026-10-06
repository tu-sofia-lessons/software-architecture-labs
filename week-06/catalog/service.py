"""The Catalogue interface the rest of the monolith uses."""
from catalog.repository import CatalogRepository


class CatalogService:
    def __init__(self, repository: CatalogRepository):
        self.repository = repository

    def get_course(self, course_id):
        """Return the course as a dict, or None if it does not exist."""
        return self.repository.get(course_id)

    def list_courses(self):
        return self.repository.list_all()
