"""Platform API — used by the admin tools and, from now on, the student mobile app.

Run:  python api.py        (listens on http://127.0.0.1:8103)
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import config
import errors
import service
from httpkit import HttpError, serve


def caller(request):
    """Who is calling? The mobile app sends the logged-in user's name in X-User."""
    return request.headers.get("X-User", "anonymous")


def run_service(operation, *args):
    """Call the application layer and translate its errors into HTTP statuses."""
    try:
        return operation(*args)
    except service.NotFound as e:
        raise HttpError(404, str(e))
    except service.Conflict as e:
        raise HttpError(409, str(e))
    except errors.Forbidden as e:
        raise HttpError(403, str(e))
    except (ValueError, KeyError, TypeError) as e:
        raise HttpError(400, f"bad request: {e}")


def health(request):
    return 200, {"status": "ok"}


def student_grades(request):
    student_id = int(request.params[0])
    print(f"  caller={caller(request)}", flush=True)
    return 200, {"student_id": student_id, "grades": run_service(service.grades_of_student, student_id)}


def course_grades(request):
    course_id = int(request.params[0])
    print(f"  caller={caller(request)}", flush=True)
    return 200, {"course_id": course_id, "grades": run_service(service.course_gradebook, course_id)}


def post_grade(request):
    body = request.body or {}
    print(f"  caller={caller(request)}", flush=True)
    run_service(service.submit_grade, body.get("student_id"), body.get("course_id"), body.get("grade"))
    return 201, {"status": "grade recorded"}


def post_enrollment(request):
    body = request.body or {}
    print(f"  caller={caller(request)}", flush=True)
    run_service(service.enroll, body.get("student_id"), body.get("course_id"))
    return 201, {"status": "enrolled"}


ROUTES = [
    ("GET", r"/health", health),
    ("GET", r"/students/(\d+)/grades", student_grades),
    ("GET", r"/courses/(\d+)/grades", course_grades),
    ("POST", r"/grades", post_grade),
    ("POST", r"/enrollments", post_enrollment),
]


if __name__ == "__main__":
    serve(ROUTES, config.PORT)
