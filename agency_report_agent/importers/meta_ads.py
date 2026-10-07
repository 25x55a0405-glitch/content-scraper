"""Meta Ads Manager — campaign table export (Export table data → .csv).

Columns are named with the currency in brackets ("Amount spent (GBP)"), the
date range sits in "Reporting starts"/"Reporting ends" columns, and Meta often
adds a summary row with an empty campaign name. Everything maps to Paid Social.
"""

from __future__ import annotations

from .common import (ImportError_, ImportResult, cell, col, decode, parse_date,
                     parse_number, period_from_range, split_rows)

LEAD_LIKE = ("lead", "purchase", "conversion", "registration", "contact", "schedule",
             "submit", "subscribe", "complete", "offsite_conversion")


def parse_meta_ads(data: bytes, period_hint: str | None = None) -> ImportResult:
    rows = split_rows(decode(data))
    res = ImportResult(source_type="meta_ads")
    hi = -1
    for i, r in enumerate(rows[:20]):
        lower = [c.lower() for c in r]
        if any(c.startswith("amount spent") for c in lower):
            hi = i
            break
    if hi < 0:
        raise ImportError_(
            "This doesn't look like a Meta Ads Manager export — I need an \"Amount spent\" column. "
            "In Ads Manager select the campaigns, set the month, then Export → Export table data → .csv.")
    h = rows[hi]
    c_name = col(h, "campaign name", "ad set name", "ad name")
    c_start, c_end = col(h, "reporting starts"), col(h, "reporting ends")
    c_spend = col(h, "amount spent")
    c_impr = col(h, "impressions")
    c_clicks = col(h, "link clicks", "clicks (all)", "clicks")
    c_results = col(h, "results")
    c_indicator = col(h, "result indicator", "result type")
    c_value = col(h, "purchases conversion value", "website purchases conversion value", "conversion value")

    ccy = h[c_spend].split("(")[-1].rstrip(")").strip() if "(" in h[c_spend] else ""
    if ccy:
        res.extras["currency"] = ccy

    period = None
    summary = None
    non_lead_results = False
    for r in rows[hi + 1:]:
        if not any(r):
            continue
        if not period and c_start >= 0:
            p, w = period_from_range(parse_date(cell(r, c_start) or ""), parse_date(cell(r, c_end) or ""))
            if w:
                res.warnings.append(w)
            period = p
        name = (cell(r, c_name) or "").strip()
        if not name:
            summary = r                      # Meta's totals row
            continue
        p = period or period_hint
        if not p:
            continue
        res.rows_read += 1
        for metric, idx in (("spend", c_spend), ("impressions", c_impr), ("clicks", c_clicks),
                            ("revenue", c_value)):
            v = parse_number(cell(r, idx))
            if v is not None:
                res.put(p, "paid_social", metric, v, add=True)
        results = parse_number(cell(r, c_results))
        indicator = (cell(r, c_indicator) or "").lower()
        if results is not None:
            if not indicator or any(k in indicator for k in LEAD_LIKE):
                res.put(p, "paid_social", "conversions", results, add=True)
            else:
                non_lead_results = True

    if res.rows_read == 0:
        raise ImportError_("The Meta export has no campaign rows with data.")
    period = period or period_hint
    if not period:
        raise ImportError_("I couldn't find the reporting dates. Pick the month above.")
    if not res.periods.get(period) and period_hint:
        period = period_hint
    if non_lead_results:
        res.warnings.append("Some campaigns optimise for reach or clicks rather than leads; their "
                            "\"Results\" were not counted as conversions.")
    if summary is not None:
        s = parse_number(cell(summary, c_spend))
        ours = res.periods.get(period, {}).get("paid_social", {}).get("spend", 0)
        if s is not None and abs(s - ours) > max(1.0, 0.005 * s):
            res.warnings.append(f"Campaign rows add up to {ours:,.2f} spend but Meta's summary row "
                                f"says {s:,.2f}. Check for filtered or deleted campaigns.")
    res.detected_period = period if c_start >= 0 else None
    return res
