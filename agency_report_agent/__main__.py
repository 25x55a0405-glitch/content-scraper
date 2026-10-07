"""Report Desk from the command line.

    python -m agency_report_agent demo                         # load the demo agency into the workspace
    python -m agency_report_agent import CLIENT 2026-09 ga4 traffic.csv
    python -m agency_report_agent draft 2026-09                # draft every client with data
    python -m agency_report_agent draft 2026-09 --client brightwave-dental --writer claude
    python -m agency_report_agent status 2026-09
    python -m agency_report_agent check CLIENT 2026-09 draft.md   # fact-check any text against the data
    python -m agency_report_agent serve                        # the web app

The workspace folder is REPORT_DESK_HOME (default ./report_desk_data), shared with the web app.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _desk(args):
    from .desk import Desk
    return Desk(args.home)


def cmd_demo(args) -> int:
    from .demo import agency as demo
    d = _desk(args)
    if d.store.list_clients(include_archived=True):
        print("The workspace already has clients; not loading the demo.")
        return 1
    demo.seed(d.store)
    d.close()
    print(f"Loaded {demo.AGENCY['name']}: {len(demo.CLIENTS)} clients. Try: python -m agency_report_agent draft {demo.PERIOD}")
    return 0


def cmd_import(args) -> int:
    from .importers import ImportError_, import_file
    d = _desk(args)
    try:
        data = Path(args.file).read_bytes()
        res = import_file(args.source, data, args.period)
        d.store.add_source(args.client, res, args.period, filename=Path(args.file).name, raw=data)
    except (ImportError_, OSError) as e:
        print(f"Couldn't import: {e}")
        return 1
    finally:
        d.close()
    for w in res.warnings:
        print(f"note: {w}")
    print(f"Imported {sum(len(r) for r in res.periods[args.period].values())} figures.")
    return 0


def cmd_draft(args) -> int:
    from . import graph as g
    d = _desk(args)
    try:
        if args.client:
            sts = [d.start(args.client, args.period, actor="command line", writer=args.writer, fresh=True)]
        else:
            queued = d.start_all(args.period, actor="command line", only_new=not args.again)
            d.wait()
            sts = [d.state(cid, args.period) for cid in queued]
        for st in sts:
            v = st["values"]
            ver = v.get("verification") or {}
            line = f"{st['client_id']:<28} {st['status_label']:<18}"
            if st["status"] == g.NEEDS_REVIEW:
                line += f"{ver.get('checked', 0):>3} figures checked, {len(ver.get('issues', []))} to fix, " \
                        f"{len(v.get('anomalies', []))} unusual"
                if v.get("draft_info", {}).get("fallback_reason"):
                    line += f"  (template used: {v['draft_info']['fallback_reason']})"
            elif st["status"] == g.BLOCKED:
                line += (v.get("problems") or [""])[0]
            elif st.get("error"):
                line += st["error"]
            print(line)
        if not sts:
            print("Nothing to draft (no data, or already drafted — use --again to redraft).")
        if args.show and args.client and sts and sts[0]["values"].get("draft"):
            print("\n" + sts[0]["values"]["draft"])
    finally:
        d.close()
    return 0


def cmd_status(args) -> int:
    d = _desk(args)
    for r in d.overview(args.period):
        print(f"{r['client']['id']:<28} {r['status_label']:<20} sources: {', '.join(r['sources']) or '—'}")
    d.close()
    return 0


def cmd_check(args) -> int:
    from .facts import build_facts
    from .store import previous_periods
    from .verify import verify
    d = _desk(args)
    try:
        c = d.store.client(args.client)
        if not c:
            print("No such client.")
            return 1
        cur, _ = d.store.period_data(args.client, args.period)
        prev_p, yago_p = previous_periods(args.period)
        prev, _ = d.store.period_data(args.client, prev_p)
        yago, _ = d.store.period_data(args.client, yago_p)
        sheet = build_facts(cur, None if prev.is_empty() else prev, None if yago.is_empty() else yago,
                            target=c.get("monthly_target"), currency=d.store.currency_symbol(),
                            conversion_label=c.get("conversion_label") or "conversions")
        text = Path(args.file).read_text(encoding="utf-8") if args.file != "-" else sys.stdin.read()
        v = verify(text, sheet)
    finally:
        d.close()
    print(f"{v.checked} figures checked, {len(v.issues)} problem(s).")
    for i in v.issues:
        print(f"- “{i.quote}”: {i.message}")
    return 0 if v.ok else 2


def cmd_serve(args) -> int:
    os.environ["REPORT_DESK_HOME"] = str(args.home)
    sys.argv = [sys.argv[0], "--host", args.host, "--port", str(args.port)]
    from .web.__main__ import main
    main()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m agency_report_agent", description="Report Desk")
    ap.add_argument("--home", default=os.environ.get("REPORT_DESK_HOME", "report_desk_data"),
                    help="workspace folder (default: REPORT_DESK_HOME or ./report_desk_data)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="load the demo agency").set_defaults(fn=cmd_demo)
    p = sub.add_parser("import", help="import one export file")
    p.add_argument("client"), p.add_argument("period"), p.add_argument("source",
                                                                        choices=["ga4", "google_ads", "search_console", "meta_ads", "generic"])
    p.add_argument("file")
    p.set_defaults(fn=cmd_import)
    p = sub.add_parser("draft", help="draft and fact-check reports for a month")
    p.add_argument("period"), p.add_argument("--client"), p.add_argument("--writer", choices=["template", "claude"])
    p.add_argument("--again", action="store_true", help="redraft reports that already have a draft")
    p.add_argument("--show", action="store_true", help="print the draft (with --client)")
    p.set_defaults(fn=cmd_draft)
    p = sub.add_parser("status", help="where each client's report is")
    p.add_argument("period")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("check", help="fact-check a text file against a client's data")
    p.add_argument("client"), p.add_argument("period"), p.add_argument("file", help="text file, or - for stdin")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("serve", help="run the web app")
    p.add_argument("--host", default="127.0.0.1"), p.add_argument("--port", type=int, default=8000)
    p.set_defaults(fn=cmd_serve)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
