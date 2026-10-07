"""The fact sheet and the claim-level fact checker.

The sheet below is one client's September 2026 (with August 2026 and
September 2025). Every sentence is checked the way a client would read it.
"""

import pytest

from agency_report_agent.facts import FactSheet, build_facts, format_value, singular
from agency_report_agent.model import PeriodData, compute_derived, fill_totals
from agency_report_agent.verify import verify


def _pd(period, rows):
    pd = PeriodData(period, {k: dict(v) for k, v in rows.items()})
    fill_totals(pd)
    compute_derived(pd)
    return pd


SEP = _pd("2026-09", {
    "organic_search": {"sessions": 2900, "conversions": 82},
    "paid_search": {"sessions": 1240, "conversions": 143, "spend": 3200.34, "clicks": 1180,
                    "impressions": 30000},
    "organic_social": {"sessions": 400, "conversions": 15},
    "paid_social": {"sessions": 460, "conversions": 60, "spend": 900.0},
})
AUG = _pd("2026-08", {
    "organic_search": {"sessions": 2520, "conversions": 70},
    "paid_search": {"sessions": 1357, "conversions": 120, "spend": 3000.0, "clicks": 1100,
                    "impressions": 29000},
    "organic_social": {"sessions": 210, "conversions": 20},
    "paid_social": {"sessions": 380, "conversions": 50, "spend": 800.0},
})
SEP_LY = _pd("2025-09", {
    "organic_search": {"sessions": 2000, "conversions": 60},
    "paid_search": {"sessions": 1300, "conversions": 110, "spend": 2900.0},
    "organic_social": {"sessions": 300, "conversions": 10},
    "paid_social": {"sessions": 400, "conversions": 40, "spend": 700.0},
})


@pytest.fixture(scope="module")
def sheet() -> FactSheet:
    return build_facts(SEP, AUG, SEP_LY, target=280, currency="£", conversion_label="enquiries")


# --------------------------------------------------------------------------- #
# The fact sheet itself
# --------------------------------------------------------------------------- #
def test_sheet_basics(sheet):
    assert sheet.find("total", "conversions").value == 300
    assert sheet.find("total", "sessions").value == 5000
    ch = sheet.find("paid_search", "sessions", "change", comparison="mom")
    assert ch.value == pytest.approx((1240 - 1357) / 1357 * 100) and ch.direction == "down"
    assert sheet.find("paid_search", "cpa").value == pytest.approx(22.38, abs=1e-6)
    assert sheet.find("total", "conversions", "target") is not None
    ids = [f.id for f in sheet.facts]
    assert len(ids) == len(set(ids)) and ids[0] == "F1"
    assert sheet.facts[0].scope == "total"


def test_sheet_round_trip(sheet):
    again = FactSheet.from_dict(sheet.to_dict())
    assert [f.to_dict() for f in again.facts] == [f.to_dict() for f in sheet.facts]


def test_sheet_text_lists_ids_and_formats(sheet):
    txt = sheet.sheet_text()
    assert "[F1]" in txt and "Paid Search:" in txt and "£22.38" in txt
    assert "−8.6%" in txt                 # paid search sessions change, with a real minus sign


def test_no_previous_month_means_no_changes():
    s = build_facts(SEP, None, None)
    assert all(f.kind in ("value", "share") for f in s.facts)


def test_zero_base_has_delta_but_no_change():
    cur = _pd("2026-09", {"email": {"sessions": 50, "conversions": 2}})
    prev = _pd("2026-08", {"email": {"sessions": 0, "conversions": 0}})
    s = build_facts(cur, prev)
    assert s.find("email", "sessions", "change", comparison="mom") is None
    assert s.find("email", "sessions", "delta", comparison="mom").value == 50


@pytest.mark.parametrize("v,unit,kw,want", [
    (3200.34, "currency", {}, "£3,200"), (22.38, "currency", {"metric": "cpa"}, "£22.38"),
    (-8.62, "percent", {"signed": True}, "−8.6%"), (12.0, "percent", {"signed": True}, "+12.0%"),
    (0, "count", {"signed": True}, "±0"), (4.2, "ratio", {}, "4.20x"), (1.4, "points", {}, "1.4 pts"),
])
def test_format_value(v, unit, kw, want):
    assert format_value(v, unit, "£", **kw) == want


