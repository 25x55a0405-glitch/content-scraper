"""The Report Desk agent: one client, one month, from uploaded data to an approved report.

                 ┌──────────────┐ blocking problem
        START ─> │  load_data   │ ───────────────────────────────> END (blocked, with the reason)
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  build_facts │  fact sheet + unusual movements (arithmetic only)
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐   wrong figures and attempts left
            ┌──> │    draft     │ <────────────────────────────┐
            │    └──────┬───────┘                              │
            │           ▼                                      │
            │    ┌──────────────┐                              │
            │    │  fact_check  │ ─────────────────────────────┘
            │    └──────┬───────┘
            │           ▼
            │    ┌──────────────┐  edit ─> re-check, back to review
            │    │    review    │  the run pauses here until a person decides
            │    └──┬────┬───┬──┘
            │       │    │   └── reject ──────────────────────────> END
            └───────┘    │  request changes / new notes -> redraft
                         ▼ approve
                 ┌──────────────┐
                 │    render    │  branded HTML + PDF, saved as a new version
                 └──────┬───────┘
                        ▼
                       END

Nothing reaches a client without a person approving it, and a draft with a
figure the fact checker can't back can't be approved unless the reviewer
explicitly confirms each flagged figure (which is recorded in the audit log).
"""

from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .anomalies import Anomaly, find_anomalies
from .drafting import DraftRequest
from .facts import FactSheet, build_facts
from .llm import write_draft
from .model import METRICS, TOTAL, PeriodData, channel_label, period_label
from .store import SOURCE_NAMES, Store, previous_periods
from .verify import Verification, verify

MAX_ATTEMPTS = 3        # drafts per cycle before handing to a person with the issues shown

# Statuses, as the app shows them
BLOCKED = "blocked"
NEEDS_REVIEW = "needs_review"
APPROVED = "approved"
REJECTED = "rejected"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RunState(TypedDict, total=False):
    # inputs
    client_id: str
    period: str
    writer: str                     # template | claude
    model: Optional[str]
    started_by: str
    # data
    problems: list[str]             # blocking — the run ends
    warnings: list[str]             # shown to the reviewer
    notes: list[str]                # source conflicts
    sheet: dict
    anomalies: list[dict]
    # drafting
    draft: str
    draft_info: dict                # writer, model, fallback reason, tokens
    attempts: int                   # drafts in the current cycle
    verification: dict
    history: Annotated[list[dict], operator.add]
    change_request: str
    next_steps: str
    # review
    status: str
    review_message: str             # feedback for the reviewer from the last action
    decision: dict
    reviewer: str
    approved_at: str
    overrides: list[dict]
    # output
    report: dict
    log: Annotated[list[str], operator.add]


