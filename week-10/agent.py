"""The agent loop (provided): LLM decides → application validates → tool executes → service acts.

    request ─▶ prompt ─▶ LLM ─▶ {"action","args"} ─▶ guard.check ─▶ (confirm?) ─▶ tools.execute ─▶ result
                  ▲                                                                                  │
                  └──────────────────────────────── history ◀────────────────────────────────────────┘
"""
import json
from dataclasses import dataclass, field

import guard
import tools as toolbox

MAX_STEPS = 8


@dataclass
class AgentResult:
    answer: str
    trace: list = field(default_factory=list)   # one entry per proposed tool call, incl. the guard decision


def build_prompt(request, principal, tools, history):
    """Prompt for the model. The STATE_JSON line is the machine-readable part."""
    tool_lines = "\n".join(
        f"- {t.name}({', '.join(f'{k}: {v.__name__}' for k, v in t.params.items())}) [{t.kind}] {t.description}"
        for t in tools.values())
    state = {"request": request,
             "user": {"name": principal.user, "role": principal.role, "student_id": principal.student_id},
             "history": history}
    return (
        "You are the University Assistant agent. Decide the NEXT step.\n"
        "Reply with ONLY one JSON object, either\n"
        '  {"action": "<tool name>", "args": {...}}   or   {"final": "<answer to the user>"}\n'
        f"Tools:\n{tool_lines}\n"
        f"STATE_JSON: {json.dumps(state, ensure_ascii=False)}\n"
    )


def parse_reply(reply):
    """Extract the JSON object from the model's reply (models like to add text around it)."""
    try:
        return json.loads(reply[reply.index("{"): reply.rindex("}") + 1])
    except ValueError:
        return None


def describe(call):
    args = ", ".join(f"{k}={v!r}" for k, v in call.get("args", {}).items())
    return f"{call.get('action')}({args})"


def run(request, principal, tools, llm, confirm, max_steps=MAX_STEPS):
    """Run the agent until it gives a final answer or the step budget is used up."""
    history, trace = [], []
    for step in range(1, max_steps + 1):
        call = parse_reply(llm(build_prompt(request, principal, tools, history)))
        if call is None:
            history.append({"action": "(invalid)", "args": {}, "result": {"error": "reply was not one JSON object"}})
            continue
        if "final" in call:
            return AgentResult(str(call["final"]), trace)

        decision = guard.check(call, principal, tools)                    # application validates
        verdict = decision.verdict
        if verdict == guard.NEEDS_APPROVAL:
            verdict = guard.ALLOW if confirm(describe(call)) else "DECLINED"
        if verdict == guard.ALLOW:
            result = toolbox.execute(tools, call)                         # tool executes → service acts
        elif verdict == "DECLINED":
            result = {"error": "the user did not approve this action"}
        else:
            result = {"error": f"denied: {decision.reason}"}

        trace.append({"step": step, "call": describe(call), "verdict": verdict,
                      "reason": decision.reason, "result": result})
        history.append({"action": call.get("action"), "args": call.get("args", {}), "result": result})
    return AgentResult("Stopped: step budget used up.", trace)
