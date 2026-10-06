"""Find the chunks that are relevant to a question."""


def retrieve(question, chunks, top_k=3, min_score=2):
    """Return up to top_k chunks, best first, each scoring at least min_score."""
    # WEEK 09 BUILD: score every chunk (word overlap with the question, see rag/text.py),
    # keep the ones with score >= min_score, return the best top_k.
    raise NotImplementedError("Week 09 Build: implement retrieve()")
