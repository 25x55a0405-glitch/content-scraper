"""The stations on the assembly line — one function per node in the graph.

Each function takes the current state and returns the fields it wants to
update. LangGraph merges those updates back into the shared state and moves on
to the next node.
"""

from __future__ import annotations

import json
from typing import Any

from .metrics import (
    find_anomalies,
    summarise_channels,
    totals,
    verify_draft,
)


def _log(state: dict[str, Any], message: str) -> list[str]:
    """Append a line to the run log and return the whole log."""
    existing = list(state.get("log", []))
    existing.append(message)
    print(f"  · {message}")
    return existing


# --------------------------------------------------------------------------- #
# 1. Fetch the client's data (with a retry, to show the graph can recover).
# --------------------------------------------------------------------------- #
def fetch_data(state: dict[str, Any]) -> dict[str, Any]:
    attempts = state.get("fetch_attempts", 0) + 1
    path = state["client_file"]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001 — we want to catch anything and retry
        log = _log(state, f"Could not read {path} (attempt {attempts}): {exc}")
        # Signal the retry edge by leaving `data` unset.
        return {"fetch_attempts": attempts, "log": log}

    log = _log(
        state,
        f"Loaded data for {data.get('client_name', 'the client')} "
        f"({data.get('period', 'this period')}).",
    )
    return {"data": data, "fetch_attempts": attempts, "log": log}


# --------------------------------------------------------------------------- #
# 2. Flag unusually large swings for a human to explain (a branch in the graph).
# --------------------------------------------------------------------------- #
def detect_anomalies(state: dict[str, Any]) -> dict[str, Any]:
    anomalies = find_anomalies(state["data"])
    if anomalies:
        log = _log(state, f"Flagged {len(anomalies)} anomaly(ies) for human review.")
    else:
        log = _log(state, "No unusual swings this period.")
    return {"anomalies": anomalies, "log": log}


# --------------------------------------------------------------------------- #
# 3. Draft the commentary — either with Claude (live) or a template (free mock).
# --------------------------------------------------------------------------- #
def _mock_commentary(state: dict[str, Any]) -> str:
    """Build a correct, deterministic draft from the data — no AI, no cost.

    If `demo_glitch` is on, the FIRST attempt deliberately states one wrong
    number so you can watch the verification loop catch and fix it in the demo.
    """
    data = state["data"]
    t = totals(data)
    rows = summarise_channels(data)
    currency = data.get("currency", "")

    best = max(rows, key=lambda r: r["sessions_change"] or -999)
    lines = []
    lines.append(
        f"This period {data['client_name']} recorded {t['total_sessions']} sessions "
        f"across all channels, with {t['total_conversions']} conversions "
        f"({t['total_conversions_change']}% versus last period). That puts the account "
        f"{'ahead of' if (t['total_conversions'] or 0) >= (t['leads_target'] or 0) else 'on track towards'} "
        f"the target of {t['leads_target']} leads a month."
    )

    glitch_on = state.get("demo_glitch") and state.get("verify_attempts", 0) == 0
    headline_change = best["sessions_change"]
    if glitch_on and headline_change is not None:
        # Deliberately wrong figure, clearly only for the demo.
        headline_change = round(headline_change + 6.1, 1)

    lines.append(
        f"The standout channel was {best['channel']}, where sessions moved {headline_change}%. "
        f"Paid search delivered {next((r['conversions'] for r in rows if r['channel'] == 'Paid Search'), 0)} "
        f"conversions on {currency}{next((r['spend'] for r in rows if r['channel'] == 'Paid Search'), 0)} of spend, "
        f"so the cost per conversion stayed efficient."
    )

    lines.append(
        "Organic search continued to build, and we recommend holding the current content "
        "cadence into next period while we watch the flagged swings above."
    )
    return "\n\n".join(lines)


def draft_commentary(state: dict[str, Any]) -> dict[str, Any]:
    attempt = state.get("verify_attempts", 0)
    issues = state.get("verify_issues", [])

    if state.get("use_llm"):
        from .llm import draft_commentary as llm_draft

        draft = llm_draft(
            state["data"],
            previous_issues=issues or None,
            model=state.get("agent_model"),
        )
        how = "Claude"
    else:
        draft = _mock_commentary(state)
        how = "mock template (free)"

    if attempt == 0:
        log = _log(state, f"Wrote first draft using {how}.")
    else:
        log = _log(state, f"Rewrote draft using {how} to fix {len(issues)} number issue(s).")
    return {"draft": draft, "log": log}


