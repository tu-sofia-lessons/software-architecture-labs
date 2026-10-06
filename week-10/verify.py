"""Acceptance scenarios for Week 10.  Run:  python verify.py   (add --punch for the Second Punch)

REQ scenarios check the requirements (what happens to the platform) and are graded.
PATH scenarios check the reference guard directly; they are hints, never graded.
Always uses the offline fake agent LLM. Keep the signature guard.check(call, principal, tools) -> Decision.
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import io
import json
import os
import shutil
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

os.environ["LLM_BACKEND"] = "fake"
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import agent  # noqa: E402
import guard  # noqa: E402
import llm_client  # noqa: E402
from identity import USERS, Principal  # noqa: E402
from platform_api import Platform  # noqa: E402
from tools import build_tools  # noqa: E402

MARIA, REGISTRAR = USERS["maria"], USERS["registrar"]


class Human:
    """A scripted human who answers the approval question and remembers what was asked."""
    def __init__(self, answer):
        self.answer, self.asked = answer, []

    def __call__(self, description):
        self.asked.append(description)
        return self.answer


def setup(extra_doc=None):
    folder = Path(tempfile.mkdtemp()) / "knowledge"
    shutil.copytree(HERE / "knowledge", folder, ignore=lambda d, names: [n for n in names if n == "ai201_notes.txt"])
    if extra_doc:
        shutil.copy(HERE / "punch" / extra_doc, folder)
    platform = Platform(folder)
    return platform, build_tools(platform)


def chat(request, principal, human, extra_doc=None):
    platform, tools = setup(extra_doc)
    result = agent.run(request, principal, tools, llm_client.generate, human)
    return platform, result


# ---------------------------------------------------------------- baseline
def s1_read_only_question_runs_without_approval():
    human = Human(True)
    _, result = chat("Which of my courses still have seats?", MARIA, human)
    assert "SA101: 1 free" in result.answer, f"unexpected answer: {result.answer!r}"
    assert not human.asked, "a read-only question must not ask the human for approval"


def s2_step_budget_stops_a_looping_model():
    _, tools = setup()
    looping = lambda prompt: json.dumps({"action": "find_course", "args": {"query": "SA101"}})  # noqa: E731
    result = agent.run("loop forever", MARIA, tools, looping, Human(True))
    assert result.answer.startswith("Stopped") and len(result.trace) == agent.MAX_STEPS, "step budget not enforced"


# ---------------------------------------------------------------- target
def s3_write_needs_approval_and_runs_when_approved():
    platform, tools = setup()
    seen_before = []

    def human(description):                     # records the platform state at the moment we are asked
        seen_before.append((1, 3) in platform.enrollments)
        return True

    agent.run("Enroll me in Databases", MARIA, tools, llm_client.generate, human)
    assert len(seen_before) == 1, f"expected exactly one approval request for one write, got {len(seen_before)}"
    assert seen_before == [False], "the enrollment happened BEFORE the human was asked"
    assert (1, 3) in platform.enrollments, "approved enrollment was not executed"


def s4_declined_write_is_not_executed():
    human = Human(False)
    platform, result = chat("Enroll me in Databases", MARIA, human)
    assert human.asked, "the human was never asked"
    assert (1, 3) not in platform.enrollments, "a declined write must not be executed"


BAD_CALLS = [
    {"action": "delete_all_students", "args": {}},
    {"action": "enroll", "args": {"student_id": 1}},                              # missing argument
    {"action": "enroll", "args": {"student_id": "1", "course_id": 3}},            # wrong type
    {"action": "enroll", "args": {"student_id": True, "course_id": 3}},           # bool is not an id
    {"action": "course_seats", "args": {"course_id": 1, "sql": "DROP TABLE x"}},  # unexpected argument
]


def s5_malformed_proposals_never_change_the_platform():
    platform, tools = setup()
    before = set(platform.enrollments)
    script = [json.dumps(c) for c in BAD_CALLS] + [json.dumps({"final": "done"})]
    replies = iter(script)
    agent.run("do strange things", MARIA, tools, lambda prompt: next(replies), Human(True))
    assert set(platform.enrollments) == before, "a malformed or unknown tool call changed the platform"


def h1_guard_denies_unknown_tools_and_bad_arguments():
    _, tools = setup()
    for call in BAD_CALLS:
        decision = guard.check(call, MARIA, tools)
        assert decision.verdict == guard.DENY, f"{call} → {decision.verdict} (reference guard: DENY)"


def s6_agent_cannot_exceed_the_users_authority():
    platform, _ = chat("Enroll Ivan in Databases", MARIA, Human(True))     # even if the human says yes
    assert (2, 3) not in platform.enrollments, "Maria's agent enrolled Ivan"


def h2_outside_authority_is_denied_without_asking():
    human = Human(True)
    chat("Enroll Ivan in Databases", MARIA, human)
    assert not human.asked, "reference path: an action outside the user's authority is DENIED, not offered for approval"
    _, tools = setup()
    reading_others = guard.check({"action": "list_my_courses", "args": {"student_id": 2}}, MARIA, tools)
    stranger = guard.check({"action": "find_course", "args": {"query": "SA101"}}, Principal("x", "guest", None), tools)
    assert reading_others.verdict == guard.DENY, "a student must not read another student's courses"
    assert stranger.verdict == guard.DENY, "unknown role must be denied (fail-safe)"


def s7_admin_may_act_for_others_but_still_confirms():
    human = Human(True)
    platform, _ = chat("Enroll Georgi in Databases", REGISTRAR, human)
    assert human.asked, "writes need confirmation for every role"
    assert (3, 3) in platform.enrollments, "the registrar may enroll other students"


SCENARIOS = [
    ("S1", "baseline", "Read-only question runs without asking for approval", s1_read_only_question_runs_without_approval),
    ("S2", "baseline", "Step budget stops a looping model", s2_step_budget_stops_a_looping_model),
    ("S3", "target", "A write runs only after exactly one human approval (not before)", s3_write_needs_approval_and_runs_when_approved),
    ("S4", "target", "A declined write is not executed", s4_declined_write_is_not_executed),
    ("S5", "target", "Unknown tools and malformed arguments never change the platform", s5_malformed_proposals_never_change_the_platform),
    ("S6", "target", "The agent cannot exceed the user's authority, even with a human 'yes'", s6_agent_cannot_exceed_the_users_authority),
    ("S7", "target", "Admin may act for others, still with confirmation", s7_admin_may_act_for_others_but_still_confirms),
    ("H1", "path", "Guard itself denies unknown tools and malformed arguments", h1_guard_denies_unknown_tools_and_bad_arguments),
    ("H2", "path", "Outside authority: denied without asking; unknown role denied", h2_outside_authority_is_denied_without_asking),
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
