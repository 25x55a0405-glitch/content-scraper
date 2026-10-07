"""Every fact of every demo client, stated truly and falsely.

For each of the 12 demo clients the September fact sheet is built from the
seeded workspace. Each fact is written out as a sentence in the way a report
would phrase it (that must pass), then mutated — wrong number, wrong channel,
wrong direction, wrong month — and every mutation must be caught.
"""

import pytest

from agency_report_agent.demo import agency as demo
from agency_report_agent.facts import FactSheet, build_facts, singular
from agency_report_agent.model import METRICS, MONTHS, TOTAL, channel_label, shift_period
from agency_report_agent.store import Store
from agency_report_agent.verify import verify


@pytest.fixture(scope="module")
def sheets(tmp_path_factory) -> dict[str, FactSheet]:
    store = Store(tmp_path_factory.mktemp("ws"))
    demo.seed(store)
    out = {}
    for c in demo.CLIENTS:
        cur, _ = store.period_data(c["id"], demo.PERIOD)
        prev, _ = store.period_data(c["id"], shift_period(demo.PERIOD, -1))
        yago, _ = store.period_data(c["id"], shift_period(demo.PERIOD, -12))
        out[c["id"]] = build_facts(cur, prev, yago, target=c["target"], currency="£",
                                   conversion_label=c["label"])
    return out


def _mname(sheet: FactSheet, m: str) -> str:
    if m == "conversions":
        return sheet.conversion_label
    if m == "cpa":
        return f"cost per {singular(sheet.conversion_label)}"
    return METRICS[m].label.lower() if m not in ("ctr", "roas", "cpc") else METRICS[m].label


def _num(sheet: FactSheet, f, value=None) -> str:
    g = f if value is None else type(f)(**{**f.to_dict(), "value": value})
    return sheet.fmt(g).lstrip("+−±")


def _subject(scope: str) -> str:
    return "Across all channels," if scope == TOTAL else f"For {channel_label(scope)},"


def _month(period: str) -> str:
    y, m = (int(x) for x in period.split("-"))
    return f"{MONTHS[m - 1]} {y}"


def sentence(sheet: FactSheet, f, value=None, scope=None, direction=None, period=None) -> str:
    scope = scope or f.scope
    name = _mname(sheet, f.metric)
    v = _num(sheet, f, value)
    subj = _subject(scope)
    if f.kind == "value":
        when = {"current": "this month", "previous": f"in {_month(sheet.previous_period or sheet.period)}",
                "year_ago": f"in {_month(sheet.year_ago_period or sheet.period)}"}[period or f.period]
        return f"{subj} {name} came in at {v} {when}."
    if f.kind in ("change", "delta"):
        d = direction or ("rose" if f.value > 0 else "fell")
        comp = "month on month" if f.comparison == "mom" else "year on year"
        return f"{subj} {name} {d} by {v} {comp}."
    if f.kind == "share":
        return f"{subj} the channel accounted for {v} of all {name}."
    if f.target_kind == "value":
        return f"{sheet.conversion_label.capitalize()} were measured against a target of {v}."
    if f.target_kind == "progress":
        return f"{sheet.conversion_label.capitalize()} finished at {v} of target."
    if f.value < 0:
        v = v.lstrip("-")
    return f"{sheet.conversion_label.capitalize()} finished {v} {'ahead of' if f.value >= 0 else 'behind'} target."


def _cases(sheet: FactSheet):
    for f in sheet.facts:
        if f.kind in ("change", "delta") and abs(f.value) < 0.05:
            continue
        if f.kind == "change" and f.direction == "flat":
            continue
        yield f


def test_every_fact_stated_truly_passes(sheets):
    failures, n = [], 0
    for cid, sheet in sheets.items():
        for f in _cases(sheet):
            text = sentence(sheet, f)
            n += 1
            v = verify(text, sheet)
            if not v.ok:
                failures.append((cid, text, [(i.kind, i.message) for i in v.issues]))
    assert n > 1000
    assert not failures, f"{len(failures)} of {n} true sentences rejected, e.g. {failures[:5]}"


def _differs(f, other_value) -> bool:
    if other_value is None:
        return True
    a, b = abs(f.value), abs(other_value)
    return abs(a - b) > max(0.02 * max(a, b), 1.0 if f.unit in ("count",) else 0.11)


def test_wrong_numbers_are_caught(sheets):
    missed, n = [], 0
    for cid, sheet in sheets.items():
        for f in _cases(sheet):
            if abs(f.value) < 5:
                continue
            for factor in (1.12, 0.85):
                text = sentence(sheet, f, value=f.value * factor)
                if _num(sheet, f, f.value * factor) == _num(sheet, f):
                    continue
                n += 1
                if verify(text, sheet).ok:
                    missed.append((cid, text))
    assert n > 1000
    assert not missed, f"{len(missed)} of {n} wrong numbers accepted, e.g. {missed[:5]}"


def test_wrong_channel_is_caught(sheets):
    missed, n = [], 0
    for cid, sheet in sheets.items():
        scopes = sorted({f.scope for f in sheet.facts if f.scope != TOTAL})
        for f in _cases(sheet):
            if f.scope == TOTAL or f.kind == "target":
                continue
            for other in scopes:
                if other == f.scope:
                    continue
                twin = sheet.find(other, f.metric, f.kind, f.period, f.comparison)
                if twin is not None and not _differs(f, twin.value):
                    continue                 # the other channel genuinely has the same figure
                n += 1
                text = sentence(sheet, f, scope=other)
                if verify(text, sheet).ok:
                    missed.append((cid, text))
    assert n > 1000
    assert not missed, f"{len(missed)} of {n} misattributed figures accepted, e.g. {missed[:5]}"


def test_wrong_direction_is_caught(sheets):
    missed, n = [], 0
    for cid, sheet in sheets.items():
        for f in _cases(sheet):
            if f.kind not in ("change", "delta") or (f.kind == "change" and abs(f.value) < 3):
                continue
            n += 1
            text = sentence(sheet, f, direction="fell" if f.value > 0 else "rose")
            if verify(text, sheet).ok:
                missed.append((cid, text))
    assert n > 200
    assert not missed, f"{len(missed)} of {n} wrong directions accepted, e.g. {missed[:5]}"


def test_wrong_month_is_caught(sheets):
    missed, n = [], 0
    for cid, sheet in sheets.items():
        for f in _cases(sheet):
            if f.kind != "value" or f.period != "current" or not sheet.previous_period:
                continue
            prev = sheet.find(f.scope, f.metric, "value", "previous")
            if prev is not None and not _differs(f, prev.value):
                continue
            n += 1
            text = sentence(sheet, f, period="previous")
            if verify(text, sheet).ok:
                missed.append((cid, text))
    assert n > 100
    assert not missed, f"{len(missed)} of {n} wrong-month figures accepted, e.g. {missed[:5]}"
