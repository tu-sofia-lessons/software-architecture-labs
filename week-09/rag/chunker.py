"""Split documents into paragraph chunks (provided). Every chunk keeps its provenance."""


def chunk_documents(documents):
    """Return a list of {source, title, updated, text}, one per paragraph."""
    chunks = []
    for doc in documents:
        for paragraph in doc["text"].split("\n\n"):
            paragraph = " ".join(paragraph.split())
            if paragraph:
                chunks.append({
                    "source": doc["source"],
                    "title": doc["title"],
                    "updated": doc["updated"],
                    "text": paragraph,
                })
    return chunks