@pytest.mark.parametrize("w,want", [("enquiries", "enquiry"), ("class bookings", "class booking"),
                                    ("sign-ups", "sign-up"), ("leads", "lead"), ("sales", "sale"),
                                    ("key events", "key event")])
def test_singular(w, want):
    assert singular(w) == want


# --------------------------------------------------------------------------- #
# Sentences that are true and must pass
# --------------------------------------------------------------------------- #
TRUE = [
    # levels
    "Paid search delivered 143 enquiries in September.",
    "Organic search brought in 82 enquiries.",
    "Across all channels, enquiries reached 300.",
    "The website received 5,000 sessions this month.",
    "Paid search spent £3.2k.",
    "Paid search spend was £3,200.34.",
    "Paid search spent £3,200.",
    "Paid search's cost per enquiry came in at £22.38.",
    "Paid social cost £15.00 per enquiry.",
    "Paid search recorded 1,180 clicks from 30,000 impressions.",
    # changes
    "Organic sessions grew 15 percent.",
    "Organic search sessions grew 15.1% on August.",
    "Paid search sessions fell 8.6% month on month.",
    "Paid search sessions were down 8.6%.",
    "Paid search sessions slipped −8.6% versus August.",
    "Paid search enquiries rose 19.2%, from 120 to 143.",
    "Paid search enquiries rose from 120 to 143.",
    "Enquiries were up 15.4% on last month.",
    "Organic social enquiries dropped 25% to 15.",
    "Paid search delivered 23 more enquiries than in August.",
    "Paid search enquiries increased by 23.",
    "Organic search sessions rose 45% year on year.",
    "Overall sessions were up 25% on September 2025.",
    "Compared with last year, total sessions grew 25%.",
    # previous / year-ago levels
    "Organic search sessions climbed to 2,900, up from 2,520 in August.",
    "Last month, organic social delivered 20 enquiries.",
    "Organic social generated 20 enquiries in August.",
    "A year ago organic search drove 60 enquiries.",
    # shares, targets
    "Paid search accounted for 47.7% of all enquiries.",
    "Paid search generated almost half of all enquiries.",
    "Organic search drove 58% of sessions.",
    "Enquiries hit 300 against a target of 280.",
    "Enquiries finished at 107.1% of target.",
    "That put enquiries 20 ahead of target.",
    # hedges and rounding
    "Around 5,000 sessions came to the site.",
    "Paid search drove nearly 150 enquiries.",
    "Paid search delivered over 140 enquiries.",
    "Organic search sessions rose by roughly 15%.",
    "Social traffic nearly doubled.",
    "Organic social sessions nearly doubled.",
    "Paid search spent just over £3,200.",
    # derived
    "Paid search converted at 11.5%.",
    "The click-through rate on paid search was 3.9%.",
    "Paid search CPC was £2.71.",
    # citations as hints: right text, wrong citation is accepted
    "Paid search delivered 143 enquiries [F1].",
    # non-metric numbers are ignored
    "Over the last 30 days of Q3, results improved.",
    "This is your September 2026 report, covering 1 September to 30 September.",
    "We track 4 channels in GA4 for this B2B account.",
    "We published 6 new blog posts and fixed 14 technical issues.",
    "Our top 3 priorities are below.",
    # numberless direction claims that are true
    "Paid search sessions dropped this month.",
    "Organic search traffic grew.",
    "Enquiries rose across the board.",
    "Paid search cost per enquiry improved.",
    # the future is not checked
    "Next month we will raise paid search budget by 10% to reach 160 enquiries.",
    "We recommend testing a 15% bid increase on brand terms.",
    # multi-claim sentences
    "Organic search delivered 82 enquiries while paid search delivered 143.",
    "Paid search sessions fell 8.6%, but enquiries rose 19.2% to 143.",
    "Sessions fell on paid search, while organic search sessions rose 15.1%.",
]


@pytest.mark.parametrize("text", TRUE)
def test_true_sentences_pass(sheet, text):
    v = verify(text, sheet)
    assert v.ok, [i.message for i in v.issues]


