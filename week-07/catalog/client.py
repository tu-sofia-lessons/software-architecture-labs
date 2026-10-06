"""Remote Catalogue: talks to the Catalogue Service over HTTP.

Interface used by the rest of the monolith:
    get_course(course_id) -> dict | None           (None = the course does not exist)
    list_courses()        -> (courses, stale)       stale=True means "served from an old copy"

Provided plumbing: _attempt() does ONE call, sends the request id and logs it.
WEEK 07 BUILD: today every call waits forever (timeout=None), is tried once, has no fallback.
Decide a failure policy PER CALL TYPE and write it in get_course / list_courses (and __init__):
    - the timeout value          - which failures to retry, how many times, with what pause
    - what browse shows when the service is down / slow
    - what enrollment's capacity check does when the service is down / slow
"""
import time

import obs
from httpkit import HttpError, ServiceTimeout, ServiceUnavailable, get_json


class CatalogClient:
    def __init__(self, base_url, timeout=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout                      # None = wait forever

    def _attempt(self, path, op, request_id, attempt):
        """ONE HTTP GET (provided plumbing, not the decision): sends X-Request-Id and logs
        request_id, op, attempt, outcome, latency_ms. Raises exactly what httpkit.get_json raises:
        HttpError (4xx/5xx), ServiceTimeout, ServiceUnavailable."""
        start = time.monotonic()
        outcome = "ok"
        try:
            return get_json(self.base_url + path, timeout=self.timeout, headers={"X-Request-Id": request_id})
        except HttpError as e:
            outcome = f"http_{e.status}"
            raise
        except ServiceTimeout:
            outcome = "timeout"
            raise
        except ServiceUnavailable:
            outcome = "unreachable"
            raise
        finally:
            obs.log("catalog_call", request_id=request_id, op=op, attempt=attempt, outcome=outcome,
                    latency_ms=round((time.monotonic() - start) * 1000))

    def get_course(self, course_id):
        request_id = obs.new_request_id()           # one id per operation, reuse it for every attempt
        try:
            return self._attempt(f"/courses/{course_id}", "get_course", request_id, attempt=1)
        except HttpError as e:
            if e.status == 404:
                return None
            raise

    def list_courses(self):
        request_id = obs.new_request_id()
        return self._attempt("/courses", "list_courses", request_id, attempt=1)["courses"], False
