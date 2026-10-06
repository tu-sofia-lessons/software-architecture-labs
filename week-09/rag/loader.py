"""Load knowledge documents (provided). Each file starts with 'Title:' and 'Updated:' lines."""
from pathlib import Path


def load_documents(folder):
    """Return a list of {source, title, updated, text} for every .txt file in folder."""
    documents = []
    for path in sorted(Path(folder).glob("*.txt")):
        header, _, body = path.read_text(encoding="utf-8").partition("\n\n")
        meta = {}
        for line in header.splitlines():
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
        documents.append({
            "source": path.name,
            "title": meta.get("title", path.stem),
            "updated": meta.get("updated", "unknown"),
            "text": body.strip(),
        })
    return documents