# --------------------------------------------------------------------------- #
# Sentences that are wrong and must be flagged, with the right reason
# --------------------------------------------------------------------------- #
FALSE = [
    # direction
    ("Paid search sessions rose 8.6% this month.", "wrong_direction"),
    ("Paid search sessions grew +8.6%.", "wrong_direction"),
    ("Organic social enquiries rose 25%.", "wrong_direction"),
    ("Organic social enquiries climbed to 15.", "wrong_direction"),
    ("Paid search sessions increased this month.", "wrong_direction"),
    ("Organic social enquiries grew.", "wrong_direction"),
    ("Paid search cost per enquiry worsened.", "wrong_direction"),
    ("Enquiries held steady at 300.", "wrong_direction"),
    # attribution
    ("Organic search delivered 143 enquiries.", "wrong_scope"),
    ("Social sessions grew 15.1%.", "wrong_scope"),
    ("Organic search delivered 82 enquiries while paid search delivered 60.", "wrong_scope"),
    ("Enquiries came in at 143.", "wrong_scope"),
    ("Organic search sessions fell 8.6%.", "wrong_scope"),
    # period
    ("Social drove 20 enquiries this month.", "wrong_period"),
    ("Organic search sessions reached 2,520.", "wrong_period"),
    ("Total sessions rose 25% on August.", "wrong_period"),
    # metric / kind
    ("Paid search delivered 1,240 enquiries.", "wrong_metric"),
    ("Paid search sessions grew 47.7%.", "unsupported"),
    ("Cost per enquiry was £22.38.", "wrong_scope"),
    ("Paid search delivered 150.", "unsupported"),
    # invented or mis-rounded figures
    ("Paid search delivered 150 enquiries.", "unsupported"),
    ("Cost per enquiry was £21.50.", "unsupported"),
    ("Organic sessions grew 16%.", "unsupported"),
    ("Total sessions were 12,000.", "unsupported"),
    ("Paid search spent £4,000.", "unsupported"),
    ("Paid and organic search together drove 225 enquiries.", "unsupported"),
    ("Paid search ROAS was 4.2x.", "unsupported"),
    ("Enquiries were 120% of target.", "unsupported"),
    ("Paid search spent nearly £4,000.", "unsupported"),
    ("Paid search sessions more than doubled.", "wrong_direction"),
    ("Paid search generated over half of all enquiries.", "unsupported"),
    ("Email delivered 12 enquiries.", "unsupported"),
]


@pytest.mark.parametrize("text,kind", FALSE)
def test_false_sentences_flagged(sheet, text, kind):
    v = verify(text, sheet)
    assert not v.ok, f"not flagged: {text}"
    assert v.issues[0].kind == kind, [(i.kind, i.message) for i in v.issues]


def test_issue_explains_correct_figure(sheet):
    v = verify("Organic search delivered 143 enquiries.", sheet)
    i = v.issues[0]
    assert "Paid Search" in i.message and "82" in i.message
    assert i.expected and sheet.by_id(i.expected).value == 82
    assert "[F" in v.feedback_for_drafter()


def test_wrong_direction_message_names_actual_change(sheet):
    i = verify("Paid search sessions rose 8.6% this month.", sheet).issues[0]
    assert "fell" in i.message and "−8.6%" in i.message


def test_offsets_point_at_the_figure(sheet):
    text = "## Summary\n\nPaid search had a good month. Organic search delivered **143** enquiries [F3]."
    v = verify(text, sheet)
    i = v.issues[0]
    assert text[i.start:i.end] == "143"


def test_provenance_is_recorded_and_corrected(sheet):
    ps_conv = sheet.find("paid_search", "conversions")
    v = verify("Paid search delivered 143 enquiries [F1].", sheet)
    assert v.ok and v.claims[0].fact_id == ps_conv.id
    assert any("provenance corrected" in n for n in v.notes)


def test_unknown_citation_is_a_note_not_an_error(sheet):
    v = verify("Paid search delivered 143 enquiries [F9999].", sheet)
    assert v.ok and any("F9999" in n for n in v.notes)


def test_heading_scope_is_inherited(sheet):
    ok = "## Paid search\n\nEnquiries reached 143. Sessions fell 8.6%."
    assert verify(ok, sheet).ok
    bad = "## Organic search\n\nEnquiries reached 143."
    assert verify(bad, sheet).issues[0].kind == "wrong_scope"


