"""Run the agent's quality checks and print a one-page eval report.

This is the sheet you show a prospect: it proves the verification step catches
made-up numbers, and it runs the whole graph end to end on the sample client.

    python -m agency_report_agent.tests.run_evals

No API key needed — everything here runs in free mock mode.
"""

from __future__ import annotations

import json
import os
import sys

from ..graph import build_graph
from ..metrics import verify_draft

HERE = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(os.path.dirname(HERE), "sample_data")


def _load_cases() -> dict:
    with open(os.path.join(HERE, "test_cases.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def run_number_check_cases() -> tuple[int, int]:
    cases = _load_cases()
    with open(os.path.join(SAMPLE_DIR, cases["client_file"]), "r", encoding="utf-8") as fh:
        data = json.load(fh)

    passed = 0
    print("Number-verification checks")
    print("-" * 68)
    for case in cases["cases"]:
        issues = verify_draft(case["draft"], data)
        draft_is_clean = len(issues) == 0
        ok = draft_is_clean == case["should_pass"]
        passed += ok
        verdict = "PASS" if ok else "FAIL"
        expected = "clean" if case["should_pass"] else "should be flagged"
        got = "clean" if draft_is_clean else f"flagged {len(issues)}"
        print(f"  [{verdict}] {case['name']:<34} (expected {expected}, got {got})")
    return passed, len(cases["cases"])


def run_full_graph_check() -> bool:
    """Run the whole graph on the sample client and confirm it finishes clean."""
    print("\nEnd-to-end graph run (mock mode, auto-approved)")
    print("-" * 68)
    graph = build_graph()
    final = graph.invoke(
        {
            "client_file": os.path.join(SAMPLE_DIR, "brightwave_dental.json"),
            "use_llm": False,
            "auto_approve": True,
            "demo_glitch": False,
            "max_verify_attempts": 3,
            "log": [],
        }
    )
    produced = bool(final.get("final_report_path"))
    clean = not final.get("verify_issues")
    print(f"  Report produced: {produced}")
    print(f"  Final draft passed number check: {clean}")
    return produced and clean


def run_loop_recovery_check() -> bool:
    """With a deliberate glitch, the loop should catch it and still finish clean."""
    print("\nSelf-correction check (glitch injected on first draft)")
    print("-" * 68)
    graph = build_graph()
    final = graph.invoke(
        {
            "client_file": os.path.join(SAMPLE_DIR, "brightwave_dental.json"),
            "use_llm": False,
            "auto_approve": True,
            "demo_glitch": True,
            "max_verify_attempts": 3,
            "log": [],
        }
    )
    retried = final.get("verify_attempts", 0) >= 2
    clean = not final.get("verify_issues")
    print(f"  Verification ran more than once (caught the glitch): {retried}")
    print(f"  Final draft is clean after self-correction: {clean}")
    return retried and clean


def main() -> int:
    passed, total = run_number_check_cases()
    graph_ok = run_full_graph_check()
    loop_ok = run_loop_recovery_check()

    print("\n" + "=" * 68)
    all_ok = passed == total and graph_ok and loop_ok
    print(f"Number checks: {passed}/{total} passed")
    print(f"End-to-end run: {'OK' if graph_ok else 'FAILED'}")
    print(f"Self-correction: {'OK' if loop_ok else 'FAILED'}")
    print("RESULT:", "ALL GOOD ✅" if all_ok else "SOMETHING FAILED ❌")
    print("=" * 68)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
