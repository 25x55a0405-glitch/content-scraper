"""Shared plumbing for reading real platform exports.

Platform exports are messier than they look: GA4 puts `#` comment lines above
the table, Google Ads' "Excel CSV" is UTF-16 and tab-separated, numbers arrive
as "£1,234.56" or "57.32%" or "--", and every platform adds its own total rows.
These helpers absorb that so each importer only maps columns.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from ..model import MONTHS

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class ImportError_(Exception):
    """A file could not be read as the selected export type. The message is user-facing."""


@dataclass
class ImportResult:
    source_type: str
    # period -> scope -> metric -> value   (a GA4 comparison export can carry two months)
    periods: dict[str, dict[str, dict[str, float]]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    rows_read: int = 0
    detected_period: Optional[str] = None
    extras: dict = field(default_factory=dict)   # e.g. top search queries

    def put(self, period: str, scope: str, metric: str, value: float, add: bool = False) -> None:
        row = self.periods.setdefault(period, {}).setdefault(scope, {})
        if add and metric in row:
            row[metric] += value
        else:
            row[metric] = value


# --------------------------------------------------------------------------- #
# Decoding
# --------------------------------------------------------------------------- #
def decode(data: bytes) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ImportError_("That file is larger than 15 MB. Export a single month and try again.")
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16")
    if len(data) > 3 and data[1:2] == b"\x00" and data[3:4] == b"\x00":
        return data.decode("utf-16-le")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ImportError_("This file isn't readable text. Upload the CSV export, not a spreadsheet.")


def looks_binary(data: bytes) -> bool:
    head = data[:2048]
    if head.startswith(b"PK"):
        return True   # zip / xlsx
    if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
        return False
    return b"\x00" in head and not (len(head) > 3 and head[1:2] == b"\x00")


def split_rows(text: str) -> list[list[str]]:
    """Parse CSV/TSV text into rows, sniffing the delimiter per file."""
    lines = text.splitlines()
    sample_lines = [ln for ln in lines if ln and not ln.lstrip().startswith("#")][:30]
    sample = "\n".join(sample_lines)
    delim = ","
    if sample.count("\t") > sample.count(","):
        delim = "\t"
    elif sample.count(";") > sample.count(",") and sample.count(";") > 2:
        delim = ";"
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    return [[cell.strip() for cell in row] for row in reader]


# --------------------------------------------------------------------------- #
# Numbers
# --------------------------------------------------------------------------- #
_NUM_CLEAN = re.compile(r"[£$€¥₹,\s ]|^(GBP|USD|EUR|AUD|CAD)\s*", re.I)


def parse_number(raw: Optional[str]) -> Optional[float]:
    """'£1,234.56' -> 1234.56; '57.3%' -> 57.3; '--', '', 'N/A' -> None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s in ("", "--", "-", "—", "n/a", "N/A", "NA", "null", "(not set)", " --"):
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    s = _NUM_CLEAN.sub("", s)
    s = s.rstrip("%")
    if s.startswith("<"):           # e.g. "< 10" anonymised
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if negative else v


# --------------------------------------------------------------------------- #
# Dates and periods
# --------------------------------------------------------------------------- #
_MONTH_INDEX = {m.lower(): i + 1 for i, m in enumerate(MONTHS)}
_MONTH_INDEX.update({m[:3].lower(): i + 1 for i, m in enumerate(MONTHS)})
_MONTH_INDEX["sept"] = 9


def parse_date(raw: str) -> Optional[date]:
    """Accepts 20260901, 2026-09-01, 01/09/2026, Sep 1, 2026, September 1, 2026, 1 Sep 2026."""
    s = (raw or "").strip().strip('"')
    if not s:
        return None
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", s)
    if m:
        return _safe_date(int(m[1]), int(m[2]), int(m[3]))
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return _safe_date(int(m[1]), int(m[2]), int(m[3]))
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:   # ambiguous; prefer day/month (UK) unless impossible
        a, b, y = int(m[1]), int(m[2]), int(m[3])
        return _safe_date(y, b, a) if b <= 12 else _safe_date(y, a, b)
    m = re.fullmatch(r"([A-Za-z]+)\.? (\d{1,2}),? (\d{4})", s)
    if m and m[1].lower() in _MONTH_INDEX:
        return _safe_date(int(m[3]), _MONTH_INDEX[m[1].lower()], int(m[2]))
    m = re.fullmatch(r"(\d{1,2}) ([A-Za-z]+)\.? (\d{4})", s)
    if m and m[2].lower() in _MONTH_INDEX:
        return _safe_date(int(m[3]), _MONTH_INDEX[m[2].lower()], int(m[1]))
    return None


def _safe_date(y: int, m: int, d: int) -> Optional[date]:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def period_from_range(start: Optional[date], end: Optional[date]) -> tuple[Optional[str], Optional[str]]:
    """Return (period, warning). A range is a valid period only if it is one calendar month."""
    if not start:
        return None, None
    period = f"{start.year:04d}-{start.month:02d}"
    if end is None:
        return period, None
    if (end.year, end.month) != (start.year, start.month):
        return None, (f"The export covers {start.isoformat()} to {end.isoformat()}, "
                      "which is more than one calendar month. Export a single month.")
    if start.day != 1:
        return period, f"The export starts on {start.isoformat()}, not the 1st — the month may be incomplete."
    nxt = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    last_day = (nxt - date.resolution).day
    if end.day != last_day:
        return period, f"The export ends on {end.isoformat()}, not the last day of the month — the month may be incomplete."
    return period, None


def parse_range_text(text: str) -> tuple[Optional[date], Optional[date]]:
    """'September 1, 2026 - September 30, 2026' or 'Sep 1, 2026 - Sep 30, 2026' or '20260901 - 20260930'."""
    t = (text or "").strip().strip('"')
    parts = re.split(r"\s+[-–—]\s+|\s+to\s+", t)
    if len(parts) == 2:
        return parse_date(parts[0]), parse_date(parts[1])
    return None, None


def find_header(rows: list[list[str]], must_have: tuple[str, ...], any_of: tuple[str, ...] = ()) -> int:
    """Index of the first row containing all `must_have` column names (case-insensitive)."""
    for i, row in enumerate(rows[:60]):
        lower = [c.lower() for c in row]
        if all(any(m == c or c.startswith(m) for c in lower) for m in must_have):
            if not any_of or any(any(a == c or c.startswith(a) for c in lower) for a in any_of):
                return i
    return -1


def col(header: list[str], *names: str) -> int:
    """Index of the first column matching any name (exact, then prefix), case-insensitive."""
    lower = [h.lower().strip() for h in header]
    for n in names:
        if n.lower() in lower:
            return lower.index(n.lower())
    for n in names:
        for i, h in enumerate(lower):
            if h.startswith(n.lower()):
                return i
    return -1


def cell(row: list[str], idx: int) -> Optional[str]:
    return row[idx] if 0 <= idx < len(row) else None


def is_total_row(first_cell: str) -> bool:
    s = (first_cell or "").strip().lower()
    return s.startswith("total") or s in ("grand total", "totals", "all", "") or s.startswith("total:")