def test_previous_sentence_scope_is_inherited(sheet):
    assert verify("Paid search had a strong month. Enquiries rose 19.2% to 143.", sheet).ok


def test_forward_looking_claims_are_listed_unchecked(sheet):
    v = verify("Next month we will aim for 400 enquiries.", sheet)
    assert v.ok and v.claims and all(c.status == "forward_looking" for c in v.claims)


def test_full_report_paragraphs(sheet):
    draft = """## Summary

September was a strong month: enquiries reached 300 [F2], up 15.4% on August, and 107.1% of the
280 target. Paid search did most of the work, delivering 143 enquiries (47.7% of the total) at a
cost per enquiry of £22.38.

## Channels

- **Organic search:** sessions grew 15.1% to 2,900, and enquiries rose from 70 to 82.
- **Paid search:** sessions fell 8.6% to 1,240, but enquiries rose 19.2%. Spend was £3,200.
- **Organic social:** sessions nearly doubled to 400, though enquiries dropped 25% to 15.
- **Paid social:** 60 enquiries at £15.00 each, from £900 of spend.

## Next month

We recommend moving £300 from paid social into paid search, which should add around 10 enquiries.
"""
    v = verify(draft, sheet)
    assert v.ok, [(i.kind, i.quote, i.message) for i in v.issues]
    assert v.checked >= 20


def test_full_report_with_planted_errors(sheet):
    draft = """## Summary

Enquiries reached 300, up 15.4% on August. Paid search delivered 143 enquiries.

## Channels

- **Organic search:** sessions grew 15.1% to 2,900, and enquiries rose to 92.
- **Paid search:** sessions rose 8.6% to 1,240.
- **Organic social:** enquiries climbed to 20.
"""
    v = verify(draft, sheet)
    kinds = sorted(i.kind for i in v.issues)
    quotes = sorted(i.quote for i in v.issues)
    assert "92" in quotes and "8.6%" in quotes and "20" in quotes, quotes
    assert "wrong_direction" in kinds and "unsupported" in kinds and "wrong_period" in kinds
    assert len(v.issues) == 3


def test_empty_and_numberless(sheet):
    assert verify("", sheet).ok
    assert verify("Thanks for another great month working together.", sheet).ok


def test_conversion_label_vocabulary():
    s = build_facts(SEP, AUG, conversion_label="class bookings")
    assert verify("Paid search drove 143 class bookings at £22.38 per class booking.", s).ok
    assert not verify("Paid search drove 82 class bookings.", s).ok


# --------------------------------------------------------------------------- #
# Realistic account-manager prose
# --------------------------------------------------------------------------- #
PROSE_TRUE = [
    "September delivered 300 enquiries — your best month this year — beating the 280 target by 20.",
    "Enquiries rose to 300 from 260 in August, a 15.4% increase.",
    "Organic search continues to be the biggest traffic driver, bringing 2,900 sessions (58% of the total).",
    "Paid search traffic dipped 8.6% month-on-month to 1,240 sessions, yet enquiries from the channel "
    "climbed 19.2% to 143.",
    "That means paid search's cost per enquiry is now £22.38, with £3,200 invested across the month.",
    "Social media had a mixed month: organic social sessions almost doubled (from 210 to 400) but "
    "enquiries slipped from 20 to 15.",
    "Paid social generated 60 enquiries from £900 spend, a cost per enquiry of £15.00.",
    "Year on year, total sessions are up 25%.",
    "Compared to September 2025, organic search sessions are 45% higher.",
    "Overall, the account generated 300 enquiries, which is 107.1% of target.",
    "Paid search's click-through rate was 3.9% on 30,000 impressions.",
    "We spent £4,100 across paid channels this month.",
    "Paid search drove 47.7% of enquiries, the largest share of any channel.",
    "Organic search accounted for 27.3% of enquiries.",
    "Enquiries from organic search grew by 12, to 82.",
    "Over the month, paid search averaged £2.71 per click.",
    "Total spend across Google Ads and Meta was £4,100.",
    "Organic social enquiries fell by 5 to 15.",
    "In August, paid search generated 120 enquiries; in September it generated 143.",
    "The 15.4% increase in enquiries came mainly from paid search.",
]
PROSE_FALSE = [
    "September delivered 310 enquiries, beating the 280 target by 30.",
    "Enquiries rose to 300 from 250 in August.",
    "Organic search brought 2,900 sessions (62% of the total).",
    "Paid search traffic grew 8.6% month-on-month to 1,240 sessions.",
    "Paid search's cost per enquiry is now £15.00.",
    "Organic social enquiries rose from 15 to 20.",
    "Paid social generated 143 enquiries from £900 spend.",
    "Year on year, total sessions are up 15.4%.",
    "We spent £3,200 across paid channels this month.",
    "Paid search drove 58% of enquiries.",
    "Organic search enquiries grew by 23, to 82.",
    "Total spend across Google Ads and Meta was £3,800.",
    "Paid social delivered 15 enquiries.",
    "Enquiries were down 15.4% on last month.",
    "Organic search sessions fell year on year.",
    "Google Ads and Meta together delivered 143 enquiries.",
]


