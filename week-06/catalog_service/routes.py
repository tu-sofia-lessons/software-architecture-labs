"""HTTP routes of the Catalogue Service. It reads ONLY its own database (catalog_service/db.py).

Each route is (method, regex, handler). The regex must match the WHOLE path.
A handler receives a request (request.params holds the named groups of the regex)
and returns (status, dict) — see httpkit.py.
"""
from db import connect
from repository import CatalogRepository


def list_courses(request):
    """GET /courses — provided as an example."""
    return 200, {"courses": CatalogRepository(connect()).list_all()}


# WEEK 06 BUILD: GET /courses/<id>  ->  200 {course}  or  404 {"error": ...}
#   A named group puts part of the path into request.params, e.g.
#   r"^/courses/(?P<id>\d+)$"   ->   request.params["id"] == "1"   (a string!)

ROUTES = [
    ("GET", r"^/courses$", list_courses),
]
