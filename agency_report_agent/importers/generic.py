"""Generic CSV — for any source without a dedicated importer (a CRM, a call
tracker, LinkedIn, a spreadsheet the agency already keeps).

Two shapes are accepted:

  Wide:   channel,sessions,conversions,spend,revenue
          Organic Search,4120,86,,
  Long:   channel,metric,value
          Organic Search,sessions,4120

An optional `period` column (YYYY-MM) lets one file carry several months.
"""

from __future__ import annotations

from ..model import BASE_METRICS, TOTAL, is_period, normalize_channel
from .common import ImportError_, ImportResult, cell, col, decode, is_total_row, parse_number, split_rows

METRIC_NAMES = {
    "sessions": "sessions", "visits": "sessions",
    "users": "users", "total users": "users", "visitors": "users",
    "conversions": "conversions", "leads": "conversions", "enquiries": "conversions",
    "key events": "conversions", "bookings": "conversions", "orders": "conversions",
    "revenue": "revenue", "sales": "revenue",
    "spend": "spend", "cost": "spend", "amount spent": "spend",
    "clicks": "clicks", "impressions": "impressions", "impr.": "impressions",
    "position": "avg_position", "avg position": "avg_position", "average position": "avg_position",
    "avg_position": "avg_position",
}


def _metric(name: str):
    n = (name or "").strip().lower()
    n = n.split("(")[0].strip()
    return METRIC_NAMES.get(n) or (n if n in BASE_METRICS else None)


def _additive(metric: str) -> bool:
    """Repeated rows for one channel (several campaigns, several weeks) add up — except averages."""
    return metric not in ("avg_position", "users")


def parse_generic(data: bytes, period_hint: str | None = None) -> ImportResult:
    rows = [r for r in split_rows(decode(data)) if any(r)]
    res = ImportResult(source_type="generic")
    if not rows:
        raise ImportError_("The file is empty.")
    h = rows[0]
    c_chan = col(h, "channel", "source", "channel group")
    if c_chan < 0:
        raise ImportError_("I need a column called \"channel\" (e.g. Organic Search, Paid Search, Email).")
    c_period = col(h, "period", "month")
    c_metric, c_value = col(h, "metric"), col(h, "value")
    long_form = c_metric >= 0 and c_value >= 0
    metric_cols = {} if long_form else {i: _metric(x) for i, x in enumerate(h) if _metric(x)}
    if not long_form and not metric_cols:
        raise ImportError_("I couldn't find any metric columns. Use names like sessions, conversions, "
                           "spend, revenue, clicks, impressions.")

    unknown = set()
    for r in rows[1:]:
        p = (cell(r, c_period) or "").strip() if c_period >= 0 else ""
        if p and not is_period(p):
            raise ImportError_(f"\"{p}\" isn't a month in the form YYYY-MM (for example 2026-09).")
        p = p or period_hint
        if not p:
            raise ImportError_("Add a period column (YYYY-MM) or pick the month above.")
        name = cell(r, c_chan) or ""
        scope = TOTAL if is_total_row(name) else normalize_channel(name)
        if scope is None:
            unknown.add(name)
            continue
        res.rows_read += 1
        if long_form:
            m = _metric(cell(r, c_metric) or "")
            v = parse_number(cell(r, c_value))
            if m and v is not None:
                res.put(p, scope, m, v, add=_additive(m))
        else:
            for i, m in metric_cols.items():
                v = parse_number(cell(r, i))
                if v is not None:
                    res.put(p, scope, m, v, add=_additive(m))
    if unknown:
        res.warnings.append("Skipped rows with channels I don't recognise: " + ", ".join(sorted(unknown))
                            + ". Use standard names like Organic Search, Paid Social, Email, Referral.")
    if not res.periods:
        raise ImportError_("No usable rows were found.")
    if len(res.periods) == 1:
        res.detected_period = next(iter(res.periods))
    return res
