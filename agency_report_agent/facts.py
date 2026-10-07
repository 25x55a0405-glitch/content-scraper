"""The fact sheet: every figure a report is allowed to state, each with an ID.

Facts are built from the resolved month (and the month before, and the same
month last year when available). The drafter is shown the sheet and must cite
fact IDs; the verifier checks every number in a draft against it.

Kinds of fact
    value    a figure for one period            "Paid Search conversions, Sep: 143"
    change   relative change between periods    "…conversions, MoM: +19.2%"
    delta    absolute difference                "…conversions, MoM: +23"
    share    share of the total                 "…share of all conversions: 56.5%"
    target   target, progress, gap              "Conversions vs target: 105.4%"
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from .model import (METRICS, TOTAL, PeriodData, channel_label, channel_order,
                    period_label)

FLAT_BAND = 2.5     # a change smaller than this (in %) can honestly be called flat
SHARE_METRICS = ("sessions", "conversions", "revenue", "spend")


@dataclass
class Fact:
    id: str
    scope: str
    metric: str
    kind: str                       # value | change | delta | share | target
    period: str                     # current | previous | year_ago
    value: float
    unit: str                       # count | currency | percent | ratio | number | points
    label: str
    comparison: Optional[str] = None    # mom | yoy   (change and delta only)
    direction: Optional[str] = None     # up | down | flat
    base: Optional[float] = None        # the earlier value of a change
    target_kind: Optional[str] = None   # value | progress | gap

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FactSheet:
    facts: list[Fact] = field(default_factory=list)
    period: str = ""
    previous_period: Optional[str] = None
    year_ago_period: Optional[str] = None
    currency: str = "£"
    conversion_label: str = "conversions"

    def by_id(self, fid: str) -> Optional[Fact]:
        for f in self.facts:
            if f.id == fid:
                return f
        return None

    def find(self, scope: str, metric: str, kind: str = "value", period: str = "current",
             comparison: Optional[str] = None) -> Optional[Fact]:
        for f in self.facts:
            if (f.scope, f.metric, f.kind, f.period) == (scope, metric, kind, period) and \
               (comparison is None or f.comparison == comparison):
                return f
        return None

    def to_dict(self) -> dict:
        return {"period": self.period, "previous_period": self.previous_period,
                "year_ago_period": self.year_ago_period, "currency": self.currency,
                "conversion_label": self.conversion_label,
                "facts": [f.to_dict() for f in self.facts]}

    @classmethod
    def from_dict(cls, d: dict) -> "FactSheet":
        return cls(facts=[Fact(**f) for f in d["facts"]], period=d["period"],
                   previous_period=d.get("previous_period"), year_ago_period=d.get("year_ago_period"),
                   currency=d.get("currency", "£"), conversion_label=d.get("conversion_label", "conversions"))

    # ------------------------------------------------------------ display
    def fmt(self, f: Fact) -> str:
        return format_value(f.value, f.unit if f.kind != "value" else METRICS.get(f.metric).unit
                            if f.metric in METRICS else f.unit, self.currency,
                            signed=f.kind in ("change", "delta"), metric=f.metric)

    def sheet_text(self, include_all: bool = False) -> str:
        """The fact sheet as the drafter sees it: one line per fact, grouped by channel."""
        lines, last_scope = [], None
        for f in self.facts:
            if not include_all and not _show_to_drafter(f):
                continue
            if f.scope != last_scope:
                lines.append(f"\n{channel_label(f.scope)}:")
                last_scope = f.scope
            lines.append(f"  [{f.id}] {f.label}: {self.fmt(f)}")
        return "\n".join(lines).strip()


def _show_to_drafter(f: Fact) -> bool:
    # Keep the sheet readable: skip the long tail the model rarely needs.
    if f.kind == "delta" and f.metric not in ("conversions", "revenue", "spend"):
        return False
    if f.kind == "share" and f.metric not in ("sessions", "conversions", "revenue"):
        return False
    return True


def format_value(v: float, unit: str, currency: str = "£", signed: bool = False, metric: str = "") -> str:
    sign = ""
    if signed:
        sign = "+" if v > 0 else ("−" if v < 0 else "±")
        v = abs(v)
    if unit == "currency":
        if metric in ("cpa", "cpc") or v < 100:
            s = f"{currency}{v:,.2f}"
        else:
            s = f"{currency}{v:,.0f}"
    elif unit == "percent":
        s = f"{v:,.1f}%"
    elif unit == "points":
        s = f"{v:,.1f} pts"
    elif unit == "ratio":
        s = f"{v:,.2f}x"
    elif unit == "number":
        s = f"{v:,.1f}"
    else:
        s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"
    return sign + s


def _direction(change_pct: float) -> str:
    if abs(change_pct) < FLAT_BAND:
        return "flat"
    return "up" if change_pct > 0 else "down"


def build_facts(current: PeriodData, previous: Optional[PeriodData] = None,
                year_ago: Optional[PeriodData] = None, *, target: Optional[float] = None,
                currency: str = "£", conversion_label: str = "conversions") -> FactSheet:
    sheet = FactSheet(period=current.period,
                      previous_period=previous.period if previous and not previous.is_empty() else None,
                      year_ago_period=year_ago.period if year_ago and not year_ago.is_empty() else None,
                      currency=currency, conversion_label=conversion_label)
    facts: list[Fact] = []
    cur_lbl = period_label(current.period)
    prev_lbl = period_label(previous.period) if sheet.previous_period else ""
    yago_lbl = period_label(year_ago.period) if sheet.year_ago_period else ""

    current = _with_missing_channels(current, previous)
    scopes = ([TOTAL] if TOTAL in current.values else []) + current.channels()
    metric_order = [m for m in METRICS]

    def mlabel(m: str) -> str:
        if m == "conversions":
            return conversion_label
        if m == "cpa":
            return f"cost per {singular(conversion_label)}"
        return METRICS[m].label.lower() if m not in ("ctr", "roas", "cpc") else METRICS[m].label

    for scope in scopes:
        row = current.values.get(scope, {})
        sname = channel_label(scope)
        for m in metric_order:
            if m not in row:
                continue
            md = METRICS[m]
            v = row[m]
            facts.append(Fact("", scope, m, "value", "current", v, md.unit,
                              f"{sname} {mlabel(m)}, {cur_lbl}"))
            for per, other, lbl, comp in (("previous", previous, prev_lbl, "mom"),
                                          ("year_ago", year_ago, yago_lbl, "yoy")):
                if not other or other.is_empty():
                    continue
                ov = other.get(scope, m)
                if ov is None:
                    continue
                facts.append(Fact("", scope, m, "value", per, ov, md.unit, f"{sname} {mlabel(m)}, {lbl}"))
                if ov != 0:
                    pct = (v - ov) / abs(ov) * 100
                    facts.append(Fact("", scope, m, "change", "current", pct, "percent",
                                      f"{sname} {mlabel(m)}, change vs {lbl}", comparison=comp,
                                      direction=_direction(pct), base=ov))
                d = v - ov
                d_unit = "points" if md.unit == "percent" else md.unit
                facts.append(Fact("", scope, m, "delta", "current", d, d_unit,
                                  f"{sname} {mlabel(m)}, difference vs {lbl}", comparison=comp,
                                  direction=_direction((d / abs(ov) * 100) if ov else (100 if d else 0)),
                                  base=ov))
        # Share of the account total, for additive metrics.
        if scope != TOTAL:
            tot = current.values.get(TOTAL, {})
            for m in SHARE_METRICS:
                if m in row and tot.get(m):
                    facts.append(Fact("", scope, m, "share", "current", row[m] / tot[m] * 100, "percent",
                                      f"{sname} share of all {mlabel(m)}, {cur_lbl}"))

    tot_conv = current.get(TOTAL, "conversions")
    if target and tot_conv is not None:
        facts.append(Fact("", TOTAL, "conversions", "target", "current", float(target), "count",
                          f"Monthly target for {conversion_label}", target_kind="value"))
        facts.append(Fact("", TOTAL, "conversions", "target", "current", tot_conv / target * 100, "percent",
                          f"{conversion_label.capitalize()} as % of target", target_kind="progress"))
        gap = tot_conv - target
        facts.append(Fact("", TOTAL, "conversions", "target", "current", gap, "count",
                          f"{conversion_label.capitalize()} above (+) or below (−) target",
                          target_kind="gap", direction="up" if gap >= 0 else "down"))

    facts.sort(key=lambda f: (0 if f.scope == TOTAL else 1, channel_order(f.scope),
                              metric_order.index(f.metric),
                              ["value", "change", "delta", "share", "target"].index(f.kind),
                              ["current", "previous", "year_ago"].index(f.period),
                              f.comparison or ""))
    for i, f in enumerate(facts, 1):
        f.id = f"F{i}"
    sheet.facts = facts
    return sheet


# Analytics exports leave out channels with no traffic. If a channel had sessions last month
# and is absent this month while other channels report sessions, it had none.
ZERO_FILL = ("sessions", "conversions", "revenue")


def _with_missing_channels(current: PeriodData, previous: Optional[PeriodData]) -> PeriodData:
    if not previous or previous.is_empty():
        return current
    from .model import compute_derived
    out = PeriodData.from_dict(current.to_dict())
    reported = {m for s, row in current.values.items() if s != TOTAL for m in row}
    for scope, row in previous.values.items():
        if scope == TOTAL or scope in current.values:
            continue
        added = False
        for m in ZERO_FILL:
            if m in row and m in reported:
                out.set(scope, m, 0.0, "not in this month's export")
                added = True
        if added:
            compute_derived(out)
    return out


def singular(label: str) -> str:
    """'enquiries' -> 'enquiry', 'class bookings' -> 'class booking', 'sign-ups' -> 'sign-up'."""
    words = label.strip().split(" ")
    w = words[-1]
    if w.endswith("ies") and len(w) > 4:
        w = w[:-3] + "y"
    elif w.endswith("ses") or w.endswith("xes") or w.endswith("ches") or w.endswith("shes"):
        w = w[:-2]
    elif w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    words[-1] = w
    return " ".join(words)
