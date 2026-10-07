"""Writing the report narrative.

Two writers produce the same shape of draft — markdown with fixed headings and
a fact ID after every figure:

    ## Summary            what the month meant, in three or four sentences
    ## What stood out     the biggest contributor and the biggest movers
    ## Channel by channel one bullet per channel
    ## Worth a look       unusual movements (only when there are some)
    ## Next month         only from the agency's own notes

The template writer needs no API key and is always correct by construction.
The Claude writer (see llm.py) reads better and can follow a reviewer's
requested changes; when it is unavailable the template writer takes over.
Either way, the fact checker reads every draft before a person sees it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from .anomalies import Anomaly
from .facts import Fact, FactSheet, singular
from .model import METRICS, TOTAL, channel_label, period_label

SECTIONS = ("Summary", "What stood out", "Channel by channel", "Worth a look", "Next month")
SMALL = 10          # below this, counts are described as "from X to Y", not as a percentage


@dataclass
class DraftRequest:
    sheet: FactSheet
    client: dict
    agency: dict
    anomalies: list[Anomaly] = field(default_factory=list)
    data_notes: list[str] = field(default_factory=list)       # source conflicts etc.
    next_steps: str = ""                                      # the agency's own plans for next month
    change_request: str = ""                                  # reviewer: "make it shorter", …
    previous_draft: str = ""
    verifier_feedback: str = ""


@dataclass
class DraftResult:
    text: str
    writer: str                        # template | claude
    model: Optional[str] = None
    fallback_reason: str = ""          # why Claude was not used, if it was asked for
    input_tokens: int = 0
    output_tokens: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Phrasing helpers
# --------------------------------------------------------------------------- #
class _Words:
    def __init__(self, sheet: FactSheet):
        self.sh = sheet
        self.label = sheet.conversion_label
        self.one = singular(sheet.conversion_label)
        self.prev = period_label(sheet.previous_period).split(" ")[0] if sheet.previous_period else ""
        self.month = period_label(sheet.period)

    def n(self, f: Fact) -> str:
        """The figure as the fact sheet shows it, without a sign, plus its citation."""
        g = Fact(**{**f.to_dict(), "value": abs(f.value)})
        return f"{self.sh.fmt(g).lstrip('+−±')} [{f.id}]"

    def name(self, metric: str) -> str:
        if metric == "conversions":
            return self.label
        if metric == "cpa":
            return f"cost per {self.one}"
        return METRICS[metric].label.lower() if metric not in ("ctr", "roas", "cpc") else METRICS[metric].label

    def value(self, scope: str, metric: str, period: str = "current") -> Optional[Fact]:
        return self.sh.find(scope, metric, "value", period)

    def change(self, scope: str, metric: str) -> Optional[Fact]:
        return self.sh.find(scope, metric, "change", "current", "mom")

    def movement(self, scope: str, metric: str) -> str:
        """'up 15.4% on August [F9]', 'down from 4 in August [F12]', or '' when there is nothing to compare."""
        cur, prev = self.value(scope, metric), self.value(scope, metric, "previous")
        if not cur or not prev:
            return ""
        unit = METRICS[metric].unit
        if unit == "count" and (prev.value < SMALL or cur.value < SMALL):
            if cur.value == prev.value:
                return f"the same as in {self.prev} [{prev.id}]"
            return f"{'up' if cur.value > prev.value else 'down'} from {self.n(prev)[:-len(prev.id) - 3]} " \
                   f"in {self.prev} [{prev.id}]"
        ch = self.change(scope, metric)
        if ch is None:
            return ""
        if ch.value == 0:
            return f"unchanged on {self.prev} [{ch.id}]"
        if ch.direction == "flat":
            return f"little changed on {self.prev}, {'up' if ch.value > 0 else 'down'} " \
                   f"{self.n(ch)[:-len(ch.id) - 3]} [{ch.id}]"
        return f"{'up' if ch.value > 0 else 'down'} {self.n(ch)[:-len(ch.id) - 3]} on {self.prev} [{ch.id}]"


def _sentence(*parts: str) -> str:
    text = " ".join(p for p in parts if p).strip()
    return text[0].upper() + text[1:] if text else ""


# --------------------------------------------------------------------------- #
# The template writer
# --------------------------------------------------------------------------- #
def template_draft(req: DraftRequest) -> DraftResult:
    sh, w = req.sheet, _Words(req.sheet)
    out: list[str] = []

    # ------------------------------------------------------------- Summary
    out.append("## Summary\n")
    para: list[str] = []
    conv = w.value(TOTAL, "conversions")
    if conv:
        mv = w.movement(TOTAL, "conversions")
        para.append(f"{w.month} brought {w.n(conv)} {w.label} across all channels"
                    + (f", {mv}." if mv else "."))
        gap = next((f for f in sh.facts if f.kind == "target" and f.target_kind == "gap"), None)
        tgt = next((f for f in sh.facts if f.kind == "target" and f.target_kind == "value"), None)
        if gap and tgt:
            if gap.value == 0:
                para.append(f"That is exactly on the monthly target of {w.n(tgt)}.")
            else:
                para.append(f"That puts {w.label} {w.n(gap)} {'ahead of' if gap.value > 0 else 'behind'} "
                            f"the monthly target of {w.n(tgt)}.")
    sess = w.value(TOTAL, "sessions")
    if sess:
        mv = w.movement(TOTAL, "sessions")
        para.append(f"The website had {w.n(sess)} sessions" + (f", {mv}." if mv else "."))
    spend, cpa = w.value(TOTAL, "spend"), w.value(TOTAL, "cpa")
    if spend and spend.value > 0:
        s = f"Ad spend totalled {w.n(spend)}"
        if cpa:
            s += f", which works out at {w.n(cpa)} per {w.one} across all channels"
        para.append(s + ".")
    rev = w.value(TOTAL, "revenue")
    if rev and rev.value > 0:
        mv = w.movement(TOTAL, "revenue")
        para.append(f"Revenue across all channels came to {w.n(rev)}" + (f", {mv}." if mv else "."))
        roas = w.value(TOTAL, "roas")
        if roas:
            para.append(f"Across all channels, that is a return on ad spend of {w.n(roas)}.")
    yoy = sh.find(TOTAL, "conversions", "change", "current", "yoy")
    if yoy and sh.year_ago_period:
        ya = period_label(sh.year_ago_period)
        if yoy.direction == "flat":
            para.append(f"Compared with {ya}, {w.label} across all channels were little changed, "
                        f"{'up' if yoy.value >= 0 else 'down'} {w.n(yoy)}.")
        else:
            para.append(f"Compared with {ya}, {w.label} across all channels were "
                        f"{'up' if yoy.value > 0 else 'down'} {w.n(yoy)}.")
    if not sh.previous_period:
        para.append("This is the first month we have data for, so there are no month-on-month comparisons yet.")
    if conv and conv.value < 30 and sh.previous_period:
        para.append(f"With numbers this small, some movement from month to month is normal and "
                    f"shouldn't be over-read.")
    out.append(" ".join(para) + "\n")

    # ------------------------------------------------------------- What stood out
    channels = [s for s in dict.fromkeys(f.scope for f in sh.facts) if s != TOTAL]
    stood: list[str] = []
    with_conv = [(w.value(c, "conversions"), c) for c in channels]
    with_conv = [(f, c) for f, c in with_conv if f and f.value > 0]
    top_channel = None
    if with_conv:
        top, top_channel = max(with_conv, key=lambda x: x[0].value)
        share = sh.find(top_channel, "conversions", "share", "current")
        mv = w.movement(top_channel, "conversions")
        stood.append(f"{channel_label(top_channel)} was the biggest source of {w.label}, with {w.n(top)}"
                     + (f" ({w.n(share)} of the total)" if share else "") + (f", {mv}." if mv else "."))
    if sh.previous_period:
        deltas = []
        for c in channels:
            d = sh.find(c, "conversions", "delta", "current", "mom")
            if d and d.value != 0:
                deltas.append((d.value, c))
        if deltas:
            best = max(deltas)
            worst = min(deltas)
            if best[0] > 0 and best[1] != top_channel:
                stood.append(_mover(w, best[1], "conversions"))
            if worst[0] < 0 and worst[1] not in (best[1], top_channel):
                stood.append(_mover(w, worst[1], "conversions"))
        traffic = []
        mentioned = {c for c in channels if any(s.startswith(channel_label(c)) for s in stood)}
        for c in channels:
            if c in mentioned:
                continue
            ch, cur = w.change(c, "sessions"), w.value(c, "sessions")
            prev = w.value(c, "sessions", "previous")
            if ch and cur and prev and max(cur.value, prev.value) >= 200 and ch.direction != "flat":
                traffic.append((abs(ch.value), c))
        if traffic:
            c = max(traffic)[1]
            if not any(channel_label(c) in s and "sessions" in s for s in stood):
                stood.append(_mover(w, c, "sessions"))
    if stood:
        out.append("## What stood out\n")
        out.extend(f"- {s}" for s in stood)
        out.append("")

    # ------------------------------------------------------------- Channel by channel
    out.append("## Channel by channel\n")
    for c in channels:
        out.append(f"- **{channel_label(c)}:** " + _channel_line(w, c))
    out.append("")

    # ------------------------------------------------------------- Worth a look
    if req.anomalies:
        out.append("## Worth a look\n")
        for a in req.anomalies:
            line = f"- {a.text}"
            if a.explanation.strip():
                line += f" {a.explanation.strip()}"
            out.append(line)
        out.append("")

    # ------------------------------------------------------------- Next month
    if req.next_steps.strip():
        out.append("## Next month\n")
        out.append(req.next_steps.strip() + "\n")

    return DraftResult("\n".join(out).strip() + "\n", "template")


def _mover(w: _Words, scope: str, metric: str) -> str:
    cur = w.value(scope, metric)
    mv = w.movement(scope, metric)
    name = w.name(metric)
    prev = w.value(scope, metric, "previous")
    if cur.value == 0 and prev and prev.value > 0:
        what = "had no sessions" if metric == "sessions" else f"delivered no {name}"
        return f"{channel_label(scope)} {what} this month, down from {w.n(prev)[:-len(prev.id) - 3]} " \
               f"in {w.prev} [{prev.id}]."
    if metric == "sessions":
        return _sentence(f"{channel_label(scope)} sessions were {mv}, at {w.n(cur)}.")
    return _sentence(f"{channel_label(scope)} delivered {w.n(cur)} {name}, {mv}.")


def _channel_line(w: _Words, scope: str) -> str:
    parts: list[str] = []
    sess, conv = w.value(scope, "sessions"), w.value(scope, "conversions")
    prev_sess = w.value(scope, "sessions", "previous")
    if sess is not None and sess.value == 0 and prev_sess and prev_sess.value > 0:
        parts.append(f"No sessions this month, down from {w.n(prev_sess)[:-len(prev_sess.id) - 3]} "
                     f"in {w.prev} [{prev_sess.id}].")
    elif sess or conv:
        bits = []
        if sess:
            mv = w.movement(scope, "sessions")
            bits.append(f"{w.n(sess)} sessions" + (f" ({mv})" if mv else ""))
        if conv:
            mv = w.movement(scope, "conversions")
            bits.append(f"{w.n(conv)} {w.label}" + (f" ({mv})" if mv else ""))
        parts.append(" and ".join(bits) + ".")
    spend = w.value(scope, "spend")
    if spend and spend.value > 0:
        s = f"Spend was {w.n(spend)}"
        cpa = w.value(scope, "cpa")
        if cpa:
            s += f", or {w.n(cpa)} per {w.one}"
        parts.append(s + ".")
    rev = w.value(scope, "revenue")
    if rev and rev.value > 0:
        s = f"It generated {w.n(rev)} in revenue"
        roas = w.value(scope, "roas")
        if roas and spend and spend.value > 0:
            s += f", a return on ad spend of {w.n(roas)}"
        parts.append(s + ".")
    clicks, impr = w.value(scope, "clicks"), w.value(scope, "impressions")
    if clicks and impr and impr.value > 0:
        where = "Organic listings in Google Search" if scope == "organic_search" else "The ads"
        s = f"{where} earned {w.n(clicks)} clicks from {w.n(impr)} impressions"
        pos = w.value(scope, "avg_position")
        if pos:
            s += f", at an average position of {w.n(pos)}"
        parts.append(s + ".")
    return " ".join(parts) if parts else "No activity recorded this month."
