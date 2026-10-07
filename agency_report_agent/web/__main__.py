"""Start the Report Desk web app.

    python -m agency_report_agent.web                    # http://127.0.0.1:8000, this computer only
    REPORT_DESK_PASSWORD=… python -m agency_report_agent.web --host 0.0.0.0   # on your network

Without a team password the app only listens on this computer.
"""
import argparse
import os
import sys

import uvicorn


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the Report Desk web app.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = ap.parse_args()
    local = args.host in ("127.0.0.1", "localhost", "::1")
    if not local and not os.environ.get("REPORT_DESK_PASSWORD"):
        sys.exit("Refusing to listen on the network without a team password. "
                 "Set REPORT_DESK_PASSWORD first.")
    print(f"\n  Report Desk running at http://{'127.0.0.1' if local else args.host}:{args.port}\n")
    uvicorn.run("agency_report_agent.web.app:create_app", factory=True, host=args.host, port=args.port,
                proxy_headers=True, forwarded_allow_ips="127.0.0.1")


if __name__ == "__main__":
    main()
