"""The finished report: one self-contained, branded HTML file (and a PDF of it).

The tiles and the channel table are drawn straight from the fact sheet, never
from the written narrative, so the numbers a client sees in them are exactly
the data. The narrative is the reviewed draft with fact IDs removed.

The report carries the agency's name, logo and colour — the tool itself stays
invisible.
"""

from __future__ import annotations

import base64
import glob
import html
import os
import re
from datetime import datetime
from typing import Optional

from .anomalies import Anomaly
from .facts import Fact, FactSheet, singular
from .model import METRICS, TOTAL, channel_label, period_label
from .store import SOURCE_NAMES, Store
from .verify import Verification

esc = html.escape
_CITE = re.compile(r"\s?\[\s*F\d+(?:\s*[,;/]\s*F?\d+)*\s*\]")


# --------------------------------------------------------------------------- #
# Markdown (the small subset drafts use) → safe HTML
# --------------------------------------------------------------------------- #
def strip_citations(text: str) -> str:
    return _CITE.sub("", text)


def _inline(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def md_to_html(text: str, keep_citations: bool = False) -> str:
    if not keep_citations:
        text = strip_citations(text)
    out: list[str] = []
    para: list[str] = []
    items: list[str] = []

    def flush():
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            level = min(max(len(m.group(1)), 2), 3)
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            continue
        m = re.match(r"^(?:[-*+•]|\d{1,2}[.)])\s+(.*)$", line)
        if m:
            if para:
                flush()
            items.append(m.group(1))
            continue
        if items:
            items[-1] += " " + line
        else:
            para.append(line)
    flush()
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Pieces
# --------------------------------------------------------------------------- #
def _fmt(sheet: FactSheet, f: Optional[Fact]) -> str:
    return sheet.fmt(f).lstrip("+−±") if f else "—"


def _change(sheet: FactSheet, scope: str, metric: str) -> str:
    """A small change badge, coloured by whether the move is good for the client."""
    cur = sheet.find(scope, metric, "value", "current")
    prev = sheet.find(scope, metric, "value", "previous")
    if not cur or not prev:
        return '<span class="chg none">—</span>'
    hib = METRICS[metric].higher_is_better
    neutral = metric == "spend"          # more spend is a decision, not good or bad news
    unit = METRICS[metric].unit
    if unit == "count" and (prev.value < 10 or cur.value < 10):
        d = cur.value - prev.value
        cls = "flat" if d == 0 or neutral else ("good" if (d > 0) == hib else "bad")
        sign = "+" if d > 0 else ("−" if d < 0 else "±")
        return f'<span class="chg {cls}" title="{esc(_fmt(sheet, prev))} last month">{sign}{abs(d):,.0f}</span>'
    ch = sheet.find(scope, metric, "change", "current", "mom")
    if not ch:
        return '<span class="chg none">—</span>'
    if ch.direction == "flat":
        cls, arrow = "flat", "→"
    else:
        cls = "flat" if neutral else ("good" if (ch.value > 0) == hib else "bad")
        arrow = "▲" if ch.value > 0 else "▼"
    return (f'<span class="chg {cls}" title="{esc(_fmt(sheet, prev))} last month">{arrow} '
            f'{abs(ch.value):.1f}%</span>')


def _tile(sheet: FactSheet, label: str, metric: str, note: str = "") -> str:
    f = sheet.find(TOTAL, metric, "value", "current")
    if not f:
        return ""
    return (f'<div class="tile"><div class="tile-label">{esc(label)}</div>'
            f'<div class="tile-value">{esc(_fmt(sheet, f))}</div>'
            f'<div class="tile-foot">{_change(sheet, TOTAL, metric)}'
            f'{f"<span class=tile-note>{esc(note)}</span>" if note else ""}</div></div>')


def _target(sheet: FactSheet) -> str:
    prog = next((f for f in sheet.facts if f.kind == "target" and f.target_kind == "progress"), None)
    tgt = next((f for f in sheet.facts if f.kind == "target" and f.target_kind == "value"), None)
    gap = next((f for f in sheet.facts if f.kind == "target" and f.target_kind == "gap"), None)
    if not (prog and tgt and gap):
        return ""
    width = max(0.0, min(prog.value, 100.0))
    state = "hit" if prog.value >= 100 else ("near" if prog.value >= 80 else "miss")
    label = sheet.conversion_label
    words = (f"{gap.value:,.0f} ahead of target" if gap.value > 0 else
             "exactly on target" if gap.value == 0 else f"{abs(gap.value):,.0f} short of target")
    return (f'<div class="target {state}"><div class="target-head"><span>Monthly target: '
            f'{esc(_fmt(sheet, tgt))} {esc(label)}</span><strong>{prog.value:.0f}% · {esc(words)}</strong></div>'
            f'<div class="meter" role="img" aria-label="{prog.value:.0f}% of target">'
            f'<div class="meter-fill" style="width:{width:.1f}%"></div></div></div>')


def _table(sheet: FactSheet) -> str:
    channels = [s for s in dict.fromkeys(f.scope for f in sheet.facts) if s != TOTAL]
    has_spend = any(f.metric == "spend" and f.kind == "value" and f.value > 0 for f in sheet.facts)
    has_rev = any(f.metric == "revenue" and f.kind == "value" and f.value > 0 for f in sheet.facts)
    label = sheet.conversion_label
    head = ["Channel", "Sessions", label.capitalize(), "Conv. rate"]
    if has_spend:
        head += ["Spend", f"Cost per {singular(label)}"]
    if has_rev:
        head += ["Revenue"]

    def row(scope: str, cls: str = "") -> str:
        v = lambda m: sheet.find(scope, m, "value", "current")  # noqa: E731
        cells = [f'<th scope="row">{esc(channel_label(scope))}</th>',
                 f'<td class="num">{esc(_fmt(sheet, v("sessions")))}'
                 f'{"<br>" + _change(sheet, scope, "sessions") if v("sessions") else ""}</td>',
                 f'<td class="num">{esc(_fmt(sheet, v("conversions")))}'
                 f'{"<br>" + _change(sheet, scope, "conversions") if v("conversions") else ""}</td>',
                 f'<td class="num">{esc(_fmt(sheet, v("conv_rate")))}</td>']
        if has_spend:
            sp = v("spend")
            cells += [f'<td class="num">{esc(_fmt(sheet, sp)) if sp and sp.value else "—"}</td>',
                      f'<td class="num">{esc(_fmt(sheet, v("cpa")))}</td>']
        if has_rev:
            rv = v("revenue")
            cells += [f'<td class="num">{esc(_fmt(sheet, rv)) if rv and rv.value else "—"}</td>']
        return f'<tr class="{cls}">' + "".join(cells) + "</tr>"

    body = "".join(row(c) for c in channels)
    if any(f.scope == TOTAL for f in sheet.facts):
        body += row(TOTAL, "total")
    ths = "".join(f'<th scope="col" class="{"num" if i else ""}">{esc(h)}</th>' for i, h in enumerate(head))
    return f'<table class="channels"><thead><tr>{ths}</tr></thead><tbody>{body}</tbody></table>'


def _logo(store: Store) -> str:
    data, mime = store.logo_bytes()
    if not data:
        return ""
    return f'<img class="logo" alt="" src="data:{mime};base64,{base64.b64encode(data).decode()}">'


def _date(iso: str) -> str:
    try:
        d = datetime.strptime(iso[:10], "%Y-%m-%d")
        return f"{d.day} {d:%B %Y}"
    except ValueError:
        return iso


def _safe_color(c: str) -> str:
    return c if re.fullmatch(r"#[0-9a-fA-F]{6}", c or "") else "#1B4D3E"


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #
def render_report(store: Store, client: dict, sheet: FactSheet, draft: str, anomalies: list[Anomaly],
                  notes: Optional[list[str]] = None, reviewer: str = "", approved_at: str = "",
                  verification: Optional[Verification] = None, preview: bool = False,
                  show_notes: bool = False) -> str:
    agency = store.agency()
    brand = _safe_color(agency.get("brand_color", ""))
    month = period_label(sheet.period)
    label = sheet.conversion_label
    tiles = [_tile(sheet, label.capitalize(), "conversions"),
             _tile(sheet, "Website sessions", "sessions")]
    if sheet.find(TOTAL, "revenue") and sheet.find(TOTAL, "revenue").value > 0:
        tiles.append(_tile(sheet, "Revenue", "revenue"))
    if sheet.find(TOTAL, "spend") and sheet.find(TOTAL, "spend").value > 0:
        tiles.append(_tile(sheet, "Ad spend", "spend"))
        tiles.append(_tile(sheet, f"Cost per {singular(label)}", "cpa"))
    tiles_html = "".join(t for t in tiles if t)[:]
    sources = store.sources(client["id"], sheet.period) if client.get("id") else []
    src_names = ", ".join(sorted({SOURCE_NAMES.get(s["type"], s["type"]) for s in sources})) or "—"
    comp = f"Changes are compared with {period_label(sheet.previous_period)}." if sheet.previous_period else \
        "No earlier month is available, so there are no comparisons."
    checked = (f"Every figure in this report was checked against the source data before approval."
               if verification is not None and verification.ok else
               "Figures were checked against the source data and confirmed by the reviewer before approval."
               if verification is not None else "")
    approval = (f"Reviewed and approved by {esc(reviewer)} on {esc(_date(approved_at))}." if reviewer and approved_at
                else "Draft — not yet approved." if preview else "")
    note_items = "".join(f"<li>{esc(n)}</li>" for n in (notes or []))
    title = f"{client.get('name', '')} — {month} performance report"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root {{ --brand: {brand}; --ink: #16181d; --muted: #5d6470; --line: #e3e5e8; --soft: #f5f6f7;
        --good: #136b3f; --bad: #a3261b; --flat: #5d6470; color-scheme: light; }}
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{ margin: 0; background: #fff; color: var(--ink);
       font: 15px/1.6 "Inter", "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif; }}
.page {{ max-width: 860px; margin: 0 auto; padding: 40px 32px 56px; }}
header.top {{ display: flex; justify-content: space-between; align-items: center; gap: 16px;
             padding-bottom: 18px; border-bottom: 3px solid var(--brand); }}
.agency {{ display: flex; align-items: center; gap: 12px; font-weight: 600; letter-spacing: .01em; }}
.logo {{ max-height: 40px; max-width: 160px; }}
.period {{ color: var(--muted); font-size: 13px; text-align: right; }}
h1 {{ font-size: 30px; line-height: 1.2; margin: 28px 0 4px; letter-spacing: -.01em; }}
.sub {{ color: var(--muted); margin: 0 0 24px; }}
.tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(128px, 1fr)); gap: 12px; margin: 8px 0 18px; }}
.tile {{ border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; background: #fff; }}
.tile-label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }}
.tile-value {{ font-size: 24px; font-weight: 650; margin-top: 4px; font-variant-numeric: tabular-nums; }}
.tile-foot {{ margin-top: 4px; font-size: 13px; }}
.chg {{ font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.chg.good {{ color: var(--good); }} .chg.bad {{ color: var(--bad); }} .chg.flat, .chg.none {{ color: var(--flat); }}
.target {{ border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; margin-bottom: 28px; }}
.target-head {{ display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; font-size: 14px; }}
.meter {{ height: 10px; background: var(--soft); border-radius: 99px; margin-top: 10px; overflow: hidden; }}
.meter-fill {{ height: 100%; background: var(--brand); border-radius: 99px; }}
.target.miss .meter-fill {{ background: #b7791f; }}
.narrative h2 {{ font-size: 19px; margin: 30px 0 8px; padding-top: 6px; color: var(--brand); }}
.narrative h3 {{ font-size: 16px; margin: 20px 0 6px; }}
.narrative p {{ margin: 0 0 12px; }}
.narrative ul {{ margin: 0 0 12px; padding-left: 20px; }}
.narrative li {{ margin: 0 0 8px; }}
h2.section {{ font-size: 19px; margin: 34px 0 10px; color: var(--brand); }}
.table-wrap {{ overflow-x: auto; }}
table.channels {{ width: 100%; border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }}
.channels th, .channels td {{ padding: 9px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
.channels td {{ white-space: nowrap; }}
.channels td .chg {{ font-size: 12px; }}
.channels thead th {{ font-size: 11.5px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 600; }}
.channels .num {{ text-align: right; }}
.channels tr.total th, .channels tr.total td {{ font-weight: 650; border-top: 2px solid var(--ink); border-bottom: 0; }}
footer.notes {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12.5px; }}
footer.notes ul {{ padding-left: 18px; margin: 6px 0; }}
footer.notes p {{ margin: 4px 0; }}
@media (max-width: 600px) {{ .page {{ padding: 24px 16px 40px; }} h1 {{ font-size: 24px; }}
  header.top {{ flex-direction: column; align-items: flex-start; }} .period {{ text-align: left; }} }}
@media print {{ .page {{ padding: 0; max-width: none; }} .tile, .target, table {{ break-inside: avoid; }}
  h2 {{ break-after: avoid; }} }}
@page {{ size: A4; margin: 16mm 14mm; }}
</style>
</head>
<body>
<div class="page">
<header class="top">
  <div class="agency">{_logo(store)}<span>{esc(agency.get("name", ""))}</span></div>
  <div class="period">Monthly performance report<br>{esc(month)}</div>
</header>
<h1>{esc(client.get("name", ""))}</h1>
<p class="sub">{esc(month)} · {esc(comp)}</p>
<section class="tiles" aria-label="Headline figures">{tiles_html}</section>
{_target(sheet)}
<article class="narrative">
{md_to_html(draft)}
</article>
<h2 class="section">All channels at a glance</h2>
<div class="table-wrap">{_table(sheet)}</div>
<footer class="notes">
  <p>Data sources: {esc(src_names)}. {esc(comp)}</p>
  {f"<p>Notes on the data:</p><ul>{note_items}</ul>" if note_items and show_notes else ""}
  <p>{esc(checked)}</p>
  <p>Prepared by {esc(agency.get("name", ""))}. {approval}</p>
</footer>
</div>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
def _chromium_path() -> Optional[str]:
    env = os.environ.get("REPORT_DESK_CHROMIUM")
    if env and os.path.exists(env):
        return env
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    for pattern in ("chromium-*/chrome-linux/chrome", "chromium-*/chrome-linux64/chrome",
                    "chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(os.path.join(base, pattern)))
        if hits:
            return hits[-1]
    return None


def html_to_pdf(page_html: str) -> tuple[Optional[bytes], str]:
    """Print the report to PDF with headless Chromium. Returns (pdf, error)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "PDF export needs Playwright installed."
    try:
        with sync_playwright() as p:
            path = _chromium_path()
            browser = p.chromium.launch(executable_path=path) if path else p.chromium.launch()
            try:
                page = browser.new_page()
                page.set_content(page_html, wait_until="load", timeout=30000)
                pdf = page.pdf(format="A4", print_background=True, prefer_css_page_size=True)
            finally:
                browser.close()
        return pdf, ""
    except Exception as e:  # noqa: BLE001 — a PDF failure must never lose the approval
        return None, f"PDF export failed ({type(e).__name__})."
