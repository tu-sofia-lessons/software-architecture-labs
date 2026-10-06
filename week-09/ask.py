"""Ask the University Assistant.

Usage:
    python ask.py "What do I need to pass Software Architecture?"            # RAG (after the Build)
    python ask.py "What do I need to pass Software Architecture?" --mode llm # LLM only
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass


import llm_client
from rag.assistant import ask


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    mode = "llm" if "--mode" in argv and argv[argv.index("--mode") + 1] == "llm" else "rag"
    question = next(a for a in argv if not a.startswith("--") and a not in ("llm", "rag"))
    try:
        answer, sources = ask(question, mode=mode)
    except NotImplementedError as e:
        print(f"RAG mode is not built yet ({e}). Try --mode llm.")
        return 2
    print(f"[{mode}] {answer}")
    if sources:
        print("Sources:", ", ".join(sources))
    print(f"(LLM calls: {llm_client.CALLS['count']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
