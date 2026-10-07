"""Meta Ads Manager — campaign table export (Export table data → .csv).

Columns are named with the currency in brackets ("Amount spent (GBP)"), the
date range sits in "Reporting starts"/"Reporting ends" columns, and Meta often
adds a summary row with an empty campaign name. Everything maps to Paid Social.
"""

from __future__ import annotations

from .common import (ImportError_, ImportResult, cell, col, decode, parse_date,
                     parse_number, period_from_range, require_single_month, split_rows)

# Results Meta reports for campaigns that don't aim for leads or sales.
NOT_LEADS = ("messaging", "conversation", "post_save", "post_engagement", "link_click", "landing_page_view",
             "reach", "impression", "video", "thruplay", "page_like", "like", "follow", "profile_visit",
             "add_to_cart", "view_content", "initiate_checkout", "add_payment_info", "engagement", "click")
LEAD_LIKE = ("lead", "purchase", "registration", "contact", "schedule", "submit_application",
             "subscribe", "fb_pixel_custom", "custom_conversion", "offsite_conversion")


def _is_lead(indicator: str) -> bool:
    if not indicator:
        return True
    if any(k in indicator for k in NOT_LEADS):
        return False
    return any(k in indicator for k in LEAD_LIKE)


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

    # The whole file's reporting range (a daily breakdown has one row per day).
    starts, ends = [], []
    for r in rows[hi + 1:]:
        if any(r) and c_start >= 0:
            s_, e_ = parse_date(cell(r, c_start) or ""), parse_date(cell(r, c_end) or "")
            if s_:
                starts.append(s_)
            if e_:
                ends.append(e_)
    period = None
    if starts:
        first, last = min(starts), max(ends) if ends else None
        require_single_month(first, last, "Meta")
        period, w = period_from_range(first, last)
        if w:
            res.warnings.append(w)
    summary = None
    non_lead_results = False
    for r in rows[hi + 1:]:
        if not any(r):
            continue
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
            if _is_lead(indicator):
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
