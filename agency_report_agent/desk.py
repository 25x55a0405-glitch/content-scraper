"""Report Desk: runs the agent for an agency's clients and tracks each run.

The web app and the command line both talk to this. It owns the workspace
store, the compiled graph with its SQLite checkpointer (so a report waiting
for review survives a restart), a registry of runs per client and month, and
a small worker pool so a whole client list can be drafted at once.
"""

from __future__ import annotations

import sqlite3
import threading
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from . import graph as g
from .model import period_label
from .store import Store

RUNNING = "running"
NOT_STARTED = "not_started"
FAILED = "failed"

STATUS_LABELS = {
    NOT_STARTED: "Not started",
    RUNNING: "Drafting…",
    g.BLOCKED: "Needs data",
    g.NEEDS_REVIEW: "Ready for review",
    g.APPROVED: "Approved",
    g.REJECTED: "Not sending",
    FAILED: "Something went wrong",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DeskError(Exception):
    """A user-facing reason an action can't be done."""


class Desk:
    def __init__(self, home: str | Path, workers: int = 4):
        self.store = Store(home)
        self._conn = sqlite3.connect(str(self.store.home / "runs.sqlite"), check_same_thread=False)
        self.graph = g.build_graph(self.store, SqliteSaver(self._conn))
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._reg_lock = threading.RLock()
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="report-desk")
        self._futures: list = []
        # A run interrupted by a restart mid-draft can't still be running.
        with self._reg_lock:
            reg = self._registry()
            for cid, periods in reg.items():
                for period, rec in periods.items():
                    if rec.get("status") == RUNNING:
                        st = self._graph_status(rec) if rec.get("thread") else NOT_STARTED
                        if st not in (g.NEEDS_REVIEW, g.APPROVED, g.REJECTED, g.BLOCKED, NOT_STARTED):
                            st = FAILED
                            rec["error"] = "Interrupted by a restart while drafting. Start it again."
                        rec["status"] = st
                        rec["queued"] = False
            self.store._write_json(self._reg_path(), reg)

    def close(self) -> None:
        self._pool.shutdown(wait=True)
        self._conn.close()

    # ------------------------------------------------------------- registry
    def _reg_path(self) -> Path:
        return self.store.home / "runs.json"

    def _registry(self) -> dict:
        return self.store._read_json(self._reg_path(), {}) or {}

    def _record(self, cid: str, period: str) -> Optional[dict]:
        return self._registry().get(cid, {}).get(period)

    def _set_record(self, cid: str, period: str, **fields) -> dict:
        with self._reg_lock:
            reg = self._registry()
            rec = dict(reg.get(cid, {}).get(period) or {})
            rec.update(fields, updated=_now())
            reg.setdefault(cid, {})[period] = rec
            self.store._write_json(self._reg_path(), reg)
            return rec

    @staticmethod
    def _config(rec: dict) -> dict:
        return {"configurable": {"thread_id": rec["thread"]}}

    # ---------------------------------------------------------------- start
    def start(self, client_id: str, period: str, actor: str = "", writer: Optional[str] = None,
              model: Optional[str] = None, fresh: bool = False, _queued: bool = False) -> dict:
        """Run the agent for one client and month until it needs a person (or finishes)."""
        self.store.check_id(client_id)
        self.store.check_period(period)
        client = self.store.client(client_id)
        if client is None:
            raise DeskError("That client doesn't exist.")
        with self._locks[f"{client_id}:{period}"]:
            rec = self._record(client_id, period)
            if rec and not (fresh or _queued) and rec.get("status") in (RUNNING, g.NEEDS_REVIEW):
                return self.state(client_id, period)
            agency = self.store.agency()
            writer = writer or agency.get("drafting") or "template"
            model = model or agency.get("model")
            run = (rec or {}).get("run", 0) + 1
            rec = self._set_record(client_id, period, run=run, thread=f"{client_id}:{period}:{run}",
                                   status=RUNNING, queued=False, writer=writer, started_by=actor,
                                   started=_now(), error="")
            self.store.audit(actor, "started report", client_id, period,
                             f"run {run}, writer: {writer}" + (f" ({model})" if writer == "claude" else ""))
            try:
                self.graph.invoke({"client_id": client_id, "period": period, "writer": writer, "model": model,
                                   "started_by": actor, "log": [f"Started by {actor or 'the system'}."]},
                                  self._config(rec))
                self._set_record(client_id, period, status=self._graph_status(rec))
            except Exception as e:  # noqa: BLE001 — record it for the agency, never crash the app
                self._set_record(client_id, period, status=FAILED, error=f"{type(e).__name__}: {e}"[:500],
                                 trace=traceback.format_exc()[-4000:])
        return self.state(client_id, period)

    def start_in_background(self, client_id: str, period: str, actor: str = "", fresh: bool = False,
                            writer: Optional[str] = None):
        """Queue a run; the dashboard shows it as drafting straight away."""
        with self._reg_lock:
            rec = self._record(client_id, period)
            if rec and rec.get("status") == RUNNING:
                return None
            if rec and rec.get("status") == g.NEEDS_REVIEW and not fresh:
                return None
            self._set_record(client_id, period, status=RUNNING, queued=True, error="")
        fut = self._pool.submit(self._safe_start, client_id, period, actor, writer)
        self._futures.append(fut)
        return fut

    def _safe_start(self, client_id, period, actor, writer):
        try:
            return self.start(client_id, period, actor, writer=writer, _queued=True)
        except Exception as e:  # noqa: BLE001
            self._set_record(client_id, period, status=FAILED, queued=False, error=str(e)[:500])

    def start_all(self, period: str, actor: str = "", client_ids: Optional[list[str]] = None,
                  only_new: bool = True) -> list[str]:
        """Draft every active client's report for a month, in parallel. Returns the ids queued."""
        self.store.check_period(period)
        queued = []
        for c in self.store.list_clients():
            if client_ids is not None and c["id"] not in client_ids:
                continue
            st = self.status(c["id"], period)
            if only_new and st in (g.NEEDS_REVIEW, g.APPROVED, RUNNING, g.REJECTED):
                continue
            if not self.store.sources(c["id"], period):
                continue
            if self.start_in_background(c["id"], period, actor) is not None:
                queued.append(c["id"])
        return queued

    def wait(self) -> None:
        """Block until queued work is done (tests and the command line)."""
        while self._futures:
            self._futures.pop(0).result()

    # --------------------------------------------------------------- review
    def _check_reviewable(self, rec: Optional[dict], decision: dict, queued: bool = False) -> None:
        ok_status = (g.NEEDS_REVIEW, RUNNING) if queued else (g.NEEDS_REVIEW,)
        if not rec or rec.get("status") not in ok_status:
            raise DeskError("This report isn't waiting for review.")
        if decision.get("action") == "request_changes" and rec.get("writer") != "claude" and \
                (decision.get("change_request") or "").strip():
            raise DeskError("The template writer can't follow written requests. Edit the text directly, "
                            "or switch drafting to Claude in Settings and draft again.")

    def review_in_background(self, client_id: str, period: str, decision: dict, actor: str = ""):
        """For decisions that redraft (slow with Claude): queue it and show the report as drafting."""
        with self._reg_lock:
            rec = self._record(client_id, period)
            self._check_reviewable(rec, decision)
            self._set_record(client_id, period, status=RUNNING)
        fut = self._pool.submit(self._safe_review, client_id, period, decision, actor)
        self._futures.append(fut)
        return fut

    def _safe_review(self, client_id, period, decision, actor):
        try:
            return self.review(client_id, period, decision, actor, _queued=True)
        except Exception as e:  # noqa: BLE001
            rec = self._record(client_id, period) or {}
            if rec.get("status") == RUNNING:
                self._set_record(client_id, period, status=self._graph_status(rec), error=str(e)[:500])

    def review(self, client_id: str, period: str, decision: dict, actor: str = "", _queued: bool = False) -> dict:
        """Resume a run waiting for review with the reviewer's decision."""
        with self._locks[f"{client_id}:{period}"]:
            rec = self._record(client_id, period)
            self._check_reviewable(rec, decision, _queued)
            snap = self.graph.get_state(self._config(rec))
            if "review" not in (snap.next or ()):
                raise DeskError("This report isn't waiting for review.")
            decision = dict(decision)
            self._set_record(client_id, period, status=RUNNING)
            try:
                self.graph.invoke(Command(resume=decision), self._config(rec))
                status = self._graph_status(rec)
                self._set_record(client_id, period, status=status)
            except Exception as e:  # noqa: BLE001
                self._set_record(client_id, period, status=FAILED, error=f"{type(e).__name__}: {e}"[:500],
                                 trace=traceback.format_exc()[-4000:])
                raise DeskError("Something went wrong applying that decision. It has been logged.") from e
            if decision.get("action") == "edit":
                self.store.audit(actor, "edited draft", client_id, period)
            elif decision.get("action") == "request_changes":
                self.store.audit(actor, "requested changes", client_id, period,
                                 (decision.get("change_request") or "")[:500])
        return self.state(client_id, period)

    # ---------------------------------------------------------------- state
    def _graph_status(self, rec: dict) -> str:
        try:
            snap = self.graph.get_state(self._config(rec))
        except Exception:  # noqa: BLE001
            return FAILED
        values = snap.values or {}
        if "review" in (snap.next or ()):
            return g.NEEDS_REVIEW
        return values.get("status") or FAILED

    def status(self, client_id: str, period: str) -> str:
        rec = self._record(client_id, period)
        return rec.get("status", NOT_STARTED) if rec else NOT_STARTED

    def state(self, client_id: str, period: str) -> dict:
        rec = self._record(client_id, period) or {}
        values: dict[str, Any] = {}
        if rec.get("thread"):
            try:
                values = dict(self.graph.get_state(self._config(rec)).values or {})
            except Exception:  # noqa: BLE001
                values = {}
        status = rec.get("status", NOT_STARTED)
        return {"client_id": client_id, "period": period, "status": status,
                "status_label": STATUS_LABELS.get(status, status), "run": rec.get("run", 0),
                "writer": rec.get("writer"), "error": rec.get("error", ""), "updated": rec.get("updated"),
                "values": values, "reports": self.store.reports(client_id, period)}

    def overview(self, period: str) -> list[dict]:
        rows = []
        for c in self.store.list_clients():
            st = self.state(c["id"], period)
            v = st["values"]
            ver = v.get("verification") or {}
            rows.append({
                "client": c, "status": st["status"], "status_label": st["status_label"],
                "has_data": bool(self.store.sources(c["id"], period)),
                "sources": [s["type"] for s in self.store.sources(c["id"], period)],
                "issues": len(ver.get("issues", [])) if ver else 0,
                "checked": ver.get("checked", 0) if ver else 0,
                "anomalies": len(v.get("anomalies", []) or []),
                "warnings": len(v.get("warnings", []) or []),
                "problems": v.get("problems", []) or [],
                "reports": st["reports"], "updated": st["updated"], "error": st["error"],
                "period_label": period_label(period),
            })
        return rows
