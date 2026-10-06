"""Second Punch, Week 9 — released in class at 15:50.

The Student Office publishes an update: from 2026/27 the attendance rule for Software Architecture is 80%.
The new document is punch/software_architecture_update.txt (same Title, newer Updated date).
Unzip into your week-09 folder. Try it by hand by copying the file into knowledge/ — and remove it again
afterwards, so that knowledge/ holds only the official documents. verify.py uses its own private copies,
so its result does not depend on what you left in knowledge/.
    python verify.py --punch
"""


def scenarios(v):
    """v = the globals of verify.py (helpers such as ask, knowledge_copy, CountingLLM, PASS_Q, HERE)."""

    def p1_newest_document_wins():
        update = (v["HERE"] / "punch" / "software_architecture_update.txt").read_text(encoding="utf-8")
        folder = v["knowledge_copy"](("software_architecture_update.txt", update))
        answer, sources = v["ask"](v["PASS_Q"], knowledge_dir=folder, llm=v["CountingLLM"]())
        assert "80%" in answer, f"the newest rule (80%) must be used: {answer!r}"
        assert "70%" not in answer, f"the superseded rule (70%) must not be presented as current: {answer!r}"

    return [("P1", "punch", "Second Punch: the newest version of a document wins", p1_newest_document_wins)]