# --------------------------------------------------------------------------- #
# 4. Verify every number in the draft against the source data (the loop check).
# --------------------------------------------------------------------------- #
def verify_numbers(state: dict[str, Any]) -> dict[str, Any]:
    issues = verify_draft(state["draft"], state["data"])
    attempts = state.get("verify_attempts", 0) + 1
    if issues:
        log = _log(
            state,
            f"Number check FAILED on attempt {attempts}: {len(issues)} figure(s) do not match.",
        )
    else:
        log = _log(state, f"Number check passed on attempt {attempts}. Every figure matches the data.")
    return {"verify_issues": issues, "verify_attempts": attempts, "log": log}


# --------------------------------------------------------------------------- #
# 5. Human approval (human-in-the-loop). A real deployment would do this in
#    Slack; here it is a terminal prompt, or auto-approved for tests/CI.
# --------------------------------------------------------------------------- #
def human_approval(state: dict[str, Any]) -> dict[str, Any]:
    anomalies = state.get("anomalies", [])

    if state.get("auto_approve"):
        log = _log(state, "Auto-approved (no human prompt).")
        return {"approval": "approved", "approval_note": None, "log": log}

    print("\n" + "=" * 68)
    print("DRAFT REPORT — needs your approval before it is 'sent'")
    print("=" * 68)
    print(state["draft"])
    if anomalies:
        print("\nFlagged for your explanation:")
        for a in anomalies:
            print(f"  ! {a}")
    print("=" * 68)

    choice = input("Approve and send? [y = yes / n = reject / e = edit note]: ").strip().lower()
    if choice == "e":
        note = input("Your note (added to the report): ").strip()
        log = _log(state, "Approved with an editor's note.")
        return {"approval": "approved", "approval_note": note, "log": log}
    if choice == "y":
        log = _log(state, "Approved by a human.")
        return {"approval": "approved", "approval_note": None, "log": log}
    log = _log(state, "Rejected by a human — nothing was sent.")
    return {"approval": "rejected", "approval_note": None, "log": log}


# --------------------------------------------------------------------------- #
# 6. Render the final report to a file.
# --------------------------------------------------------------------------- #
def render_report(state: dict[str, Any]) -> dict[str, Any]:
    import os

    data = state["data"]
    t = totals(data)
    rows = summarise_channels(data)
    currency = data.get("currency", "")

    lines = [
        f"# {data['client_name']} — Marketing Report",
        f"*{data.get('period', '')} · prepared by {data.get('agency_name', 'your agency')}*",
        "",
        "## Summary",
        state["draft"],
        "",
        "## The numbers",
        "",
        "| Channel | Sessions | Change | Conversions | Change |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        sc = "—" if r["sessions_change"] is None else f"{r['sessions_change']:+.1f}%"
        cc = "—" if r["conversions_change"] is None else f"{r['conversions_change']:+.1f}%"
        lines.append(
            f"| {r['channel']} | {r['sessions']} | {sc} | {r['conversions']} | {cc} |"
        )
    lines.append(
        f"| **Total** | **{t['total_sessions']}** | "
        f"**{t['total_sessions_change']:+.1f}%** | **{t['total_conversions']}** | "
        f"**{t['total_conversions_change']:+.1f}%** |"
    )

    if state.get("anomalies"):
        lines += ["", "## Flagged for review", ""]
        lines += [f"- {a}" for a in state["anomalies"]]

    if state.get("approval_note"):
        lines += ["", "## Account manager's note", "", state["approval_note"]]

    lines += [
        "",
        "---",
        "*Every figure in this report was automatically checked against the source "
        "data before an account manager approved it.*",
    ]

    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    safe = data["client_name"].lower().replace(" ", "_")
    period = data.get("period", "report").lower().replace(" ", "_")
    path = os.path.join(out_dir, f"{safe}_{period}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    log = _log(state, f"Report written to {path}")
    return {"final_report_path": path, "log": log}
