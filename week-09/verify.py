"""Acceptance scenarios for Week 9.  Run:  python verify.py   (add --punch for the Second Punch)

REQ scenarios check the requirements and are graded. PATH scenarios are hints about the reference path.
Always uses the offline fake LLM. Keep the signature ask(question, mode, knowledge_dir, llm) -> (answer, sources).
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import io
import os
import re
import shutil
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

os.environ["LLM_BACKEND"] = "fake"
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import llm_client  # noqa: E402
from rag.assistant import KNOWLEDGE, ask  # noqa: E402
from rag.chunker import chunk_documents  # noqa: E402
from rag.loader import load_documents  # noqa: E402
from rag.retriever import retrieve  # noqa: E402

PASS_Q = "What do I need to pass Software Architecture?"
UNANSWERABLE = ("Who is the rector of the university?", "What is the parking fee for students?")
NO_INFO = re.compile(   # any clear "the documents don't have this" wording, EN or BG (the given REFUSAL matches)
    r"(do|does|did) ?n[o']t contain|not (in|found in|covered by|covered in) (the|our) (university |official )?documents"
    r"|(could not|cannot|can't|couldn't) find .{0,40}documents|no information"
    r"|не съдърж|няма информация|няма отговор", re.I)
PUNCH_FILES = {"software_architecture_update.txt"}   # the Second Punch document never counts for S-scenarios


class CountingLLM:
    """Wraps a model and counts calls, so we can see whether the model was used at all."""
    def __init__(self, inner=None):
        self.inner = inner or llm_client.fake_llm
        self.calls = 0

    def __call__(self, prompt):
        self.calls += 1
        return self.inner(prompt)


def hallucinating_llm(prompt):
    """A confident model: answers from the context when it clearly has it, otherwise invents a rule."""
    if "CONTEXT:" in prompt and "70%" in prompt:
        return llm_client.fake_llm(prompt)
    return "Students pay a parking fee of 50 EUR per semester, set by the Rector, Prof. Ivanov."


def knowledge_copy(*extra_files):
    """A private copy of the documents (without the punch file), plus extra (name, text) documents."""
    folder = Path(tempfile.mkdtemp()) / "knowledge"
    shutil.copytree(KNOWLEDGE, folder, ignore=lambda d, names: [n for n in names if n in PUNCH_FILES])
    for name, text in extra_files:
        (folder / name).write_text(text, encoding="utf-8")
    return folder


# ---------------------------------------------------------------- baseline (REQ)
def s1_llm_only_answers_confidently_but_wrong():
    answer, sources = ask(PASS_Q, mode="llm", llm=CountingLLM())
    assert answer and not sources, "LLM-only mode should answer without sources"
    assert "50%" in answer and "70%" not in answer, "the fake model should invent its numbers here"


def s2_chunks_keep_provenance():
    chunks = chunk_documents(load_documents(KNOWLEDGE))
    assert len(chunks) >= 10, "expected paragraph chunks from 5 documents"
    assert all(c["source"].endswith(".txt") and c["updated"] for c in chunks), "every chunk needs source + updated"


# ---------------------------------------------------------------- target (REQ)
def s3_rag_answer_is_grounded_and_cited():
    answer, sources = ask(PASS_Q, knowledge_dir=knowledge_copy(), llm=CountingLLM())
    assert "70%" in answer and "3.00" in answer, f"answer not grounded in the documents: {answer!r}"
    assert "software_architecture.txt" in sources, f"sources should name the document, got {sources}"


def s4_never_presents_invented_rules():
    """Student Office: when the documents have no evidence, an invented rule must never reach a student.
    Tested with a model that invents. NOTE: this covers only questions WITHOUT retrieved evidence; with
    retrieved context a model can still distort it (see the student guide, 'Why' box)."""
    for question in UNANSWERABLE:
        answer, sources = ask(question, knowledge_dir=knowledge_copy(), llm=hallucinating_llm)
        assert "50 EUR" not in answer and "Ivanov" not in answer, \
            f"{question!r}: invented content reached the student: {answer!r}"
        assert not sources, f"{question!r}: an unsupported answer must not cite sources: {sources}"
        assert NO_INFO.search(answer), f"{question!r}: the student must be told the documents have no answer: {answer!r}"


def s5_new_knowledge_without_code_change():
    folder = knowledge_copy(("library.txt", "Title: Library\nUpdated: 2026-03-01\n\n"
                             "Students can borrow up to 5 books from the University Library for 30 days.\n"))
    answer, sources = ask("How many books can I borrow from the library?", knowledge_dir=folder, llm=CountingLLM())
    assert "5 books" in answer and "library.txt" in sources, f"new document not used: {answer!r}"


def s6_model_is_swappable():
    answer, _ = ask(PASS_Q, knowledge_dir=knowledge_copy(),
                    llm=lambda prompt: "stub answer [software_architecture.txt | updated 2026-02-01]")
    assert "stub answer" in answer, "ask() must use the llm it is given (the model boundary), not a fixed model"


# ---------------------------------------------------------------- reference path (PATH, not graded)
def h1_no_model_call_without_evidence():
    for question in UNANSWERABLE:
        llm = CountingLLM()
        ask(question, knowledge_dir=knowledge_copy(), llm=llm)
        assert llm.calls == 0, "reference path refuses in code, so the model is not called (no cost, no risk)"


def h2_retriever_ranks_and_filters():
    chunks = chunk_documents(load_documents(knowledge_copy()))
    found = retrieve(PASS_Q, chunks, top_k=3, min_score=2)
    assert 1 <= len(found) <= 3, f"expected 1..3 chunks, got {len(found)}"
    assert "70%" in found[0]["text"], "the pass-rule paragraph should rank first"
    assert retrieve("parking fee", chunks) == [], "an irrelevant question should retrieve nothing"


SCENARIOS = [
    ("S1", "baseline", "LLM-only mode answers fluently, with invented numbers", s1_llm_only_answers_confidently_but_wrong),
    ("S2", "baseline", "Chunks keep their provenance (source, updated)", s2_chunks_keep_provenance),
    ("S3", "target", "RAG answer is grounded (70%, 3.00) and cites its source", s3_rag_answer_is_grounded_and_cited),
    ("S4", "target", "No invented rule reaches the student when the documents have no evidence (model that invents)", s4_never_presents_invented_rules),
    ("S5", "target", "A new document is used without any code change", s5_new_knowledge_without_code_change),
    ("S6", "target", "The model is swappable: ask() uses the llm it is given", s6_model_is_swappable),
    ("H1", "path", "No model call when nothing relevant is retrieved (cost)", h1_no_model_call_without_evidence),
    ("H2", "path", "Retriever ranks the pass-rule chunk first and filters irrelevant ones", h2_retriever_ranks_and_filters),
]


def load_punch():
    """The Second Punch is released in class (punch_scenarios.py). Before that it is not in your folder."""
    try:
        import punch_scenarios
    except ImportError:
        return None
    return punch_scenarios.scenarios(globals())


def main():
    run_punch = "--punch" in sys.argv
    scenarios = list(SCENARIOS)
    if run_punch:
        extra = load_punch()
        if extra is None:
            print("Вторият удар още не е пуснат (няма punch_scenarios.py). / Second Punch not released yet.\n")
        else:
            scenarios += extra
    graded = passed = hints_ok = hints = 0
    for sid, tag, title, fn in scenarios:
        try:
            with redirect_stdout(io.StringIO()):
                fn()
            ok, msg = True, ""
        except AssertionError as e:
            ok, msg = False, str(e)
        except NotImplementedError as e:
            ok, msg = False, f"not built yet: {e}"
        except Exception as e:  # a crash is also a failure, show where
            ok, msg = False, f"{type(e).__name__}: {e}"
        if tag == "path":                       # reference-path guidance: shown, never graded
            hints += 1
            hints_ok += ok
            print(f"[PASS] {sid} (path) {title}" if ok else f"[path] {sid} {title} -> насока/guidance: {msg}")
            continue
        graded += 1
        passed += ok
        print(f"[PASS] {sid} {title}" if ok else f"[FAIL] {sid} {title} -> {msg}")
    note = "All graded (REQ) scenarios pass." if passed == graded else "Target scenarios fail until you complete the Build."
    print(f"\nREQ {passed}/{graded} passed. {note}  PATH hints: {hints_ok}/{hints}."
          + ("" if run_punch else "  (Second Punch: python verify.py --punch)"))
    return 0 if passed == graded else 1


if __name__ == "__main__":
    sys.exit(main())
