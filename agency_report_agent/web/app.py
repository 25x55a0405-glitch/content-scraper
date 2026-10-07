"""Report Desk — the web app an agency's team uses every month.

    python -m agency_report_agent.web            # http://127.0.0.1:8000

Configuration (environment variables):
    REPORT_DESK_HOME        workspace folder (default: ./report_desk_data)
    REPORT_DESK_PASSWORD    team password; required unless bound to localhost
    REPORT_DESK_SECRET      cookie signing key (generated and kept in the workspace if unset)
    REPORT_DESK_SECURE_COOKIES=1   when served over HTTPS
    ANTHROPIC_API_KEY       lets the Claude writer be switched on in Settings
"""

from __future__ import annotations

import hmac
import math
from contextlib import asynccontextmanager
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import date
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware

from .. import graph as g
from ..anomalies import Anomaly
from ..desk import RUNNING, STATUS_LABELS, Desk, DeskError
from ..facts import FactSheet
from ..importers import SOURCES, ImportError_, import_file
from ..importers.common import MAX_UPLOAD_BYTES
from ..llm import MODELS, claude_available
from ..model import BASE_METRICS, CHANNELS, METRICS, TOTAL, channel_label, is_period, period_label, shift_period
from ..render import md_to_html, render_report, strip_citations
from ..store import CURRENCY_SYMBOLS, SOURCE_NAMES, StoreError
from ..verify import Verification

HERE = Path(__file__).parent

SOURCE_HELP = {
    "ga4": ("GA4 — Traffic acquisition",
            "Reports → Acquisition → Traffic acquisition. Set the date range to the whole month, "
            "then Share this report → Download file → Download CSV."),
    "google_ads": ("Google Ads — Campaigns",
                   "Campaigns → set the month as the date range → Download (↓) → CSV or Excel .csv."),
    "search_console": ("Search Console — Performance",
                       "Performance → Search results → Date: the month → Export → Download CSV (zip)."),
    "meta_ads": ("Meta Ads — Campaigns",
                 "Ads Manager → Campaigns → the month as the date range → Reports → Export table data → .csv."),
    "generic": ("Any other CSV",
                "Columns: channel plus any of sessions, conversions, spend, revenue, clicks, impressions — "
                "or channel, metric, value."),
}


