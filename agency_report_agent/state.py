"""The shared record that travels through the agent graph.

Think of it as a job folder moving from desk to desk in an office. Each desk
reads it, adds its pages, and puts it back. No desk talks to another directly —
the graph decides where the folder goes next.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict


class ReportState(TypedDict, total=False):
    # --- Inputs, set before the run starts ---
    client_id: str                 # short id, e.g. "brightwave_dental"
    client_file: str               # path to this client's data file
    agency: dict[str, Any]         # the agency's name, brand colour and house voice
    agent_model: Optional[str]     # which Claude model to use in live mode
    use_llm: bool                  # True = write with Claude; False = free mock mode
    demo_glitch: bool              # inject one wrong figure to show the check working
    max_verify_attempts: int       # how many rewrites the number check may ask for

    # --- Filled in as the graph runs ---
    data: dict[str, Any]           # the client's figures
    fetch_attempts: int
    anomalies: list[str]           # unusual swings that need a human explanation
    draft: str                     # the current commentary
    verify_issues: list[str]       # figures in the draft that don't match the data
    verify_attempts: int
    verify_history: list[dict[str, Any]]  # the audit trail of every check
    figures_checked: int           # how many numbers were validated in the final draft

    # --- Human decision ---
    approval: Literal["approved", "rejected", "pending"]
    approval_note: Optional[str]
    reviewer: Optional[str]

    # --- Output ---
    report_html: Optional[str]
    report_path: Optional[str]
    log: list[str]
