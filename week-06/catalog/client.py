"""Remote Catalogue: same interface as CatalogService, but over HTTP."""


class CatalogClient:
    """WEEK 06 BUILD: talk to the Catalogue Service (http://127.0.0.1:8101) with httpkit.get_json."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def get_course(self, course_id):
        raise NotImplementedError("Week 06 Build: GET /courses/<id> (None if 404)")

    def list_courses(self):
        raise NotImplementedError("Week 06 Build: GET /courses")
