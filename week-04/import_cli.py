"""Registrar's import tool.

Usage:
    python import_cli.py admissions
    python import_cli.py erasmus
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass


from pathlib import Path

from importer.legacy_import import import_admissions
from importer.store import StudentStore

DATA = Path(__file__).parent / "data"


def run_import(source, store, data_dir=DATA):
    """Import one source file into the store. Returns the number of stored students."""
    if source == "admissions":
        return import_admissions(data_dir / "admissions.csv", store)
    print(f"Source '{source}' is not supported yet.")
    return 0


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 1
    store = StudentStore()
    stored = run_import(argv[0], store)
    for s in store.list_all():
        print(f"{s['id']:>3}  {s['name']:<18} {s['email']:<32} {s['source']}")
    print(f"{stored} students stored")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
