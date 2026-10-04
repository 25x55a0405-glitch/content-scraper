"""Wire the steps together into the agent graph.

This is what makes it a graph rather than a straight script: it can go
backwards (rewrite a draft), take different paths (retry, approve, reject),
and stop mid-run to wait for a person.

    fetch_data ──(got the data?)──> detect_anomalies ──> draft_commentary
        │  ▲ no                                               │
        └──┘ retry (max 2)                                    ▼
                                                       verify_numbers
                                                        │          ▲
                      (every figure correct?) no, rewrite│          │
                                  ┌──────────────────────┘          │
                                  ▼                                 │
                           draft_commentary ────────────────────────┘
                                  │ yes (or out of attempts)
                                  ▼
                           human_approval  ← the run PAUSES here
                                  │
                       approved   │   sent back for changes
                          ┌───────┴────────┐
                          ▼                ▼
                   render_report          END
                          │
                          ▼
                         END
"""

from __future__ import annotations

import os

from langgraph.graph import END, START, StateGraph

from . import nodes
from .state import ReportState

MAX_FETCH_ATTEMPTS = 2

# Where paused runs are saved, so the approval queue survives a restart.
CHECKPOINT_DB = os.path.join(os.path.dirname(__file__), "output", "runs.sqlite")


def _after_fetch(state: ReportState) -> str:
    """Did the data load? If not, try again a couple of times, then stop."""
    if state.get("data"):
        return "ok"
    if state.get("fetch_attempts", 0) < MAX_FETCH_ATTEMPTS:
        return "retry"
    return "give_up"


def _after_verify(state: ReportState) -> str:
    """The loop: rewrite if figures are wrong and we still have attempts left.

    The attempt limit matters. Without it an agent can loop forever, calling a
    paid API every time.
    """
    issues = state.get("verify_issues", [])
    attempts = state.get("verify_attempts", 0)
    limit = state.get("max_verify_attempts", 3)
    return "rewrite" if issues and attempts < limit else "continue"


def _after_approval(state: ReportState) -> str:
    """Only produce the client-facing report if a person approved it."""
    return "approved" if state.get("approval") == "approved" else "rejected"


def _build(checkpointer):
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
        {"rewrite": "draft_commentary", "continue": "human_approval"},
    )
    g.add_conditional_edges(
        "human_approval",
        _after_approval,
        {"approved": "render_report", "rejected": END},
    )
    g.add_edge("render_report", END)

    return g.compile(checkpointer=checkpointer)


def build_graph(persist: bool = True):
    """Build the agent.

    With `persist` on, paused runs are written to a small database file, so a
    report waiting for approval is still waiting after you restart the app.
    """
    if persist:
        from langgraph.checkpoint.sqlite import SqliteSaver

        os.makedirs(os.path.dirname(CHECKPOINT_DB), exist_ok=True)
        import sqlite3

        conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
        return _build(SqliteSaver(conn))

    from langgraph.checkpoint.memory import MemorySaver

    return _build(MemorySaver())
