"""Wire the nodes together into an agent graph.

This is the part that makes it a *graph* and not a straight script: it has a
loop (verify -> back to draft) and three branches (fetch retry, loop-or-move-on,
approved-or-rejected). Here is the shape:

    fetch_data ──(data ok?)──> detect_anomalies ──> draft_commentary
        │  ▲ no                                            │
        └──┘ retry (max 2)                                 ▼
                                                     verify_numbers
                                                      │        ▲
                           (numbers match?) no, retry │        │
                                   ┌──────────────────┘        │
                                   ▼                           │
                            draft_commentary ─────────────────┘
                                   │ yes (or gave up after N tries)
                                   ▼
                            human_approval ──(approved?)──> render_report ──> END
                                   │ rejected
                                   └──────────────────────────────────────> END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from . import nodes
from .state import ReportState

MAX_FETCH_ATTEMPTS = 2


def _after_fetch(state: ReportState) -> str:
    """Branch: did we get the data? If not, retry a couple of times."""
    if state.get("data"):
        return "ok"
    if state.get("fetch_attempts", 0) < MAX_FETCH_ATTEMPTS:
        return "retry"
    return "give_up"


def _after_verify(state: ReportState) -> str:
    """Branch (and loop): rewrite the draft if numbers are wrong and we have tries left."""
    issues = state.get("verify_issues", [])
    attempts = state.get("verify_attempts", 0)
    limit = state.get("max_verify_attempts", 3)
    if issues and attempts < limit:
        return "revise"
    return "continue"


def _after_approval(state: ReportState) -> str:
    """Branch: only render and 'send' if a human approved."""
    return "approved" if state.get("approval") == "approved" else "rejected"


def build_graph():
    """Assemble and compile the agent graph."""
    g = StateGraph(ReportState)

    g.add_node("fetch_data", nodes.fetch_data)
    g.add_node("detect_anomalies", nodes.detect_anomalies)
    g.add_node("draft_commentary", nodes.draft_commentary)
    g.add_node("verify_numbers", nodes.verify_numbers)
    g.add_node("human_approval", nodes.human_approval)
    g.add_node("render_report", nodes.render_report)

    g.add_edge(START, "fetch_data")
    g.add_conditional_edges(
        "fetch_data",
        _after_fetch,
        {"ok": "detect_anomalies", "retry": "fetch_data", "give_up": END},
    )
    g.add_edge("detect_anomalies", "draft_commentary")
    g.add_edge("draft_commentary", "verify_numbers")
    g.add_conditional_edges(
        "verify_numbers",
        _after_verify,
        {"revise": "draft_commentary", "continue": "human_approval"},
    )
    g.add_conditional_edges(
        "human_approval",
        _after_approval,
        {"approved": "render_report", "rejected": END},
    )
    g.add_edge("render_report", END)

    return g.compile()
