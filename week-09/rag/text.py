"""Tiny text helpers for retrieval (provided)."""
import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is", "are", "be", "do",
    "does", "i", "me", "my", "we", "you", "what", "which", "who", "how", "when", "where",
    "can", "at", "by", "with", "from", "it", "this", "that", "there", "as", "have", "has",
}


def tokenize(text):
    """Lower-case words without stop words, as a set."""
    return {w for w in re.findall(r"\w+", text.lower()) if w not in STOPWORDS}
