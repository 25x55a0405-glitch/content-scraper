"""Helpers for turning raw client numbers into the facts a report talks about.

Kept separate from the graph so the number-checking logic is easy to read and
test on its own. None of this calls an AI model — it is plain arithmetic.
"""

from __future__ import annotations

import re
from typing import Any

# A channel swing bigger than this (up or down) gets flagged for a human to explain.
ANOMALY_THRESHOLD_PCT = 40.0


def pct_change(current: float, previous: float) -> float | None:
    """Percentage change from previous to current, rounded to one decimal.

    Returns None when there is no previous value to compare against.
    """
    if previous in (0, None):
        return None
    return round((current - previous) / previous * 100, 1)


def summarise_channels(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten the client file into one tidy row per channel."""
    rows: list[dict[str, Any]] = []
    for key, c in data.get("channels", {}).items():
        rows.append(
            {
                "channel": key.replace("_", " ").title(),
                "sessions": c.get("sessions"),
                "sessions_change": pct_change(c.get("sessions", 0), c.get("prev_sessions", 0)),
                "conversions": c.get("conversions"),
                "conversions_change": pct_change(c.get("conversions", 0), c.get("prev_conversions", 0)),
                "spend": c.get("spend"),
            }
        )
    return rows


def totals(data: dict[str, Any]) -> dict[str, Any]:
    """Roll the channels up into whole-account totals."""
    channels = data.get("channels", {}).values()
    total_conversions = sum(c.get("conversions", 0) for c in channels)
    prev_conversions = sum(c.get("prev_conversions", 0) for c in channels)
    total_sessions = sum(c.get("sessions", 0) for c in channels)
    prev_sessions = sum(c.get("prev_sessions", 0) for c in channels)
    return {
        "total_sessions": total_sessions,
        "total_sessions_change": pct_change(total_sessions, prev_sessions),
        "total_conversions": total_conversions,
        "total_conversions_change": pct_change(total_conversions, prev_conversions),
        "leads_target": data.get("goals", {}).get("monthly_leads_target"),
    }


def find_anomalies(data: dict[str, Any]) -> list[str]:
    """Flag any channel whose sessions or conversions moved by a lot."""
    flags: list[str] = []
    for row in summarise_channels(data):
        for metric in ("sessions_change", "conversions_change"):
            change = row[metric]
            if change is not None and abs(change) >= ANOMALY_THRESHOLD_PCT:
                label = metric.replace("_change", "")
                direction = "up" if change > 0 else "down"
                flags.append(
                    f"{row['channel']} {label} {direction} {abs(change)}% — needs a human explanation"
                )
    return flags


def allowed_counts(data: dict[str, Any]) -> set[float]:
    """Every plain count a truthful report may state: raw values and totals.

    These are the numbers NOT written as a percentage — sessions, conversions,
    spend, the leads target, and the account-wide totals.
    """
    nums: set[float] = set()

    def add(value: Any) -> None:
        if isinstance(value, (int, float)):
            nums.add(round(float(value), 1))

    for c in data.get("channels", {}).values():
        for v in c.values():
            add(v)
    t = totals(data)
    add(t["total_sessions"])
    add(t["total_conversions"])
    add(t["leads_target"])
    return nums


def allowed_percentages(data: dict[str, Any]) -> set[float]:
    """Every percentage a truthful report may state.

    Two kinds: month-over-month changes, and conversion rates
    (conversions / sessions). We include both the signed value and its absolute
    value, because a report may write "+15.1%" or just "15.1%".
    """
    nums: set[float] = set()

    def add(value: Any) -> None:
        if isinstance(value, (int, float)):
            nums.add(round(float(value), 1))
            nums.add(round(abs(float(value)), 1))

    # Month-over-month changes per channel and overall.
    for row in summarise_channels(data):
        add(row["sessions_change"])
        add(row["conversions_change"])
    t = totals(data)
    add(t["total_sessions_change"])
    add(t["total_conversions_change"])

    # Conversion rates (this period and last), per channel and overall.
    for c in data.get("channels", {}).values():
        if c.get("sessions"):
            add(c["conversions"] / c["sessions"] * 100)
        if c.get("prev_sessions"):
            add(c["prev_conversions"] / c["prev_sessions"] * 100)
    if t["total_sessions"]:
        add(t["total_conversions"] / t["total_sessions"] * 100)
    return nums


# A number, optionally followed (allowing one space) by a percent sign.
_NUMBER_RE = re.compile(r"(-?\d[\d,]*\.?\d*)\s*(%?)")


def numbers_in_text(text: str) -> list[tuple[float, bool]]:
    """Pull every number out of text as (value, is_percentage).

    Four-digit years like 2026 are treated as labels and skipped.
    """
    found: list[tuple[float, bool]] = []
    for raw, pct in _NUMBER_RE.findall(text):
        cleaned = raw.replace(",", "")
        try:
            value = float(cleaned)
        except ValueError:
            continue
        is_percent = pct == "%"
        if not is_percent and 1900 <= value <= 2100 and value == int(value):
            continue  # a year, not a metric
        found.append((round(value, 1), is_percent))
    return found


def verify_draft(draft: str, data: dict[str, Any], tolerance: float = 0.5) -> list[str]:
    """Return a list of numbers in the draft that don't match the source data.

    Percentages are checked against the real percentage changes and conversion
    rates; plain counts are checked against the real counts. An empty list means
    every number checks out.

    Known limit: this validates figures that come straight from the data or are
    simple month-over-month changes / conversion rates. A report that cites some
    other derived metric would be flagged — add it to the allowed sets above if
    you want the agent to use it.
    """
    counts = allowed_counts(data)
    percentages = allowed_percentages(data)
    issues: list[str] = []
    for value, is_percent in numbers_in_text(draft):
        allowed = percentages if is_percent else counts
        if any(abs(value - ok) <= tolerance for ok in allowed):
            continue
        shown = f"{value:g}%" if is_percent else f"{value:g}"
        kind = "percentage" if is_percent else "figure"
        issues.append(
            f'The draft states the {kind} "{shown}", which does not match the client data.'
        )
    # De-duplicate while keeping order.
    seen: set[str] = set()
    unique: list[str] = []
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            unique.append(issue)
    return unique
