"""MaterialStore backed by the faculty file server (HTTP). See file_server.py for its API."""
import http_util  # noqa: F401  (provided helpers: get_json, get_bytes, put_bytes)


class RemoteMaterialStore:
    def __init__(self, base_url, timeout=2.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # WEEK 03 BUILD: implement list / read / write by calling the file server,
    # and decide what the caller sees when the server is down, slow, or says 404.
    def list(self, course_id):
        raise NotImplementedError("Week 03 Build: RemoteMaterialStore.list")

    def read(self, course_id, name):
        raise NotImplementedError("Week 03 Build: RemoteMaterialStore.read")

    def write(self, course_id, name, data):
        raise NotImplementedError("Week 03 Build: RemoteMaterialStore.write")
