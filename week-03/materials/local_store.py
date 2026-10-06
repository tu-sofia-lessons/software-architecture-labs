"""MaterialStore on the local disk: local_materials/course_<id>/<name>."""
from pathlib import Path


class LocalMaterialStore:
    def __init__(self, root):
        self.root = Path(root)

    def _folder(self, course_id):
        return self.root / f"course_{course_id}"

    def list(self, course_id):
        folder = self._folder(course_id)
        return sorted(p.name for p in folder.iterdir() if p.is_file()) if folder.exists() else []

    def read(self, course_id, name):
        return (self._folder(course_id) / name).read_bytes()

    def write(self, course_id, name, data):
        folder = self._folder(course_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(data)
