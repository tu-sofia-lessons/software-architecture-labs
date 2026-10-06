"""Business operations on course materials. Knows the MaterialStore contract, not where files live."""
from pathlib import Path

from materials.store import MaterialStore


class MaterialService:
    def __init__(self, store: MaterialStore):
        self.store = store

    @staticmethod
    def _check_name(name):
        # Names come from users (and later from other systems): never trust them as paths.
        if not name or "/" in name or "\\" in name or ".." in name:
            raise ValueError(f"Invalid file name: {name!r}")

    def list_materials(self, course_id):
        return self.store.list(course_id)

    def download(self, course_id, name, dest_dir):
        self._check_name(name)
        data = self.store.read(course_id, name)
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / name).write_bytes(data)
        return dest / name

    def upload(self, course_id, path):
        path = Path(path)
        self._check_name(path.name)
        self.store.write(course_id, path.name, path.read_bytes())
        return path.name
