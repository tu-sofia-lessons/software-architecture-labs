"""The guard: the application's deterministic check between 'the model proposes' and 'the tool executes'.

check(call, principal, tools) -> Decision
    ALLOW           execute now
    NEEDS_APPROVAL  execute only if the human confirms
    DENY            never execute; the reason goes back to the model
"""
from dataclasses import dataclass

ALLOW, NEEDS_APPROVAL, DENY = "ALLOW", "NEEDS_APPROVAL", "DENY"


@dataclass(frozen=True)
class Decision:
    verdict: str
    reason: str


def check(call, principal, tools) -> Decision:
    """Decide whether the proposed tool call may run on behalf of this principal."""
    # WEEK 10 BUILD: this is the hole — every proposal is executed, whoever asked.
    return Decision(ALLOW, "no guard yet")
