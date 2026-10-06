"""Registrar's command-line tool — students (local) and course materials.

Usage:
    python cli.py list-students
    python cli.py materials list <course_id>
    python cli.py materials get  <course_id> <name>      # saved into downloads/
    python cli.py materials put  <course_id> <file_path>

Environment:
    MATERIALS_BACKEND=local|remote   (default local)
    MATERIALS_ROOT   folder for the local backend (default local_materials/)
    MATERIALS_URL    file server for the remote backend (default http://127.0.0.1:8102)
    DOWNLOADS_DIR    where `get` saves files (default downloads/)
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import os
from pathlib import Path

from materials.service import MaterialService
from students import STUDENTS

HERE = Path(__file__).parent


def make_store():
    """Composition root: the only place that knows which MaterialStore implementation is used."""
    if os.environ.get("MATERIALS_BACKEND", "local") == "remote":
        from materials.remote_store import RemoteMaterialStore
        return RemoteMaterialStore(os.environ.get("MATERIALS_URL", "http://127.0.0.1:8102"))
    from materials.local_store import LocalMaterialStore
    return LocalMaterialStore(os.environ.get("MATERIALS_ROOT", HERE / "local_materials"))


def materials_command(args):
    service = MaterialService(make_store())
    action, course_id = args[0], int(args[1])
    if action == "list":
        for name in service.list_materials(course_id):
            print(name)
    elif action == "get":
        saved = service.download(course_id, args[2], os.environ.get("DOWNLOADS_DIR", HERE / "downloads"))
        print(f"Saved {saved}")
    elif action == "put":
        print(f"Uploaded {service.upload(course_id, args[2])}")
    # WEEK 03 BUILD: what should the user see when the materials storage fails?
    return 0


def main(argv):
    if argv[:1] == ["list-students"]:
        for s in STUDENTS:
            print(f"{s['id']:>3}  {s['name']:<18} {s['email']}")
        return 0
    if argv[:1] == ["materials"] and len(argv) >= 3:
        return materials_command(argv[1:])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