@pytest.mark.parametrize("text", PROSE_TRUE)
def test_prose_true(sheet, text):
    v = verify(text, sheet)
    assert v.ok, [(i.kind, i.quote, i.message) for i in v.issues]


@pytest.mark.parametrize("text", PROSE_FALSE)
def test_prose_false(sheet, text):
    assert not verify(text, sheet).ok


PROSE2_TRUE = [
    "Hi Sarah, here's your September 2026 performance summary.",
    "It was a strong month overall. Enquiries reached 300, up 15.4% on August and 20 ahead of your 280 target.",
    "Organic search remains your largest channel by traffic. Sessions grew 15.1% to 2,900, and enquiries "
    "rose 17.1% to 82.",
    "Paid search was the standout for leads. Although clicks rose to 1,180, sessions fell 8.6%; enquiries "
    "still climbed 19.2% to 143. With £3,200 of spend, that's £22.38 per enquiry.",
    "On social, organic sessions rose 90.5% to 400, the result of two viral posts.",
    "However, organic social enquiries fell 25%, from 20 to 15.",
    "Meta ads produced 60 enquiries at £15.00 each, from £900.",
    "Sessions across the site totalled 5,000, a 25% increase on September last year.",
    "Paid search's conversion rate improved to 11.5%.",
    "Paid search CTR came in at 3.93%.",
    "Organic search's share of sessions was 58.0%.",
    "Paid social enquiries were up 20% on last month.",
    "Enquiries were up 36.4% year on year.",
    "Paid search sessions were 4.6% lower than a year ago.",
    "Paid search enquiries have risen 30% year-on-year.",
    "Top 5 queries are listed in the appendix.",
    "Enquiries from organic search were 82 (up from 70).",
    "Paid social spend rose 12.5% to £900.",
    "Paid search spend increased by £200.",
    "Organic social delivered 15 enquiries, 5 fewer than in August.",
    "There were 40 more enquiries than in August.",
    "Paid social cost per enquiry fell slightly, from £16.00 to £15.00.",
]
PROSE2_FALSE = [
    "Enquiries reached 300, up 15.4% on August and 30 ahead of your 280 target.",
    "Organic search sessions grew 15.1% to 2,520.",
    "Paid search clicks rose to 1,240.",
    "Paid search spent £3,200, which is £15.00 per enquiry.",
    "Organic social enquiries fell 25%, from 20 to 10.",
    "Meta ads produced 60 enquiries at £22.38 each.",
    "Paid search's conversion rate fell to 11.5%.",
    "Organic search's share of sessions was 48.0%.",
    "Paid social enquiries were up 20% year on year.",
    "Paid search sessions were 4.6% higher than a year ago.",
    "Paid social spend fell 12.5% to £900.",
    "There were 40 fewer enquiries than in August.",
    "Paid social cost per enquiry rose from £16.00 to £15.00.",
    "Paid search spend increased by £300.",
    "Organic search delivered 15 enquiries, 5 fewer than in August.",
]


@pytest.mark.parametrize("text", PROSE2_TRUE)
def test_prose2_true(sheet, text):
    v = verify(text, sheet)
    assert v.ok, [(i.kind, i.quote, i.message) for i in v.issues]


@pytest.mark.parametrize("text", PROSE2_FALSE)
def test_prose2_false(sheet, text):
    assert not verify(text, sheet).ok
