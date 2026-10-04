"""Run the agent across every client an agency has, and track where each one is.

This is the layer the web app talks to. It knows how to start a client's report,
read back what state it is in, and resume a report that is waiting for approval.
"""

from __future__ import annotations

import glob
import json
import os
from typing import Any, Optional

from .graph import build_graph

HERE = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(HERE, "sample_data")
CLIENTS_DIR = os.path.join(SAMPLE_DIR, "clients")
OUTPUT_DIR = os.path.join(HERE, "output")
META_PATH = os.path.join(OUTPUT_DIR, "batch_meta.json")

# Status names used across the whole app.
NOT_STARTED = "not_started"
NEEDS_REVIEW = "needs_review"
APPROVED = "approved"
CHANGES_REQUESTED = "changes_requested"
FAILED = "failed"

STATUS_LABELS = {
    NOT_STARTED: "Not started",
    NEEDS_REVIEW: "Needs you",
    APPROVED: "Approved",
    CHANGES_REQUESTED: "Changes requested",
    FAILED: "Could not run",
}

_graph = None


def graph():
    """One shared agent for the whole app, so paused runs stay available."""
    global _graph
    if _graph is None:
        _graph = build_graph(persist=True)
    return _graph


# --------------------------------------------------------------------------- #
# Loading the agency and its clients
# --------------------------------------------------------------------------- #
def load_agency() -> dict[str, Any]:
    with open(os.path.join(SAMPLE_DIR, "agency.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def client_files() -> list[str]:
    return sorted(glob.glob(os.path.join(CLIENTS_DIR, "*.json")))


def load_clients() -> list[dict[str, Any]]:
    clients = []
    for path in client_files():
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        clients.append(
            {
                "id": os.path.splitext(os.path.basename(path))[0],
                "file": path,
                "name": data.get("client_name"),
                "period": data.get("period"),
            }
        )
    return clients


# --------------------------------------------------------------------------- #
# Run generation — lets "Start over" give every client a clean run
# --------------------------------------------------------------------------- #
def _meta() -> dict[str, Any]:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {"generation": 1}


def _save_meta(meta: dict[str, Any]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh)


def generation() -> int:
    return _meta().get("generation", 1)


def start_over() -> None:
    """Begin a fresh round of reports, leaving the old ones in the history."""
    meta = _meta()
    meta["generation"] = meta.get("generation", 1) + 1
    _save_meta(meta)


def _config(client_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": f"gen{generation()}:{client_id}"}}


# --------------------------------------------------------------------------- #
# Reading where a client's report has got to
# --------------------------------------------------------------------------- #
def status_of(client_id: str) -> dict[str, Any]:
    """Describe a single client's report in terms the dashboard can display."""
    snapshot = graph().get_state(_config(client_id))
    values: dict[str, Any] = snapshot.values or {}

    if not values:
        return {"status": NOT_STARTED, "state": {}}

    if snapshot.next and "human_approval" in snapshot.next:
        status = NEEDS_REVIEW
    elif values.get("approval") == "approved" and values.get("report_path"):
        status = APPROVED
    elif values.get("approval") == "rejected":
        status = CHANGES_REQUESTED
    elif not values.get("data"):
        status = FAILED
    else:
        status = NEEDS_REVIEW if snapshot.next else APPROVED

    history = values.get("verify_history", [])
    corrected = sum(len(h.get("issues", [])) for h in history)

    return {
        "status": status,
        "label": STATUS_LABELS[status],
        "state": values,
        "figures_checked": values.get("figures_checked", 0),
        "corrections": corrected,
        "attempts": values.get("verify_attempts", 0),
        "anomalies": values.get("anomalies", []),
        "draft": values.get("draft"),
        "report_path": values.get("report_path"),
    }


def overview() -> dict[str, Any]:
    """Everything the dashboard needs in one call."""
    agency = load_agency()
    rows = []
    for client in load_clients():
        info = status_of(client["id"])
        rows.append({**client, **info})

    counts = {key: 0 for key in STATUS_LABELS}
    for row in rows:
        counts[row["status"]] += 1

    figures = sum(r["figures_checked"] for r in rows)
    corrections = sum(r["corrections"] for r in rows)
    done = counts[APPROVED]

    return {
        "agency": agency,
        "clients": rows,
        "counts": counts,
        "figures_checked": figures,
        "corrections": corrections,
        # A conservative estimate the agency can sanity-check: the research
        # behind this offer put manual reporting at roughly 3 hours per client.
        "hours_saved": round(done * 3, 1),
    }


# --------------------------------------------------------------------------- #
# Running and resuming
# --------------------------------------------------------------------------- #
def run_client(
    client: dict[str, Any],
    agency: dict[str, Any],
    use_llm: bool = False,
    demo_glitch: bool = False,
) -> dict[str, Any]:
    """Start one client's report and let it run until it needs a person."""
    initial = {
        "client_id": client["id"],
        "client_file": client["file"],
        "agency": agency,
        "use_llm": use_llm,
        "demo_glitch": demo_glitch,
        "max_verify_attempts": 3,
        "agent_model": os.environ.get("AGENT_MODEL"),
        "log": [],
    }
    graph().invoke(initial, config=_config(client["id"]))
    return status_of(client["id"])


def run_all(use_llm: bool = False, demo_glitch: bool = False) -> dict[str, Any]:
    """Start every client that has not been started yet."""
    agency = load_agency()
    started = 0
    for client in load_clients():
        if status_of(client["id"])["status"] == NOT_STARTED:
            run_client(client, agency, use_llm=use_llm, demo_glitch=demo_glitch)
            started += 1
    return {"started": started}


def submit_decision(
    client_id: str,
    decision: str,
    note: Optional[str] = None,
    reviewer: Optional[str] = None,
) -> dict[str, Any]:
    """Resume a paused report with a person's decision."""
    from langgraph.types import Command

    graph().invoke(
        Command(resume={"decision": decision, "note": note, "reviewer": reviewer}),
        config=_config(client_id),
    )
    return status_of(client_id)
