"""The stations on the assembly line — one function per step in the graph.

Each function receives the shared record, does one job, and returns only the
fields it changed. LangGraph merges those changes in and moves to the next step.
"""

from __future__ import annotations

import json
from typing import Any

from langgraph.types import interrupt

from .metrics import count_numbers, find_anomalies, summarise_channels, totals, verify_draft


def _log(state: dict[str, Any], message: str) -> list[str]:
    """Add a line to the plain-English run log."""
    existing = list(state.get("log", []))
    existing.append(message)
    return existing


# --------------------------------------------------------------------------- #
# 1. Load the client's figures. Retries once, because real data sources fail.
# --------------------------------------------------------------------------- #
def fetch_data(state: dict[str, Any]) -> dict[str, Any]:
    attempts = state.get("fetch_attempts", 0) + 1
    path = state["client_file"]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001 — any failure should trigger the retry
        return {
            "fetch_attempts": attempts,
            "log": _log(state, f"Could not read the data (attempt {attempts}): {exc}"),
        }

    return {
        "data": data,
        "fetch_attempts": attempts,
        "log": _log(state, f"Loaded {data.get('client_name')} figures for {data.get('period')}."),
    }


# --------------------------------------------------------------------------- #
# 2. Flag unusual swings. Plain arithmetic — no AI, so it cannot invent a flag.
# --------------------------------------------------------------------------- #
def detect_anomalies(state: dict[str, Any]) -> dict[str, Any]:
    anomalies = find_anomalies(state["data"])
    msg = (
        f"Flagged {len(anomalies)} unusual change for a human to explain."
        if len(anomalies) == 1
        else f"Flagged {len(anomalies)} unusual changes for a human to explain."
        if anomalies
        else "Nothing unusual this period."
    )
    return {"anomalies": anomalies, "log": _log(state, msg)}


# --------------------------------------------------------------------------- #
# 3. Write the commentary — with Claude (live) or a template (free mock mode).
# --------------------------------------------------------------------------- #
def _mock_commentary(state: dict[str, Any]) -> str:
    """A correct, deterministic draft built straight from the data. No cost.

    With `demo_glitch` on, the FIRST draft deliberately states one wrong figure
    so you can watch the checking step catch and fix it.
    """
    data = state["data"]
    t = totals(data)
    rows = summarise_channels(data)
    currency = data.get("currency", "")
    paid = next((r for r in rows if r["channel"] == "Paid Search"), None)
    best = max(rows, key=lambda r: r["sessions_change"] or -999)

    hit_target = (t["total_conversions"] or 0) >= (t["leads_target"] or 0)
    standing = "ahead of" if hit_target else "tracking towards"

    def phrase(change: float | None, noun: str = "") -> str:
        """Turn a raw percentage into something a person would actually write."""
        if change is None:
            return f"with no {noun} comparison available".strip()
        if abs(change) < 0.05:
            return "level with last month"
        return f"{'up' if change > 0 else 'down'} {abs(change)}% on last month"

    headline_change = best["sessions_change"]
    if state.get("demo_glitch") and state.get("verify_attempts", 0) == 0 and headline_change:
        headline_change = round(headline_change + 6.1, 1)  # deliberate demo error

    if headline_change is None:
        standout = f"{best['channel']} carried the month."
    elif abs(headline_change) < 0.05:
        standout = f"{best['channel']} held level with last month."
    else:
        direction = "grew" if headline_change > 0 else "fell"
        standout = f"{best['channel']} {direction} {abs(headline_change)}% in sessions."

    closing = (
        "We would hold the current content plan into next month while we look into "
        "the changes flagged above."
        if state.get("anomalies")
        else "We would hold the current plan into next month and keep building on organic search."
    )

    paragraphs = [
        f"{data['client_name']} recorded {t['total_sessions']} sessions this period and "
        f"{t['total_conversions']} enquiries, {phrase(t['total_conversions_change'])}. "
        f"That puts the account {standing} the target of {t['leads_target']} enquiries a month.",
        standout
        + (
            f" Paid search brought in {paid['conversions']} enquiries from "
            f"{currency}{paid['spend']} of spend, holding cost per enquiry steady."
            if paid
            else ""
        ),
        closing,
    ]
    return "\n\n".join(paragraphs)


def draft_commentary(state: dict[str, Any]) -> dict[str, Any]:
    attempt = state.get("verify_attempts", 0)
    issues = state.get("verify_issues", [])

    if state.get("use_llm"):
        from .llm import draft_commentary as llm_draft

        draft = llm_draft(
            state["data"],
            agency=state.get("agency", {}),
            previous_issues=issues or None,
            model=state.get("agent_model"),
        )
        how = "Claude"
    else:
        draft = _mock_commentary(state)
        how = "the built-in template"

    message = (
        f"Wrote the first draft using {how}."
        if attempt == 0
        else f"Rewrote the draft to correct {len(issues)} figure(s)."
    )
    return {"draft": draft, "log": _log(state, message)}


# --------------------------------------------------------------------------- #
# 4. Check every figure in the draft against the source data. Again, no AI.
# --------------------------------------------------------------------------- #
def verify_numbers(state: dict[str, Any]) -> dict[str, Any]:
    draft = state["draft"]
    issues = verify_draft(draft, state["data"])
    checked = count_numbers(draft)
    attempts = state.get("verify_attempts", 0) + 1

    history = list(state.get("verify_history", []))
    history.append({"attempt": attempts, "checked": checked, "issues": issues})

    message = (
        f"Checked {checked} figures — all match the source data."
        if not issues
        else f"Checked {checked} figures — {len(issues)} did not match the source data."
    )
    return {
        "verify_issues": issues,
        "verify_attempts": attempts,
        "verify_history": history,
        "figures_checked": checked,
        "log": _log(state, message),
    }


# --------------------------------------------------------------------------- #
# 5. Stop and wait for a person. This is a real pause: the run is saved to disk
#    and resumes only when someone approves it, even days later.
# --------------------------------------------------------------------------- #
def human_approval(state: dict[str, Any]) -> dict[str, Any]:
    decision = interrupt(
        {
            "client_id": state.get("client_id"),
            "client_name": state.get("data", {}).get("client_name"),
            "draft": state.get("draft"),
            "anomalies": state.get("anomalies", []),
            "verify_history": state.get("verify_history", []),
        }
    )

    approved = decision.get("decision") == "approved"
    note = decision.get("note") or None
    reviewer = decision.get("reviewer") or None
    message = (
        f"Approved by {reviewer or 'a reviewer'}."
        if approved
        else f"Sent back for changes by {reviewer or 'a reviewer'}."
    )
    return {
        "approval": "approved" if approved else "rejected",
        "approval_note": note,
        "reviewer": reviewer,
        "log": _log(state, message),
    }


# --------------------------------------------------------------------------- #
# 6. Produce the finished, branded report the agency sends to its client.
# --------------------------------------------------------------------------- #
def render_report(state: dict[str, Any]) -> dict[str, Any]:
    import os

    from .render import render_client_report

    html = render_client_report(state)

    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    period = str(state["data"].get("period", "report")).lower().replace(" ", "_")
    path = os.path.join(out_dir, f"{state['client_id']}_{period}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)

    return {
        "report_html": html,
        "report_path": path,
        "log": _log(state, "Final report produced and saved."),
    }
