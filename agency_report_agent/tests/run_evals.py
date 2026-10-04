"""Run the quality checks and print the one-page report you show a client.

    python -m agency_report_agent.tests.run_evals

No API key needed — everything here runs in free mock mode. This is the sheet
that answers a prospect's real question: "can I trust what it writes?"
"""

from __future__ import annotations

import json
import os
import sys

from langgraph.types import Command

from ..graph import build_graph
from ..metrics import verify_draft

HERE = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(os.path.dirname(HERE), "sample_data")
CLIENTS_DIR = os.path.join(SAMPLE_DIR, "clients")


def _load_cases() -> dict:
    with open(os.path.join(HERE, "test_cases.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _agency() -> dict:
    with open(os.path.join(SAMPLE_DIR, "agency.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _run_to_approval(graph, client_id: str, thread: str, demo_glitch: bool):
    """Start a client's report and stop where it waits for a person."""
    config = {"configurable": {"thread_id": thread}}
    graph.invoke(
        {
            "client_id": client_id,
            "client_file": os.path.join(CLIENTS_DIR, f"{client_id}.json"),
            "agency": _agency(),
            "use_llm": False,
            "demo_glitch": demo_glitch,
            "max_verify_attempts": 3,
            "log": [],
        },
        config=config,
    )
    return config


# --------------------------------------------------------------------------- #
def run_number_check_cases() -> tuple[int, int]:
    cases = _load_cases()
    with open(os.path.join(CLIENTS_DIR, cases["client_file"]), "r", encoding="utf-8") as fh:
        data = json.load(fh)

    passed = 0
    print("Fact-check: can it spot a made-up figure?")
    print("-" * 70)
    for case in cases["cases"]:
        issues = verify_draft(case["draft"], data)
        clean = len(issues) == 0
        ok = clean == case["should_pass"]
        passed += ok
        expected = "accept" if case["should_pass"] else "reject"
        got = "accepted" if clean else f"rejected ({len(issues)})"
        print(f"  [{'PASS' if ok else 'FAIL'}] {case['name']:<36} expected {expected}, {got}")
    return passed, len(cases["cases"])


def run_pause_check() -> bool:
    """The agent must stop and wait for a person before anything is produced."""
    print("\nSafety: does it stop and wait for a human?")
    print("-" * 70)
    graph = build_graph(persist=False)
    config = _run_to_approval(graph, "brightwave_dental", "eval-pause", demo_glitch=False)
    snapshot = graph.get_state(config)

    paused = bool(snapshot.next) and "human_approval" in snapshot.next
    nothing_sent = not snapshot.values.get("report_html")
    print(f"  Paused for approval: {paused}")
    print(f"  Nothing produced before a human decided: {nothing_sent}")
    return paused and nothing_sent


def run_rejection_check() -> bool:
    """If a person rejects it, no client-facing report may be produced."""
    print("\nSafety: does 'send back for changes' really stop it?")
    print("-" * 70)
    graph = build_graph(persist=False)
    config = _run_to_approval(graph, "summit_fitness", "eval-reject", demo_glitch=False)
    graph.invoke(Command(resume={"decision": "rejected", "reviewer": "Eval"}), config=config)
    values = graph.get_state(config).values

    stopped = values.get("approval") == "rejected" and not values.get("report_html")
    print(f"  Rejected and no report produced: {stopped}")
    return stopped


def run_self_correction_check() -> bool:
    """With a deliberate error planted, the agent must catch and fix it."""
    print("\nSelf-correction: planted one wrong figure in the first draft")
    print("-" * 70)
    graph = build_graph(persist=False)
    config = _run_to_approval(graph, "brightwave_dental", "eval-glitch", demo_glitch=True)
    values = graph.get_state(config).values
    history = values.get("verify_history", [])

    caught = any(step["issues"] for step in history)
    fixed = not values.get("verify_issues")
    print(f"  Caught the wrong figure: {caught} (checked {len(history)} drafts)")
    print(f"  Final draft is clean: {fixed}")

    graph.invoke(
        Command(resume={"decision": "approved", "reviewer": "Eval"}), config=config
    )
    produced = bool(graph.get_state(config).values.get("report_html"))
    print(f"  Report produced after approval: {produced}")
    return caught and fixed and produced


def run_all_clients_check() -> bool:
    """Every client in the roster must get through to the approval queue."""
    print("\nScale: every client reaches the approval queue")
    print("-" * 70)
    graph = build_graph(persist=False)
    ids = [
        os.path.splitext(f)[0] for f in sorted(os.listdir(CLIENTS_DIR)) if f.endswith(".json")
    ]
    ok = True
    for cid in ids:
        config = _run_to_approval(graph, cid, f"eval-all-{cid}", demo_glitch=False)
        snap = graph.get_state(config)
        waiting = bool(snap.next) and "human_approval" in snap.next
        clean = not snap.values.get("verify_issues")
        ok = ok and waiting and clean
        print(f"  {cid:<22} queued: {waiting}  figures all verified: {clean}")
    return ok


def main() -> int:
    passed, total = run_number_check_cases()
    pause_ok = run_pause_check()
    reject_ok = run_rejection_check()
    correction_ok = run_self_correction_check()
    scale_ok = run_all_clients_check()

    all_ok = passed == total and pause_ok and reject_ok and correction_ok and scale_ok
    print("\n" + "=" * 70)
    print(f"  Fact-check cases      {passed}/{total} passed")
    print(f"  Waits for a human     {'OK' if pause_ok else 'FAILED'}")
    print(f"  Rejection stops it    {'OK' if reject_ok else 'FAILED'}")
    print(f"  Self-correction       {'OK' if correction_ok else 'FAILED'}")
    print(f"  All clients queued    {'OK' if scale_ok else 'FAILED'}")
    print("  RESULT:", "ALL GOOD" if all_ok else "SOMETHING FAILED")
    print("=" * 70)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
