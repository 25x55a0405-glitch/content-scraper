"""Google Analytics 4 — Traffic acquisition export (Reports → Acquisition →
Traffic acquisition → Share → Download file → CSV).

Handles the `#` header block (account, property, start/end date), the channel
dimension under any of its GA4 names, the 2024 rename of "Conversions" to
"Key events", a grand-total row when present, and comparison exports that
carry a "Date range" column (two months in one file).
"""

from __future__ import annotations

import re

from ..model import TOTAL, normalize_channel, shift_period
from .common import (ImportError_, ImportResult, cell, col, decode, is_total_row,
                     parse_date, parse_number, parse_range_text, period_from_range,
                     split_rows)

CHANNEL_COLS = ("session primary channel group", "session default channel group",
                "first user primary channel group", "first user default channel group",
                "primary channel group", "default channel group", "channel group",
                "session channel group", "channel")


def parse_ga4(data: bytes) -> ImportResult:
    text = decode(data)
    res = ImportResult(source_type="ga4")

    # --- header block ------------------------------------------------------ #
    start = end = cmp_start = cmp_end = None
    for line in text.splitlines()[:40]:
        s = line.lstrip("#").strip()
        low = s.lower()
        if low.startswith("start date") and "comparison" not in low:
            start = parse_date(s.split(":", 1)[1])
        elif low.startswith("end date") and "comparison" not in low:
            end = parse_date(s.split(":", 1)[1])
        elif "comparison" in low and "start" in low and ":" in s:
            cmp_start = parse_date(s.split(":", 1)[1])
        elif "comparison" in low and "end" in low and ":" in s:
            cmp_end = parse_date(s.split(":", 1)[1])

    rows = [r for r in split_rows(text) if r and not (r[0].startswith("#"))]
    hi = -1
    for i, r in enumerate(rows[:40]):
        lower = [c.lower() for c in r]
        if any(c in CHANNEL_COLS or "channel group" in c for c in lower) and \
           any(c.startswith("sessions") or c.startswith("key events") or c.startswith("conversions")
               or c.startswith("total users") or c.startswith("active users") for c in lower):
            hi = i
            break
    if hi < 0:
        raise ImportError_(
            "This doesn't look like a GA4 Traffic acquisition export — I couldn't find a channel "
            "column next to Sessions or Key events. In GA4 open Reports → Acquisition → Traffic "
            "acquisition, then Share → Download file → Download CSV.")
    header = rows[hi]
    c_chan = next(i for i, h in enumerate(header)
                  if h.lower() in CHANNEL_COLS or "channel group" in h.lower())
    c_range = col(header, "date range")
    cols = {
        "sessions": col(header, "sessions"),
        "users": col(header, "total users", "active users", "users"),
        "conversions": col(header, "key events", "conversions"),
        "revenue": col(header, "total revenue", "purchase revenue", "revenue"),
    }
    if cols["sessions"] < 0:
        res.warnings.append("This GA4 export has no Sessions column, so traffic figures are unavailable.")
    if cols["conversions"] < 0:
        res.warnings.append("This GA4 export has no Key events column, so conversions come from other sources only.")

    primary, warn = period_from_range(start, end)
    if warn:
        res.warnings.append(warn)
    comparison = None
    if cmp_start:
        comparison, cwarn = period_from_range(cmp_start, cmp_end)
        if cwarn:
            res.warnings.append(cwarn)

    range_period: dict[str, str] = {}
    unknown_channels: set[str] = set()
    for r in rows[hi + 1:]:
        if not any(r):
            break                                   # end of the first table
        if r[0].startswith("#"):
            break
        name = cell(r, c_chan) or ""
        period = primary
        if c_range >= 0:
            label = (cell(r, c_range) or "").strip()
            if label not in range_period:
                s2, e2 = parse_range_text(label)
                if s2:
                    p, w = period_from_range(s2, e2)
                    if w:
                        res.warnings.append(w)
                    range_period[label] = p
                elif re.search(r"\b1\b|comparison|previous", label.lower()):
                    range_period[label] = comparison or (shift_period(primary, -1) if primary else None)
                else:
                    range_period[label] = primary
            period = range_period[label]
        if not period:
            continue
        scope = TOTAL if is_total_row(name) else normalize_channel(name)
        if scope is None:
            unknown_channels.add(name)
            scope = "other"
        res.rows_read += 1
        for metric, idx in cols.items():
            v = parse_number(cell(r, idx))
            if v is None:
                continue
            # Unknown channels are pooled into "other"; total rows are taken as given.
            res.put(period, scope, metric, v, add=(scope == "other"))

    if unknown_channels:
        res.warnings.append("Grouped these unrecognised channels under Other: "
                            + ", ".join(sorted(unknown_channels)) + ".")
    if not res.periods:
        if primary is None:
            raise ImportError_("I couldn't tell which month this export covers. Pick the month above, "
                               "or re-export with the date range in the file header.")
        raise ImportError_("The export has a header but no channel rows underneath it.")
    res.detected_period = primary
    return res


def parse_ga4_for_period(data: bytes, period: str) -> ImportResult:
    """Same as parse_ga4, but fills in the period if the file doesn't state one."""
    try:
        return parse_ga4(data)
    except ImportError_ as e:
        if "which month" not in str(e):
            raise
    # Re-run treating the chosen period as the export's period.
    text = decode(data)
    y, m = period.split("-")
    patched = f"# Start date: {y}{m}01\n" + text
    res = parse_ga4(patched.encode("utf-8"))
    res.detected_period = None
    return res
