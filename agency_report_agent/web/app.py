"""Report Desk — the web app an agency actually uses.

Run it with:
    python -m agency_report_agent.web

Then open http://127.0.0.1:8000
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import batch
from ..metrics import summarise_channels, totals

HERE = os.path.dirname(__file__)

app = FastAPI(title="Report Desk")
app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(HERE, "templates"))


def _period() -> str:
    clients = batch.load_clients()
    return clients[0]["period"] if clients else ""


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, flash: Optional[str] = None):
    data = batch.overview()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={**data, "period": _period(), "flash": flash},
    )


@app.post("/run")
def run(demo_glitch: Optional[str] = Form(None)):
    use_llm = os.environ.get("REPORT_DESK_LIVE") == "1"
    result = batch.run_all(use_llm=use_llm, demo_glitch=bool(demo_glitch))
    msg = f"Drafted and fact-checked {result['started']} reports."
    return RedirectResponse(f"/?flash={msg}", status_code=303)


@app.post("/start-over")
def start_over():
    batch.start_over()
    return RedirectResponse("/", status_code=303)


def _client_or_404(client_id: str):
    for c in batch.load_clients():
        if c["id"] == client_id:
            return c
    return None


@app.get("/review/{client_id}", response_class=HTMLResponse)
def review(request: Request, client_id: str):
    client = _client_or_404(client_id)
    if client is None:
        return RedirectResponse("/", status_code=303)

    info = batch.status_of(client_id)
    if info["status"] not in (batch.NEEDS_REVIEW, batch.CHANGES_REQUESTED):
        return RedirectResponse("/", status_code=303)

    data = info["state"].get("data", {})
    t = totals(data)
    rows = summarise_channels(data)
    summary_rows = [
        ("Total sessions", f"{t['total_sessions']:,}"),
        ("Total enquiries", f"{t['total_conversions']:,}"),
        ("Change on last month", f"{t['total_conversions_change']:+.1f}%"),
        ("Monthly target", f"{t['leads_target']:,}"),
    ]
    for r in rows:
        change = "—" if r["sessions_change"] is None else f"{r['sessions_change']:+.1f}%"
        summary_rows.append((r["channel"], change))

    paragraphs = [p.strip() for p in (info.get("draft") or "").split("\n\n") if p.strip()]

    return templates.TemplateResponse(
        request=request,
        name="review.html",
        context={
            "agency": batch.load_agency(),
            "period": _period(),
            "client": client,
            "info": info,
            "draft_paragraphs": paragraphs,
            "summary_rows": summary_rows,
        },
    )


@app.post("/review/{client_id}")
def submit_review(
    client_id: str,
    decision: str = Form(...),
    note: Optional[str] = Form(None),
    reviewer: Optional[str] = Form(None),
):
    batch.submit_decision(client_id, decision, note=note or None, reviewer=reviewer)
    msg = (
        "Report approved and generated."
        if decision == "approved"
        else "Sent back for changes."
    )
    return RedirectResponse(f"/?flash={msg}", status_code=303)


@app.get("/report/{client_id}", response_class=HTMLResponse)
def report_view(request: Request, client_id: str):
    client = _client_or_404(client_id)
    info = batch.status_of(client_id)
    if client is None or not info["state"].get("report_html"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="report_view.html",
        context={
            "agency": batch.load_agency(),
            "period": _period(),
            "client": client,
            "info": info,
        },
    )


@app.get("/report/{client_id}/raw", response_class=HTMLResponse)
def report_raw(client_id: str):
    info = batch.status_of(client_id)
    html = info["state"].get("report_html")
    if not html:
        return RedirectResponse("/", status_code=303)
    return HTMLResponse(html)
