"""Google Ads — Campaigns report download (CSV or "Excel CSV").

The file opens with a title line and a quoted date range, then the table, then
"Total: …" summary rows. "Excel CSV" downloads are UTF-16 and tab-separated.
Campaign types are mapped to the channels GA4 uses for the same traffic, so
spend lines up with GA4's conversions: Display → Display, Video → Paid Video,
Shopping → Paid Shopping, Performance Max → Cross-network, everything else
(Search, Demand Gen) → Paid Search.
"""

from __future__ import annotations

from .common import (ImportError_, ImportResult, cell, col, decode, is_total_row, parse_date,
                     parse_number, parse_range_text, period_from_range, require_single_month, split_rows)

TYPE_TO_CHANNEL = {
    "display": "display",
    "video": "paid_video",
    "shopping": "paid_shopping",
    "performance max": "cross_network",
    "pmax": "cross_network",
}


def parse_google_ads(data: bytes, period_hint: str | None = None) -> ImportResult:
    text = decode(data)
    rows = split_rows(text)
    res = ImportResult(source_type="google_ads")

    start = end = None
    for r in rows[:5]:
        joined = " ".join(r)
        s, e = parse_range_text(joined)
        if s:
            start, end = s, e
            break

    hi = -1
    for i, r in enumerate(rows[:40]):
        lower = [c.lower() for c in r]
        if any(c.startswith("clicks") for c in lower) and any(c.startswith("cost") for c in lower) \
           and any(c.startswith("impr") for c in lower):
            hi = i
            break
    if hi < 0:
        raise ImportError_(
            "This doesn't look like a Google Ads campaign report — I need Clicks, Impr. and Cost "
            "columns. In Google Ads open Campaigns, set the date range to one month, then "
            "Download → CSV.")
    h = rows[hi]
    c_name = col(h, "campaign")
    c_type = col(h, "campaign type")
    c_clicks = col(h, "clicks")
    c_impr = col(h, "impr.", "impressions", "impr")
    # "Cost" but never "Cost / conv." or "Cost per…"
    c_cost = next((i for i, x in enumerate(h) if x.lower() in ("cost", "cost (gbp)", "cost (usd)", "cost (eur)")
                   or (x.lower().startswith("cost") and "/" not in x and "per" not in x.lower()
                       and "conv" not in x.lower())), -1)
    c_conv = col(h, "conversions", "conv.")
    c_value = col(h, "conv. value", "conversion value", "all conv. value")
    c_ccy = col(h, "currency code", "currency")

    require_single_month(start, end, "Google Ads")
    c_seg = col(h, "month", "day", "date", "week")
    if c_seg >= 0:      # segmented by time: every row must be in the same month
        months = set()
        for r in rows[hi + 1:]:
            d = parse_date(cell(r, c_seg) or "") or parse_date("1 " + (cell(r, c_seg) or ""))
            if d:
                months.add((d.year, d.month))
        if len(months) > 1:
            raise ImportError_("This Google Ads export is split across more than one month. Download one "
                               "month at a time.")
    period, warn = period_from_range(start, end)
    if warn:
        res.warnings.append(warn)
    if not period:
        period = period_hint
        if not period:
            raise ImportError_("I couldn't find the date range in this Google Ads export. Pick the month "
                               "above, or download the report again — the range is on its second line.")
        res.warnings.append("The file didn't state its date range, so I used the month you selected.")

    totals_seen = False
    account_total = None
    currencies = set()
    for r in rows[hi + 1:]:
        if not any(r):
            continue
        first = (cell(r, 0) or "")
        name = cell(r, c_name) or first
        if first.lower().startswith("total") or (name or "").lower().startswith("total"):
            totals_seen = True
            if "account" in (first + name).lower():
                account_total = r
            continue
        if is_total_row(name) and c_name >= 0 and not name:
            continue
        clicks = parse_number(cell(r, c_clicks))
        impr = parse_number(cell(r, c_impr))
        cost = parse_number(cell(r, c_cost))
        if clicks is None and impr is None and cost is None:
            continue
        ctype = (cell(r, c_type) or "").strip().lower()
        scope = TYPE_TO_CHANNEL.get(ctype, "paid_search")
        res.rows_read += 1
        for metric, v in (("clicks", clicks), ("impressions", impr), ("spend", cost),
                          ("conversions", parse_number(cell(r, c_conv))),
                          ("revenue", parse_number(cell(r, c_value)))):
            if v is not None:
                res.put(period, scope, metric, v, add=True)
        ccy = (cell(r, c_ccy) or "").strip()
        if ccy:
            currencies.add(ccy)

    if res.rows_read == 0:
        raise ImportError_("The Google Ads export has no campaign rows with data.")
    if c_type < 0:
        res.warnings.append("There's no Campaign type column, so all spend is counted as Paid Search "
                            "(including any Display, Video, Shopping or Performance Max). Add the column "
                            "in Google Ads (Columns → Attributes → Campaign type) for an exact split.")
    if len(currencies) > 1:
        res.warnings.append("This export mixes currencies (" + ", ".join(sorted(currencies))
                            + "). Spend has been added together as-is — check it.")
    if currencies:
        res.extras["currency"] = sorted(currencies)[0]

    # Cross-check our sum against Google's own account total, if present.
    if account_total is not None:
        tc = parse_number(cell(account_total, c_cost))
        ours = sum(row.get("spend", 0) for row in res.periods[period].values())
        if tc is not None and abs(tc - ours) > max(1.0, 0.005 * tc):
            res.warnings.append(f"Campaign rows add up to {ours:,.2f} spend but Google's account total "
                                f"says {tc:,.2f}. Removed or filtered campaigns may be missing.")
    elif not totals_seen:
        res.warnings.append("No total row was found, so the figures are the sum of the campaign rows.")
    res.detected_period = period if start else None
    return res