def create_app(home: Optional[str] = None) -> FastAPI:
    home = Path(home or os.environ.get("REPORT_DESK_HOME") or "report_desk_data").resolve()
    home.mkdir(parents=True, exist_ok=True)
    desk = Desk(home)
    secret = os.environ.get("REPORT_DESK_SECRET") or _workspace_secret(home)
    password = os.environ.get("REPORT_DESK_PASSWORD", "")

    @asynccontextmanager
    async def lifespan(_app):
        yield
        desk.close()

    app = FastAPI(title="Report Desk", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.desk = desk
    app.state.password = password
    app.add_middleware(SessionMiddleware, secret_key=secret, session_cookie="report_desk",
                       max_age=12 * 3600, same_site="lax",
                       https_only=os.environ.get("REPORT_DESK_SECURE_COOKIES") == "1")
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.globals.update(STATUS_LABELS=STATUS_LABELS, SOURCE_NAMES=SOURCE_NAMES, period_label=period_label,
                                 channel_label=channel_label)
    templates.env.filters["n"] = lambda v: f"{v:,.0f}" if isinstance(v, (int, float)) else v
    templates.env.filters["when"] = _when
    templates.env.filters["strip_cites"] = strip_citations
    attempts: dict[str, deque] = defaultdict(deque)
    attempts_lock = threading.Lock()

    # ------------------------------------------------------------------ helpers
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; script-src 'self'; frame-ancestors 'self'; "
            "form-action 'self'; base-uri 'none'")
        if request.url.path.startswith(("/clients", "/month", "/reports", "/settings", "/activity")):
            resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    def user(request: Request) -> Optional[str]:
        return request.session.get("user")

    def csrf(request: Request) -> str:
        tok = request.session.get("csrf")
        if not tok:
            tok = secrets.token_urlsafe(32)
            request.session["csrf"] = tok
        return tok

    def check_csrf(request: Request, token: str) -> bool:
        good = request.session.get("csrf", "")
        return bool(good) and hmac.compare_digest(good, token or "")

    def flash(request: Request, msg: str, kind: str = "ok") -> None:
        request.session.setdefault("flash", [])
        request.session["flash"] = request.session["flash"][-4:] + [[kind, msg]]

    def page(request: Request, name: str, status_code: int = 200, **ctx) -> HTMLResponse:
        flashes = request.session.pop("flash", []) if "session" in request.scope else []
        agency = desk.store.agency()
        base = {"user": user(request), "csrf_token": csrf(request), "agency": agency, "flashes": flashes,
                "no_password": not password, "claude_ready": claude_available(),
                "current_period": _default_period(desk)}
        return templates.TemplateResponse(request=request, name=name, context={**base, **ctx},
                                          status_code=status_code)

    def back(url: str) -> RedirectResponse:
        return RedirectResponse(url, status_code=303)

    def guard(request: Request, token: Optional[str] = None, post: bool = False):
        """Returns a response to send instead (login redirect / bad CSRF), or None to continue."""
        if not user(request):
            if post:
                return Response("Your session has expired. Sign in again.", status_code=401)
            nxt = request.url.path
            return back("/login" + (f"?next={nxt}" if nxt.startswith("/") and not nxt.startswith("//") else ""))
        if post and not check_csrf(request, token or ""):
            return Response("This form has expired. Go back, reload the page and try again.", status_code=403)
        return None

    def client_or_404(request: Request, cid: str, period: Optional[str] = None):
        try:
            desk.store.check_id(cid)
            if period is not None:
                desk.store.check_period(period)
        except StoreError:
            return None, page(request, "error.html", 404, message="That page doesn't exist.")
        c = desk.store.client(cid)
        if c is None:
            return None, page(request, "error.html", 404, message="That client doesn't exist.")
        return c, None

    # -------------------------------------------------------------------- auth
    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request, next: str = "/"):
        return page(request, "login.html", next=_safe_next(next), reviewers=desk.store.agency().get("reviewers", []))

    @app.post("/login")
    def login(request: Request, name: str = Form(""), password_: str = Form("", alias="password"),
              next: str = Form("/"), csrf_token: str = Form("")):
        ip = request.client.host if request.client else "?"
        now = time.time()
        with attempts_lock:
            q = attempts[ip]
            while q and now - q[0] > 300:
                q.popleft()
            if len(q) >= 8:
                return page(request, "login.html", 429, next=_safe_next(next), error="Too many attempts. "
                            "Wait a few minutes and try again.", reviewers=desk.store.agency().get("reviewers", []))
        if not check_csrf(request, csrf_token):
            return page(request, "login.html", 403, next=_safe_next(next),
                        error="The sign-in form expired. Try again.", reviewers=desk.store.agency().get("reviewers", []))
        name = re.sub(r"\s+", " ", name).strip()[:60]
        ok = bool(name) and (not password or hmac.compare_digest(password_.encode(), password.encode()))
        if not ok:
            with attempts_lock:
                attempts[ip].append(now)
            return page(request, "login.html", 401, next=_safe_next(next),
                        error="Enter your name and the team password." if not name else "That password isn't right.",
                        reviewers=desk.store.agency().get("reviewers", []))
        request.session.clear()
        request.session["user"] = name
        request.session["csrf"] = secrets.token_urlsafe(32)
        desk.store.audit(name, "signed in")
        return back(_safe_next(next))

    @app.post("/logout")
    def logout(request: Request, csrf_token: str = Form("")):
        if check_csrf(request, csrf_token):
            request.session.clear()
        return back("/login")

    @app.get("/healthz")
    def healthz():
        return JSONResponse({"ok": True})

    # ------------------------------------------------------------- dashboard
    @app.get("/", response_class=HTMLResponse)
    def home_page(request: Request):
        if (r := guard(request)):
            return r
        if not desk.store.list_clients(include_archived=True):
            return page(request, "setup.html")
        return back(f"/month/{_default_period(desk)}")

    @app.post("/setup/demo")
    def setup_demo(request: Request, csrf_token: str = Form("")):
        if (r := guard(request, csrf_token, post=True)):
            return r
        from ..demo import agency as demo
        if desk.store.list_clients(include_archived=True):
            flash(request, "The workspace already has clients.", "warn")
            return back("/")
        demo.seed(desk.store)
        desk.store.audit(user(request), "loaded the demo agency")
        flash(request, "Loaded Northstar Digital: 12 clients with three months of real-format exports.")
        return back(f"/month/{demo.PERIOD}")

    @app.get("/month/{period}", response_class=HTMLResponse)
    def month(request: Request, period: str):
        if (r := guard(request)):
            return r
        if not is_period(period):
            return page(request, "error.html", 404, message="That month doesn't exist.")
        rows = desk.overview(period)
        counts = defaultdict(int)
        for r_ in rows:
            counts[r_["status"]] += 1
        ready = sum(1 for r_ in rows if r_["has_data"] and r_["status"] not in (g.NEEDS_REVIEW, g.APPROVED, RUNNING,
                                                                                  g.REJECTED))
        checked = sum(r_["checked"] for r_ in rows)
        return page(request, "month.html", period=period, rows=rows, counts=counts, ready=ready, checked=checked,
                    prev_period=shift_period(period, -1), next_period=shift_period(period, 1),
                    running=counts[RUNNING] > 0)

    @app.post("/month/{period}/draft-all")
    def draft_all(request: Request, period: str, csrf_token: str = Form("")):
        if (r := guard(request, csrf_token, post=True)):
            return r
        if not is_period(period):
            return back("/")
        queued = desk.start_all(period, actor=user(request))
        flash(request, f"Drafting {len(queued)} report{'s' if len(queued) != 1 else ''}. Each one is fact-checked "
                       f"before it reaches you." if queued else "Nothing new to draft.")
        return back(f"/month/{period}")

    # ----------------------------------------------------------------- clients
    @app.get("/clients", response_class=HTMLResponse)
    def clients(request: Request):
        if (r := guard(request)):
            return r
        return page(request, "clients.html", clients=desk.store.list_clients(include_archived=True))

    @app.post("/clients")
    def create_client(request: Request, csrf_token: str = Form(""), name: str = Form(""), sector: str = Form(""),
                      conversion_label: str = Form("enquiries"), monthly_target: str = Form(""),
                      context: str = Form("")):
        if (r := guard(request, csrf_token, post=True)):
            return r
        try:
            c = desk.store.create_client(name, sector=sector, conversion_label=conversion_label,
                                         monthly_target=monthly_target, context=context)
        except StoreError as e:
            flash(request, str(e), "error")
            return back("/clients")
        desk.store.audit(user(request), "added client", c["id"], detail=c["name"])
        flash(request, f"Added {c['name']}. Upload this month's exports next.")
        return back(f"/clients/{c['id']}/{_default_period(desk)}")

    @app.get("/clients/{cid}/settings", response_class=HTMLResponse)
    def client_settings(request: Request, cid: str):
        if (r := guard(request)):
            return r
        c, err = client_or_404(request, cid)
        if err:
            return err
        return page(request, "client_settings.html", client=c)

    @app.post("/clients/{cid}/settings")
    def save_client(request: Request, cid: str, csrf_token: str = Form(""), name: str = Form(""),
                    sector: str = Form(""), conversion_label: str = Form(""), monthly_target: str = Form(""),
                    context: str = Form(""), archived: str = Form("")):
        if (r := guard(request, csrf_token, post=True)):
            return r
        c, err = client_or_404(request, cid)
        if err:
            return err
        try:
            desk.store.update_client(cid, name=name, sector=sector, conversion_label=conversion_label,
                                     monthly_target=monthly_target, context=context, archived=bool(archived))
        except StoreError as e:
            flash(request, str(e), "error")
            return back(f"/clients/{cid}/settings")
        desk.store.audit(user(request), "updated client", cid)
        flash(request, "Saved.")
        return back(f"/clients/{cid}/settings")

    @app.get("/clients/{cid}/{period}", response_class=HTMLResponse)
    def client_month(request: Request, cid: str, period: str):
        if (r := guard(request)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        st = desk.state(cid, period)
        sources = desk.store.sources(cid, period)
        pd, notes = desk.store.period_data(cid, period)
        return page(request, "client_month.html", client=c, period=period, st=st, sources=sources,
                    source_help=SOURCE_HELP, pd=pd, notes=notes, channels=_channel_rows(pd),
                    manual_channels=[(k, v.label) for k, v in CHANNELS.items() if k not in ("other",)],
                    periods=desk.store.periods_with_data(cid), prev_period=shift_period(period, -1),
                    next_period=shift_period(period, 1), max_mb=MAX_UPLOAD_BYTES // (1024 * 1024))

    @app.post("/clients/{cid}/{period}/upload")
    async def upload(request: Request, cid: str, period: str, csrf_token: str = Form(""),
                     source_type: str = Form(""), file: UploadFile = File(...)):
        if (r := guard(request, csrf_token, post=True)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        url = f"/clients/{cid}/{period}"
        if source_type not in SOURCES:
            flash(request, "Choose which platform the file came from.", "error")
            return back(url)
        data = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            flash(request, f"That file is over {MAX_UPLOAD_BYTES // (1024 * 1024)} MB. Export only the month you need.",
                  "error")
            return back(url)
        try:
            res = import_file(source_type, data, period)
        except ImportError_ as e:
            flash(request, f"{SOURCE_NAMES[source_type]}: {e}", "error")
            return back(url)
        if period not in res.periods:
            got = ", ".join(period_label(p) for p in sorted(res.periods)) or "no month"
            flash(request, f"That {SOURCE_NAMES[source_type]} file covers {got}, not {period_label(period)}. "
                           f"Upload it on that month's page, or export {period_label(period)}.", "error")
            return back(url)
        fname = re.sub(r"[^\w.\- ]", "_", (file.filename or "upload"))[:120]
        try:
            desk.store.add_source(cid, res, period, filename=fname, raw=data)
            other = [p for p in res.periods if p != period and is_period(p)]
            for p in other:            # a comparison export also fills the earlier month
                if not any(s["type"] == source_type for s in desk.store.sources(cid, p)):
                    desk.store.add_source(cid, res, p, filename=fname, raw=data)
        except StoreError as e:
            flash(request, str(e), "error")
            return back(url)
        desk.store.audit(user(request), f"uploaded {SOURCE_NAMES[source_type]}", cid, period, fname)
        n = sum(len(row) for row in res.periods[period].values())
        msg = f"Imported {SOURCE_NAMES[source_type]}: {n} figures for {period_label(period)}."
        if res.warnings:
            msg += " Note: " + " ".join(res.warnings[:2])
        flash(request, msg, "warn" if res.warnings else "ok")
        return back(url)

    @app.post("/clients/{cid}/{period}/sources/{sid}/delete")
    def delete_source(request: Request, cid: str, period: str, sid: str, csrf_token: str = Form("")):
        if (r := guard(request, csrf_token, post=True)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        try:
            desk.store.delete_source(cid, period, sid)
        except StoreError as e:
            flash(request, str(e), "error")
            return back(f"/clients/{cid}/{period}")
        desk.store.audit(user(request), "removed a data file", cid, period, sid)
        flash(request, "Removed.")
        return back(f"/clients/{cid}/{period}")

    @app.post("/clients/{cid}/{period}/manual")
    async def manual(request: Request, cid: str, period: str):
        form = await request.form()
        if (r := guard(request, str(form.get("csrf_token", "")), post=True)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        values: dict[str, dict[str, float]] = {}
        for key, raw in form.multi_items():
            m = re.fullmatch(r"v__([a-z_]+)__([a-z_]+)", key)
            if not m or not str(raw).strip():
                continue
            scope, metric = m.groups()
            if scope not in CHANNELS or metric not in BASE_METRICS:
                continue
            try:
                v = float(str(raw).replace(",", "").replace("£", "").replace("$", "").replace("€", "").strip())
            except ValueError:
                flash(request, f"“{str(raw)[:30]}” isn't a number ({channel_label(scope)} {METRICS[metric].label}).",
                      "error")
                return back(f"/clients/{cid}/{period}")
            if not math.isfinite(v) or v < 0 or v > 1e12:
                flash(request, f"{channel_label(scope)} {METRICS[metric].label}: enter an ordinary number, "
                               f"zero or more.", "error")
                return back(f"/clients/{cid}/{period}")
            values.setdefault(scope, {})[metric] = v
        if not values:
            flash(request, "Enter at least one figure.", "error")
            return back(f"/clients/{cid}/{period}")
        desk.store.set_manual(cid, period, values)
        desk.store.audit(user(request), "entered figures by hand", cid, period,
                         ", ".join(f"{channel_label(s)} {m}" for s, row in values.items() for m in row)[:500])
        flash(request, "Saved. Figures entered by hand take priority over uploaded files.")
        return back(f"/clients/{cid}/{period}")

    @app.post("/clients/{cid}/{period}/draft")
    def draft(request: Request, cid: str, period: str, csrf_token: str = Form("")):
        if (r := guard(request, csrf_token, post=True)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        fut = desk.start_in_background(cid, period, actor=user(request), fresh=True)
        if fut is None:
            flash(request, "This report is already being drafted.", "warn")
        return back(f"/clients/{cid}/{period}")

    @app.get("/clients/{cid}/{period}/status")
    def run_status(request: Request, cid: str, period: str):
        if not user(request):
            return JSONResponse({"error": "signed out"}, status_code=401)
        try:
            desk.store.check_id(cid)
            desk.store.check_period(period)
        except StoreError:
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse({"status": desk.status(cid, period)})

    @app.get("/month/{period}/status")
    def month_status(request: Request, period: str):
        if not user(request):
            return JSONResponse({"error": "signed out"}, status_code=401)
        if not is_period(period):
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse({"running": sum(1 for c in desk.store.list_clients()
                                            if desk.status(c["id"], period) == RUNNING)})

    # ------------------------------------------------------------------ review
    @app.get("/clients/{cid}/{period}/review", response_class=HTMLResponse)
    def review_page(request: Request, cid: str, period: str):
        if (r := guard(request)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        st = desk.state(cid, period)
        v = st["values"]
        if not v.get("draft"):
            return back(f"/clients/{cid}/{period}")
        sheet = FactSheet.from_dict(v["sheet"])
        ver = Verification.from_dict(v.get("verification") or {})
        return page(request, "review.html", client=c, period=period, st=st, v=v, sheet=sheet, ver=ver,
                    draft_html=Markup(_review_html(v["draft"], ver, sheet)),
                    anomalies=[Anomaly.from_dict(a) for a in v.get("anomalies", [])],
                    fact_groups=_fact_groups(sheet), reviewers=desk.store.agency().get("reviewers", []),
                    can_request=v.get("writer") == "claude" or st.get("writer") == "claude")

    @app.post("/clients/{cid}/{period}/review")
    async def review_action(request: Request, cid: str, period: str):
        form = await request.form()
        if (r := guard(request, str(form.get("csrf_token", "")), post=True)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        action = str(form.get("action", ""))
        if action not in ("approve", "edit", "request_changes", "update_notes", "reject"):
            return back(f"/clients/{cid}/{period}/review")
        decision: dict[str, Any] = {"action": action, "reviewer": str(form.get("reviewer") or user(request))[:60]}
        if action in ("edit", "approve") and form.get("text") is not None and str(form.get("text")).strip():
            decision["text"] = str(form.get("text")).replace("\r\n", "\n")[:40000]
        if action == "approve":
            decision["confirm_flagged"] = form.get("confirm_flagged") == "1"
            decision["comment"] = str(form.get("comment", ""))[:1000]
        if action == "request_changes":
            decision["change_request"] = str(form.get("change_request", ""))[:3000]
        if action == "reject":
            decision["reason"] = str(form.get("reason", ""))[:500]
        if action in ("update_notes", "request_changes"):
            decision["explanations"] = {k[5:]: str(v)[:600] for k, v in form.multi_items() if k.startswith("expl_")}
            decision["next_steps"] = str(form.get("next_steps", ""))[:3000]
        slow = action in ("request_changes", "update_notes")
        try:
            if slow:
                desk.review_in_background(cid, period, decision, actor=user(request))
            else:
                st = await run_in_threadpool(desk.review, cid, period, decision, user(request))
        except DeskError as e:
            flash(request, str(e), "error")
            return back(f"/clients/{cid}/{period}/review")
        if slow:
            flash(request, "Redrafting with your changes. The new draft is fact-checked before it appears here.")
            return back(f"/clients/{cid}/{period}")
        msg = st["values"].get("review_message")
        if msg:
            flash(request, msg, "error")
            return back(f"/clients/{cid}/{period}/review")
        if st["status"] == g.APPROVED:
            rep = st["reports"][-1]
            flash(request, f"Approved. Version {rep['version']} is ready to download"
                           + ("." if rep.get("has_pdf") else f" (PDF unavailable: {rep.get('pdf_error')})."))
            return back(f"/clients/{cid}/{period}")
        if st["status"] == g.REJECTED:
            flash(request, "Marked as not sending this month.")
            return back(f"/month/{period}")
        flash(request, "Saved and re-checked." if st["values"].get("verification", {}).get("ok")
              else "Saved. Some figures need attention — see the highlighted sentences.",
              "ok" if st["values"].get("verification", {}).get("ok") else "warn")
        return back(f"/clients/{cid}/{period}/review")

    @app.get("/clients/{cid}/{period}/preview", response_class=HTMLResponse)
    def preview(request: Request, cid: str, period: str):
        if (r := guard(request)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        v = desk.state(cid, period)["values"]
        if not v.get("draft"):
            return back(f"/clients/{cid}/{period}")
        html = render_report(desk.store, c, FactSheet.from_dict(v["sheet"]), v["draft"],
                             [Anomaly.from_dict(a) for a in v.get("anomalies", [])], preview=True)
        return HTMLResponse(html)

    # ---------------------------------------------------------------- reports
    @app.get("/reports/{cid}/{period}/v{version}.{ext}")
    def report_file(request: Request, cid: str, period: str, version: int, ext: str):
        if (r := guard(request)):
            return r
        c, err = client_or_404(request, cid, period)
        if err:
            return err
        if ext not in ("html", "pdf"):
            return page(request, "error.html", 404, message="That file doesn't exist.")
        p = desk.store.report_file(cid, period, version, ext)
        if p is None:
            return page(request, "error.html", 404, message="That file doesn't exist.")
        slug = re.sub(r"[^A-Za-z0-9]+", "-", c["name"]).strip("-")
        fname = f"{slug}-{period}-report-v{version}.{ext}"
        if ext == "pdf":
            return FileResponse(p, media_type="application/pdf", filename=fname)
        return FileResponse(p, media_type="text/html; charset=utf-8",
                            headers={"Content-Disposition": f'inline; filename="{fname}"'})

    # --------------------------------------------------------------- settings
    @app.get("/settings", response_class=HTMLResponse)
    def settings(request: Request):
        if (r := guard(request)):
            return r
        return page(request, "settings.html", models=MODELS, currencies=list(CURRENCY_SYMBOLS))

    @app.post("/settings")
    async def save_settings(request: Request):
        form = await request.form()
        if (r := guard(request, str(form.get("csrf_token", "")), post=True)):
            return r
        updates: dict[str, Any] = {}
        name = str(form.get("name", "")).strip()[:80]
        if not name:
            flash(request, "The agency needs a name.", "error")
            return back("/settings")
        updates["name"] = name
        color = str(form.get("brand_color", "")).strip()
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            flash(request, "Brand colour must look like #1B4D3E.", "error")
            return back("/settings")
        updates["brand_color"] = color
        updates["voice"] = str(form.get("voice", "")).strip()[:1500]
        updates["sign_off"] = str(form.get("sign_off", "")).strip()[:200]
        reviewers = [re.sub(r"\s+", " ", x).strip()[:60] for x in str(form.get("reviewers", "")).splitlines()]
        updates["reviewers"] = [x for x in reviewers if x][:30]
        cur = str(form.get("currency", "GBP"))
        updates["currency"] = cur if cur in CURRENCY_SYMBOLS else "GBP"
        drafting = str(form.get("drafting", "template"))
        updates["drafting"] = drafting if drafting in ("template", "claude") else "template"
        model = str(form.get("model", ""))
        updates["model"] = model if model in MODELS else desk.store.agency().get("model")
        logo = form.get("logo")
        if logo is not None and getattr(logo, "filename", ""):
            data = await logo.read(1024 * 1024 + 1)
            try:
                desk.store.save_logo(data, logo.content_type or "")
            except StoreError as e:
                flash(request, str(e), "error")
                return back("/settings")
        if form.get("remove_logo") == "1":
            desk.store.save_agency({"logo": ""})
        desk.store.save_agency(updates)
        desk.store.audit(user(request), "updated agency settings")
        flash(request, "Settings saved.")
        return back("/settings")

    @app.get("/settings/logo")
    def logo(request: Request):
        if (r := guard(request)):
            return r
        data, mime = desk.store.logo_bytes()
        if not data:
            return Response(status_code=404)
        return Response(data, media_type=mime, headers={"Content-Security-Policy": "default-src 'none'"})

    @app.get("/activity", response_class=HTMLResponse)
    def activity(request: Request, client: str = ""):
        if (r := guard(request)):
            return r
        if client and not re.fullmatch(r"[a-z0-9-]{1,63}", client):
            client = ""
        return page(request, "activity.html", entries=desk.store.audit_log(400, client_id=client), client=client)

    @app.exception_handler(404)
    async def not_found(request: Request, exc):
        if request.url.path.startswith("/static"):
            return Response("Not found", status_code=404)
        return page(request, "error.html", 404, message="That page doesn't exist.")

    return app


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _workspace_secret(home: Path) -> str:
    p = home / "secret.key"
    if not p.exists():
        p.write_text(secrets.token_urlsafe(48))
        os.chmod(p, 0o600)
    return p.read_text().strip()


def _safe_next(nxt: str) -> str:
    return nxt if nxt.startswith("/") and not nxt.startswith("//") and "\\" not in nxt else "/"


def _default_period(desk: Desk) -> str:
    """The most recent month any client has data for; otherwise last month."""
    latest = ""
    for c in desk.store.list_clients():
        ps = desk.store.periods_with_data(c["id"])
        if ps and ps[-1] > latest:
            latest = ps[-1]
    if latest:
        return latest
    t = date.today()
    return shift_period(f"{t.year:04d}-{t.month:02d}", -1)


def _when(iso: Optional[str]) -> str:
    if not iso:
        return ""
    try:
        d, t = iso[:10], iso[11:16]
        y, m, dd = (int(x) for x in d.split("-"))
        return f"{dd} {date(y, m, dd):%b} {t}"
    except ValueError:
        return iso


def _fmt_cell(metric: str, v) -> str:
    if v is None or not isinstance(v, (int, float)) or not math.isfinite(v):
        return ""
    if metric in ("spend", "revenue"):
        return f"{v:,.2f}"
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"


def _channel_rows(pd) -> list[dict]:
    rows = []
    has = {m: any(row.get(m) for row in pd.values.values()) for m in ("spend", "revenue", "clicks")}
    for scope in pd.channels() + ([TOTAL] if TOTAL in pd.values else []):
        row = pd.values.get(scope, {})
        rows.append({"scope": scope, "label": channel_label(scope),
                     "cells": {m: (_fmt_cell(m, row.get(m)) if has.get(m, True) else "")
                               for m in ("sessions", "conversions", "spend", "revenue", "clicks", "impressions")},
                     "origin": pd.origin.get(scope, {})})
    return rows


def _fact_groups(sheet: FactSheet) -> list[tuple[str, list]]:
    groups: dict[str, list] = {}
    for f in sheet.facts:
        groups.setdefault(channel_label(f.scope), []).append((f, sheet.fmt(f)))
    return list(groups.items())


_PRIV_OPEN, _PRIV_MID, _PRIV_CLOSE = "", "", ""


def _review_html(draft: str, ver: Verification, sheet: FactSheet) -> str:
    """The draft as the reviewer sees it: every checked figure marked, problems highlighted, sources on hover."""
    import html as _h

    def attr(t: str) -> str:          # brackets escaped so the citation pass can't touch attributes
        return _h.escape(t).replace("[", "&#91;").replace("]", "&#93;")

    spans = sorted(((c.start, c.end, i) for i, c in enumerate(ver.claims) if 0 <= c.start < c.end <= len(draft)),
                   key=lambda x: x[0])
    keep, last_end = [], -1
    for s in spans:
        if s[0] >= last_end:
            keep.append(s)
            last_end = s[1]
    text = draft
    for start, end, i in reversed(keep):
        text = text[:start] + f"{_PRIV_OPEN}{i}{_PRIV_MID}" + text[start:end] + _PRIV_CLOSE + text[end:]
    out = md_to_html(text)              # fact IDs are carried by the marks' hover text instead
    issue_by_span = {(i.start, i.end): i for i in ver.issues}

    def open_tag(m):
        c = ver.claims[int(m.group(1))]
        if c.status == "verified" and c.fact_id and sheet.by_id(c.fact_id):
            f = sheet.by_id(c.fact_id)
            tip = f"{f.label}: {sheet.fmt(f)} ({f.id})"
            return f'<mark class="claim ok" title="{attr(tip)}" data-fact="{f.id}">'
        if c.status == "issue":
            iss = issue_by_span.get((c.start, c.end))
            tip = iss.message if iss else "Couldn't be backed by the data."
            return f'<mark class="claim bad" title="{attr(tip)}">'
        if c.status == "forward_looking":
            return '<mark class="claim future" title="About the future — not checked against the data.">'
        return '<mark class="claim unchecked" title="Not a figure from the data — check it yourself.">'

    out = re.sub(re.escape(_PRIV_OPEN) + r"(\d+)" + re.escape(_PRIV_MID), open_tag, out)
    out = out.replace(_PRIV_CLOSE, "</mark>")

    return out

