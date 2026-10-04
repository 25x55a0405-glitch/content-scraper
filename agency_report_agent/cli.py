"""Run Report Desk from the command line, without the web app.

Most of the time you want the web app instead:

    python -m agency_report_agent.web

This command line is for a quick check that everything works, and for seeing
the fact-checking loop in plain text.

    python -m agency_report_agent.cli                 # draft every client, free
    python -m agency_report_agent.cli --demo-glitch   # watch it catch a wrong figure
    python -m agency_report_agent.cli --approve-all   # also approve and produce reports
    python -m agency_report_agent.cli --live          # write with Claude (needs a key)
"""

from __future__ import annotations

import argparse
import os

from . import batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft and fact-check this month's client reports.")
    parser.add_argument("--live", action="store_true", help="Write the drafts with Claude (costs tokens).")
    parser.add_argument(
        "--demo-glitch",
        action="store_true",
        help="Plant one wrong figure in each first draft, to show the fact-check working.",
    )
    parser.add_argument(
        "--approve-all",
        action="store_true",
        help="Approve everything automatically and produce the reports (skips the human step).",
    )
    parser.add_argument("--start-over", action="store_true", help="Begin a fresh round of reports.")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:  # noqa: BLE001 — python-dotenv is optional
        pass

    if args.start_over:
        batch.start_over()
        print("Started a fresh round.")

    mode = "LIVE (Claude)" if args.live else "FREE (no API key)"
    print(f"\nReport Desk — {mode}\n" + "-" * 56)

    result = batch.run_all(use_llm=args.live, demo_glitch=args.demo_glitch)
    print(f"Drafted {result['started']} report(s).\n")

    for row in batch.overview()["clients"]:
        line = f"  {row['name']:<24} {row['label']:<20} {row['figures_checked']} figures"
        if row["corrections"]:
            line += f", {row['corrections']} corrected"
        if row["anomalies"]:
            line += f", {len(row['anomalies'])} flagged for a human"
        print(line)

    if args.approve_all:
        print("\nApproving everything (demo only — normally a person does this)...")
        for row in batch.overview()["clients"]:
            if row["status"] == batch.NEEDS_REVIEW:
                done = batch.submit_decision(row["id"], "approved", reviewer="Command line")
                print(f"  {row['name']:<24} saved to {os.path.basename(done['report_path'])}")

    counts = batch.overview()["counts"]
    print(f"\n{counts['needs_review']} waiting for a human · {counts['approved']} approved")
    print("Open the web app to review them: python -m agency_report_agent.web\n")


if __name__ == "__main__":
    main()
