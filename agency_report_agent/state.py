"""The shared "memory" that flows through the agent graph.

Every node reads from this object and writes new values back into it.
Think of it as a form that gets passed from one station to the next on an
assembly line, with each station filling in its part.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict


class ReportState(TypedDict, total=False):
    # --- Inputs ---
    client_file: str              # path to the client's data file
    agent_model: str              # which Claude model to use in live mode
    use_llm: bool                 # True = call Claude; False = free mock mode
    auto_approve: bool            # True = skip the human approval prompt
    demo_glitch: bool             # True = inject one wrong number to show the check working
    max_verify_attempts: int      # how many times the number-check loop may retry

    # --- Filled in as the graph runs ---
    data: dict[str, Any]          # the client's metrics, loaded by fetch_data
    fetch_attempts: int           # how many times we tried to load the data
    anomalies: list[str]          # unusually large swings flagged for a human
    draft: str                    # the current draft of the report commentary
    verify_attempts: int          # how many times the number-check loop has run
    verify_issues: list[str]      # numbers in the draft that don't match the source
    approval: Literal["approved", "rejected", "pending"]
    approval_note: Optional[str]  # an editor's note left during approval
    final_report_path: Optional[str]
    log: list[str]                # a human-readable trace of what happened