def build_graph(store: Store, checkpointer=None):
    """Compile the agent for a workspace. Nodes close over the store."""

    # ------------------------------------------------------------------ load_data
    def load_data(state: RunState) -> dict:
        cid, period = state["client_id"], state["period"]
        client = store.client(cid)
        problems: list[str] = []
        warnings: list[str] = []
        if client is None:
            return {"status": BLOCKED, "problems": ["This client doesn't exist any more."],
                    "log": ["Stopped: client not found."]}
        sources = store.sources(cid, period)
        month = period_label(period)
        if not sources:
            problems.append(f"No data has been uploaded for {month}. Upload at least the GA4 "
                            f"Traffic acquisition export for the month.")
            return {"status": BLOCKED, "problems": problems, "warnings": [],
                    "log": [f"Stopped: no data for {month}."]}
        cur, notes = store.period_data(cid, period)
        prev_p, yago_p = previous_periods(period)
        prev, _ = store.period_data(cid, prev_p)
        yago, _ = store.period_data(cid, yago_p)
        if not any(cur.get(s, m) for s in cur.values for m in ("sessions", "conversions", "spend")):
            problems.append(f"The files uploaded for {month} contain no sessions, conversions or spend. "
                            f"Check that the right exports were uploaded.")
        types = {s["type"] for s in sources}
        prev_types = {s["type"] for s in store.sources(cid, prev_p)}
        for t in sorted(prev_types - types - {"manual", "generic"}):
            warnings.append(f"{SOURCE_NAMES.get(t, t)} was uploaded for {period_label(prev_p)} but not for "
                            f"{month}, so its figures are missing from this report. Upload it, or ignore this "
                            f"if the account was paused.")
        if "ga4" not in types and "generic" not in types and "manual" not in types:
            warnings.append("No GA4 export for this month: sessions and conversions come only from the ad "
                            "platforms, so organic and direct traffic are missing.")
        agency_ccy = store.agency().get("currency", "GBP")
        ccys = {SOURCE_NAMES.get(x["type"], x["type"]): (x.get("extras") or {}).get("currency") for x in sources
                if (x.get("extras") or {}).get("currency")}
        if len({c for c in ccys.values()}) > 1:
            warnings.append("The files use different currencies (" + ", ".join(f"{k}: {v}" for k, v in ccys.items())
                            + "). Spend has been added together as-is, so totals and cost per "
                            + "conversion are wrong. Export them in one currency.")
        else:
            for name, ccy in ccys.items():
                if ccy.upper() != agency_ccy.upper():
                    warnings.append(f"{name} is in {ccy.upper()} but your agency is set to {agency_ccy}. The report "
                                    f"will show these amounts in {agency_ccy}; change the currency in Settings or "
                                    f"re-export in {agency_ccy}.")
        for s in sources:
            for w in s.get("warnings", []):
                warnings.append(f"{SOURCE_NAMES.get(s['type'], s['type'])}: {w}")
        if prev.is_empty():
            warnings.append(f"No data for {period_label(prev_p)}, so the report has no month-on-month "
                            f"comparisons.")
        if problems:
            return {"status": BLOCKED, "problems": problems, "warnings": warnings, "notes": notes,
                    "log": ["Stopped: " + problems[0]]}
        target = client.get("monthly_target") or None
        sheet = build_facts(cur, prev if not prev.is_empty() else None, yago if not yago.is_empty() else None,
                            target=float(target) if target else None, currency=store.currency_symbol(),
                            conversion_label=client.get("conversion_label") or "conversions")
        n_src = ", ".join(sorted(SOURCE_NAMES.get(t, t) for t in types))
        return {"problems": [], "warnings": warnings, "notes": notes, "sheet": sheet.to_dict(),
                "attempts": 0, "status": "drafting",
                "log": [f"Loaded {month} from {n_src}; {len(sheet.facts)} figures on the fact sheet."]}

    def after_load(state: RunState) -> str:
        return "stop" if state.get("problems") else "go"

    # ---------------------------------------------------------------- build_facts
    def find_unusual(state: RunState) -> dict:
        sheet = FactSheet.from_dict(state["sheet"])
        anomalies = find_anomalies(sheet)
        msg = (f"Flagged {len(anomalies)} unusual movement{'s' if len(anomalies) != 1 else ''} for review."
               if anomalies else "No unusual movements this month.")
        return {"anomalies": [a.to_dict() for a in anomalies], "log": [msg]}

    # ---------------------------------------------------------------------- draft
    def draft(state: RunState) -> dict:
        sheet = FactSheet.from_dict(state["sheet"])
        client = store.client(state["client_id"]) or {}
        agency = store.agency()
        ver = state.get("verification") or {}
        failed = ver and not ver.get("ok", True)
        attempts = state.get("attempts", 0)
        req = DraftRequest(
            sheet=sheet, client=client, agency=agency,
            anomalies=[Anomaly.from_dict(a) for a in state.get("anomalies", [])],
            data_notes=state.get("notes", []), next_steps=state.get("next_steps", ""),
            change_request=state.get("change_request", ""),
            previous_draft=state.get("draft", "") if (failed or state.get("change_request")) else "",
            verifier_feedback=Verification.from_dict(ver).feedback_for_drafter() if failed else "")
        res = write_draft(req, state.get("writer") or "template", state.get("model"))
        info = res.to_dict()
        info.pop("text")
        what = "Claude" if res.writer == "claude" else "the template writer"
        line = f"Draft {attempts + 1} written by {what}"
        if res.fallback_reason:
            line += f" ({res.fallback_reason})"
        update = {"draft": res.text, "draft_info": info, "attempts": attempts + 1, "log": [line + "."],
                  "review_message": ""}
        if state.get("change_request") and state.get("draft") and \
                res.text.split() == state["draft"].split():
            update["review_message"] = ("The writer returned the same text, so nothing changed. Rephrase the "
                                        "request, or edit the draft yourself.")
            update["log"] = [line + ". It came back unchanged."]
        return update

    # ----------------------------------------------------------------- fact_check
    def fact_check(state: RunState) -> dict:
        sheet = FactSheet.from_dict(state["sheet"])
        v = verify(state["draft"], sheet)
        entry = {"at": _now(), "attempt": state.get("attempts", 0),
                 "writer": state.get("draft_info", {}).get("writer", ""),
                 "checked": v.checked, "issues": len(v.issues),
                 "examples": [i.message for i in v.issues[:3]]}
        line = (f"Fact check passed: {v.checked} figures, all backed by the data." if v.ok else
                f"Fact check found {len(v.issues)} problem{'s' if len(v.issues) != 1 else ''} "
                f"in {v.checked} figures.")
        return {"verification": v.to_dict(), "history": [entry], "log": [line]}

    def after_check(state: RunState) -> str:
        ok = state["verification"]["ok"]
        writer = state.get("draft_info", {}).get("writer")
        if not ok and writer == "claude" and state.get("attempts", 0) < MAX_ATTEMPTS:
            return "redraft"
        return "review"

    # --------------------------------------------------------------------- review
    def review(state: RunState) -> dict:
        ver = state.get("verification", {})
        decision = interrupt({
            "client_id": state["client_id"], "period": state["period"],
            "fact_check_ok": ver.get("ok", False), "issues": len(ver.get("issues", [])),
        })
        decision = dict(decision or {})
        action = decision.get("action")
        reviewer = (decision.get("reviewer") or "").strip()
        out: dict[str, Any] = {"decision": decision, "reviewer": reviewer, "review_message": ""}
        if not reviewer and action in ("approve", "reject"):
            out["review_message"] = "Choose who is reviewing before approving or rejecting."
            out["decision"] = {"action": "stay"}
            return out
        anomalies = state.get("anomalies", [])
        notes_changed = False
        expl = decision.get("explanations") or {}
        if expl:
            for a in anomalies:
                new = str(expl.get(a["id"], a.get("explanation", ""))).strip()[:600]
                if new != a.get("explanation", ""):
                    a["explanation"] = new
                    notes_changed = True
            out["anomalies"] = anomalies
        if "next_steps" in decision and (decision.get("next_steps") or "").strip() != state.get("next_steps", ""):
            out["next_steps"] = (decision.get("next_steps") or "").strip()[:3000]
            notes_changed = True

        if action == "edit" or (action == "approve" and decision.get("text") is not None
                                and decision["text"] != state.get("draft")):
            text = (decision.get("text") or "").strip()
            if not text:
                out["review_message"] = "The draft can't be empty."
                out["decision"] = {"action": "stay"}
                return out
            sheet = FactSheet.from_dict(state["sheet"])
            v = verify(text + "\n", sheet)
            out["draft"] = text + "\n"
            out["verification"] = v.to_dict()
            out["draft_info"] = dict(state.get("draft_info", {}), edited_by=reviewer or "reviewer")
            out["history"] = [{"at": _now(), "attempt": "edit", "writer": "reviewer", "checked": v.checked,
                               "issues": len(v.issues), "examples": [i.message for i in v.issues[:3]]}]
            out["log"] = [f"{reviewer or 'Reviewer'} edited the draft; fact check "
                          + ("passed." if v.ok else f"found {len(v.issues)} problem(s).")]
            if action == "approve" and not v.ok and not decision.get("confirm_flagged"):
                out["review_message"] = ("Your edit introduced figures the fact checker can't back. "
                                         "Fix them, or confirm each one before approving.")
                out["decision"] = {"action": "stay"}
            elif action == "edit":
                out["decision"] = {"action": "stay"}
            return out
        if action == "approve":
            if not ver.get("ok", False) and not decision.get("confirm_flagged"):
                out["review_message"] = ("Some figures couldn't be backed by the data. Fix them, or confirm "
                                         "each one before approving.")
                out["decision"] = {"action": "stay"}
            return out
        if action == "request_changes":
            req = (decision.get("change_request") or "").strip()[:3000]
            if not req and not notes_changed:
                out["review_message"] = "Say what should change."
                out["decision"] = {"action": "stay"}
                return out
            out["change_request"] = req
            out["attempts"] = 0
            out["verification"] = {}
            out["log"] = [f"{reviewer or 'Reviewer'} asked for changes: {req[:200]}" if req else
                          f"{reviewer or 'Reviewer'} updated the notes; redrafting."]
            return out
        if action == "update_notes":
            out["attempts"] = 0
            out["verification"] = {}
            out["change_request"] = ("Update the Worth a look and Next month sections to use the reviewer's "
                                     "latest explanations and notes. Change nothing else.")
            out["log"] = [f"{reviewer or 'Reviewer'} updated explanations and notes; redrafting."]
            out["decision"] = {"action": "request_changes"}
            return out
        if action == "reject":
            out["log"] = [f"{reviewer} rejected this month's report: "
                          f"{(decision.get('reason') or 'no reason given')[:300]}"]
            return out
        out["decision"] = {"action": "stay"}
        return out

    def after_review(state: RunState) -> str:
        action = (state.get("decision") or {}).get("action")
        if action == "approve":
            return "approve"
        if action == "request_changes":
            return "redraft"
        if action == "reject":
            return "reject"
        return "stay"

    def mark_rejected(state: RunState) -> dict:
        store.audit(state.get("reviewer", ""), "rejected", state["client_id"], state["period"],
                    (state.get("decision") or {}).get("reason", ""))
        return {"status": REJECTED}

    # --------------------------------------------------------------------- render
    def render(state: RunState) -> dict:
        from .render import render_report, html_to_pdf

        decision = state.get("decision") or {}
        ver = Verification.from_dict(state.get("verification", {}))
        overrides = []
        if not ver.ok:
            overrides = [{"quote": i.quote, "sentence": i.sentence, "message": i.message} for i in ver.issues]
            for o in overrides:
                store.audit(state.get("reviewer", ""), "confirmed flagged figure", state["client_id"],
                            state["period"], f"{o['quote']} — {o['message']}")
        approved_at = _now()
        client = store.client(state["client_id"]) or {}
        sheet = FactSheet.from_dict(state["sheet"])
        html = render_report(store, client, sheet, state["draft"],
                             [Anomaly.from_dict(a) for a in state.get("anomalies", [])],
                             notes=state.get("notes", []), reviewer=state.get("reviewer", ""),
                             approved_at=approved_at, verification=ver)
        pdf, pdf_error = html_to_pdf(html)
        meta = {"client_id": state["client_id"], "period": state["period"], "reviewer": state.get("reviewer"),
                "approved_at": approved_at, "writer": state.get("draft_info", {}).get("writer"),
                "model": state.get("draft_info", {}).get("model"), "checked": ver.checked,
                "confirmed_flags": len(overrides), "draft": state["draft"], "pdf_error": pdf_error,
                "comment": (decision.get("comment") or "")[:1000]}
        saved = store.save_report(state["client_id"], state["period"], html, meta, pdf)
        store.audit(state.get("reviewer", ""), "approved", state["client_id"], state["period"],
                    f"version {saved['version']}, {ver.checked} figures checked"
                    + (f", {len(overrides)} flagged figure(s) confirmed by reviewer" if overrides else ""))
        line = f"Approved by {state.get('reviewer')}; report version {saved['version']} saved"
        line += " with PDF." if pdf else f" (PDF unavailable: {pdf_error})."
        return {"status": APPROVED, "approved_at": approved_at, "report": saved, "overrides": overrides,
                "log": [line]}

    # ---------------------------------------------------------------------- wire
    def mark_review(state: RunState) -> dict:
        return {"status": NEEDS_REVIEW}

    g = StateGraph(RunState)
    g.add_node("load_data", load_data)
    g.add_node("find_unusual", find_unusual)
    g.add_node("draft", draft)
    g.add_node("fact_check", fact_check)
    g.add_node("ready_for_review", mark_review)
    g.add_node("review", review)
    g.add_node("render", render)
    g.add_node("rejected", mark_rejected)

    g.add_edge(START, "load_data")
    g.add_conditional_edges("load_data", after_load, {"stop": END, "go": "find_unusual"})
    g.add_edge("find_unusual", "draft")
    g.add_edge("draft", "fact_check")
    g.add_conditional_edges("fact_check", after_check, {"redraft": "draft", "review": "ready_for_review"})
    g.add_edge("ready_for_review", "review")
    g.add_conditional_edges("review", after_review,
                            {"approve": "render", "redraft": "draft", "reject": "rejected", "stay": "review"})
    g.add_edge("render", END)
    g.add_edge("rejected", END)
    return g.compile(checkpointer=checkpointer)
