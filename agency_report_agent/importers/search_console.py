"""Google Search Console — Performance export (Export → Download CSV).

GSC downloads a zip of several CSVs. The right one for monthly totals is
Dates.csv (one row per day): summing query rows undercounts, because Google
hides anonymised queries. Position is averaged weighted by impressions, which
is how GSC computes it. Top queries are kept for the report table.
"""

from __future__ import annotations

import io
import zipfile
from datetime import date

from .common import (ImportError_, ImportResult, cell, col, decode, parse_date,
                     parse_number, split_rows)


def _read_zip(data: bytes) -> dict[str, str]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ImportError_("That zip file is damaged. Download the export from Search Console again.")
    out = {}
    for info in zf.infolist():
        if info.file_size > 15 * 1024 * 1024 or info.filename.endswith("/"):
            continue
        name = info.filename.rsplit("/", 1)[-1].lower()
        out[name] = decode(zf.read(info))
    return out


def parse_search_console(data: bytes, period_hint: str | None = None) -> ImportResult:
    res = ImportResult(source_type="search_console")
    files = _read_zip(data) if data[:2] == b"PK" else {"upload.csv": decode(data)}

    dates_text = files.get("dates.csv") or files.get("chart.csv")
    queries_text = files.get("queries.csv")
    if dates_text is None:
        # A single CSV upload: work out which kind it is from its header.
        for name, text in files.items():
            head = text[:400].lower()
            if head.startswith("date,") or "\ndate," in head or head.startswith("date\t"):
                dates_text = text
            elif "top queries" in head or head.startswith("query"):
                queries_text = text

    if dates_text is None:
        if queries_text is not None:
            raise ImportError_(
                "This is the Queries file on its own. Monthly totals need Dates.csv — upload the whole "
                "zip that Search Console downloads (Performance → Export → Download CSV).")
        raise ImportError_("This doesn't look like a Search Console Performance export. Upload the zip "
                           "from Performance → Export → Download CSV.")

    rows = split_rows(dates_text)
    hi = next((i for i, r in enumerate(rows[:10]) if r and r[0].lower() == "date"), -1)
    if hi < 0:
        raise ImportError_("Search Console's Dates file is missing its header row.")
    h = rows[hi]
    c_date, c_clicks, c_impr, c_pos = col(h, "date"), col(h, "clicks"), col(h, "impressions"), col(h, "position")

    per_month: dict[str, dict[str, float]] = {}
    days: dict[str, set[int]] = {}
    for r in rows[hi + 1:]:
        d = parse_date(cell(r, c_date) or "")
        if not d:
            continue
        p = f"{d.year:04d}-{d.month:02d}"
        m = per_month.setdefault(p, {"clicks": 0.0, "impressions": 0.0, "pos_x_impr": 0.0})
        clk = parse_number(cell(r, c_clicks)) or 0.0
        imp = parse_number(cell(r, c_impr)) or 0.0
        pos = parse_number(cell(r, c_pos))
        m["clicks"] += clk
        m["impressions"] += imp
        if pos is not None:
            m["pos_x_impr"] += pos * imp
        days.setdefault(p, set()).add(d.day)
        res.rows_read += 1

    if not per_month:
        raise ImportError_("The Dates file has no daily rows.")

    for p, m in per_month.items():
        res.put(p, "organic_search", "clicks", m["clicks"])
        res.put(p, "organic_search", "impressions", m["impressions"])
        if m["impressions"] > 0:
            res.put(p, "organic_search", "avg_position", m["pos_x_impr"] / m["impressions"])
        y, mo = (int(x) for x in p.split("-"))
        nxt = date(y + (mo == 12), mo % 12 + 1, 1)
        month_days = (nxt - date(y, mo, 1)).days
        if len(days[p]) < month_days:
            res.warnings.append(f"Search Console has {len(days[p])} of {month_days} days for {p}. "
                                "Recent days can lag by 2–3 days — re-export later for a complete month.")

    if len(per_month) == 1:
        res.detected_period = next(iter(per_month))
    elif period_hint and period_hint in per_month:
        res.detected_period = period_hint

    if queries_text:
        qrows = split_rows(queries_text)
        qh = next((i for i, r in enumerate(qrows[:5]) if r and ("quer" in r[0].lower())), -1)
        if qh >= 0:
            cq, cc, ci, cp = 0, col(qrows[qh], "clicks"), col(qrows[qh], "impressions"), col(qrows[qh], "position")
            top = []
            for r in qrows[qh + 1:]:
                if not r or not r[0]:
                    continue
                top.append({"query": r[cq][:120], "clicks": parse_number(cell(r, cc)) or 0,
                            "impressions": parse_number(cell(r, ci)) or 0,
                            "position": parse_number(cell(r, cp))})
            top.sort(key=lambda q: -q["clicks"])
            res.extras["top_queries"] = top[:10]
    return res
