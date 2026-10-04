"""Run the Agency Report Agent from the command line.

Examples
--------
Free demo, no API key, watch the number-check loop catch a mistake:
    python -m agency_report_agent.cli --demo-glitch

Free demo, auto-approve (no prompt), good for a quick run:
    python -m agency_report_agent.cli --auto-approve

Live mode with Claude (needs ANTHROPIC_API_KEY in your environment or .env):
    python -m agency_report_agent.cli --live
"""

from __future__ import annotations

import argparse
import os

from .graph import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft and self-check a client marketing report.")
    parser.add_argument(
        "--client",
        default=os.path.join(os.path.dirname(__file__), "sample_data", "brightwave_dental.json"),
        help="Path to the client's data file (JSON).",
    )
    parser.add_argument("--live", action="store_true", help="Use Claude to write the draft (costs tokens).")
    parser.add_argument("--auto-approve", action="store_true", help="Skip the human approval prompt.")
    parser.add_argument(
        "--demo-glitch",
        action="store_true",
        help="Inject one wrong number on the first draft to show the verification loop working.",
    )
    parser.add_argument("--max-verify", type=int, default=3, help="Max times the number-check loop may retry.")
    args = parser.parse_args()

    # Load a .env file if python-dotenv is installed (optional convenience).
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:  # noqa: BLE001
        pass

    graph = build_graph()

    initial_state = {
        "client_file": args.client,
        "use_llm": args.live,
        "auto_approve": args.auto_approve,
        "demo_glitch": args.demo_glitch,
        "max_verify_attempts": args.max_verify,
        "agent_model": os.environ.get("AGENT_MODEL"),
        "log": [],
    }

    mode = "LIVE (Claude)" if args.live else "MOCK (free, no API key)"
    print(f"\nAgency Report Agent — {mode}\n" + "-" * 40)

    final = graph.invoke(initial_state)

    print("-" * 40)
    if final.get("final_report_path"):
        print(f"Done. Report saved to: {final['final_report_path']}")
    elif final.get("approval") == "rejected":
        print("Stopped: the draft was rejected, so nothing was sent.")
    else:
        print("Stopped before producing a report. See the log above.")


if __name__ == "__main__":
    main()
