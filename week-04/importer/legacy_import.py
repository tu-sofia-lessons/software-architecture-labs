"""The original admissions import: one function that does everything."""
from importer.sources import read_csv
from importer.store import DuplicateStudent


def import_admissions(path, store):
    """Read, check, clean, de-duplicate and store admitted students. Returns how many were stored."""
    rows = read_csv(path)
    stored = 0
    seen = set()
    for row in rows:
        name = row.get("name") or ""
        email = row.get("email") or ""
        if not name.strip() or not email.strip():
            continue
        name = " ".join(name.split())
        email = email.strip().lower()
        if not email.endswith("@tu-sofia.bg"):
            continue
        if email in seen:
            continue
        seen.add(email)
        try:
            store.add(name, email, "admissions")
            stored += 1
        except DuplicateStudent:
            continue
    return stored
