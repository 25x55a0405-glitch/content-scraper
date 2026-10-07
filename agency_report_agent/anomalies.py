"""Unusual movements a person should look at before the report goes out.

Plain arithmetic on the fact sheet — no model involved, so nothing here can be
invented. Each anomaly carries a sentence (with fact IDs) that the report can
use as written, and the reviewer can add an explanation to it.

Small numbers are deliberately ignored: a yoga studio going from 1 booking to
2 is "+100%" and means nothing. A movement is flagged only when it is large
in relative terms AND the volume behind it is big enough to matter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from .facts import Fact, FactSheet, singular
from .model import METRICS, TOTAL, channel_label, period_label

SWING = 30.0                       # % change that counts as unusual for a channel
TOTAL_SWING = 20.0                 # % change that counts as unusual for the whole account
MIN_VOLUME = {"sessions": 200, "conversions": 15, "spend": 300, "revenue": 500}
TARGET_WARN = 80.0                 # % of target below which we flag


@dataclass
class Anomaly:
    id: str
    kind: str                       # spike | drop | stopped | started | target
    scope: str
    metric: str
    text: str                       # report-ready sentence with fact citations
    fact_ids: list[str] = field(default_factory=list)
    severity: str = "notice"        # notice | important
    explanation: str = ""           # filled in by the reviewer

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Anomaly":
        return cls(**d)


def _name(sheet: FactSheet, metric: str) -> str:
    if metric == "conversions":
        return sheet.conversion_label
    if metric == "cpa":
        return f"cost per {singular(sheet.conversion_label)}"
    return METRICS[metric].label.lower()


def find_anomalies(sheet: FactSheet) -> list[Anomaly]:
    out: list[Anomaly] = []
    if not sheet.previous_period:
        return out
    prev_month = period_label(sheet.previous_period).split(" ")[0]
    scopes = list(dict.fromkeys(f.scope for f in sheet.facts))     # total first, then channel order

    def fmt(f: Fact) -> str:
        return sheet.fmt(f).lstrip("+−±")

    for scope in scopes:
        label = "Across all channels," if scope == TOTAL else f"{channel_label(scope)}"
        for metric in ("conversions", "sessions", "revenue", "spend", "cpa"):
            cur = sheet.find(scope, metric, "value", "current")
            prev = sheet.find(scope, metric, "value", "previous")
            if cur is None or prev is None:
                continue
            name = _name(sheet, metric)
            if metric == "cpa":
                conv_c = sheet.find(scope, "conversions", "value", "current")
                conv_p = sheet.find(scope, "conversions", "value", "previous")
                if not conv_c or not conv_p or conv_c.value < 10 or conv_p.value < 10:
                    continue
                vol_ok = True
            else:
                vol_ok = max(cur.value, prev.value) >= MIN_VOLUME[metric]
            if not vol_ok:
                continue
            if cur.value == 0 and prev.value > 0:
                out.append(Anomaly("", "stopped", scope, metric,
                                   f"{label} {name} fell to zero, from {fmt(prev)} in {prev_month} [{prev.id}].",
                                   [cur.id, prev.id], "important"))
                continue
            if prev.value == 0 and cur.value > 0:
                out.append(Anomaly("", "started", scope, metric,
                                   f"{label} {name} started this month, at {fmt(cur)} [{cur.id}].",
                                   [cur.id, prev.id]))
                continue
            ch = sheet.find(scope, metric, "change", "current", "mom")
            if ch is None:
                continue
            limit = TOTAL_SWING if scope == TOTAL else SWING
            if abs(ch.value) < limit:
                continue
            up = ch.value > 0
            good = up == METRICS[metric].higher_is_better
            verb = "rose" if up else "fell"
            subject = f"{label} {name}" if scope == TOTAL else f"{channel_label(scope)} {name}"
            text = (f"{subject} {verb} {fmt(ch)} on {prev_month} [{ch.id}], "
                    f"from {fmt(prev)} [{prev.id}] to {fmt(cur)} [{cur.id}].")
            out.append(Anomaly("", "spike" if up else "drop", scope, metric, text,
                               [ch.id, prev.id, cur.id], "notice" if good else "important"))

    prog = next((f for f in sheet.facts if f.kind == "target" and f.target_kind == "progress"), None)
    tgt = next((f for f in sheet.facts if f.kind == "target" and f.target_kind == "value"), None)
    if prog and tgt and prog.value < TARGET_WARN:
        out.append(Anomaly("", "target", TOTAL, "conversions",
                           f"{sheet.conversion_label.capitalize()} reached {fmt(prog)} of the monthly target "
                           f"of {fmt(tgt)} [{prog.id}, {tgt.id}].", [prog.id, tgt.id], "important"))
    # most important first, then account-level before channels
    out.sort(key=lambda a: (0 if a.severity == "important" else 1, 0 if a.scope == TOTAL else 1))
    for i, a in enumerate(out, 1):
        a.id = f"A{i}"
    return out
