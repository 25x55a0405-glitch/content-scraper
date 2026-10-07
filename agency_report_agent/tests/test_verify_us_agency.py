"""Fact-checker cases from an independent review: a US agency ($, "leads").

TRUE sentences must pass; FALSE must be flagged.
"""

import pytest

from agency_report_agent.facts import build_facts
from agency_report_agent.model import PeriodData, compute_derived, fill_totals
from agency_report_agent.verify import verify


def _pd(period, rows):
    pd = PeriodData(period, {k: dict(v) for k, v in rows.items()})
    fill_totals(pd)
    compute_derived(pd)
    return pd


SEP = _pd("2026-09", {
    "organic_search": {"sessions": 4120, "users": 3300, "conversions": 96, "clicks": 3010,
                       "impressions": 98000, "avg_position": 11.4},
    "paid_search": {"sessions": 1860, "conversions": 124, "spend": 5480.50, "clicks": 1712,
                    "impressions": 41250, "revenue": 21922.0},
    "paid_social": {"sessions": 940, "conversions": 38, "spend": 1520.00, "clicks": 1105, "impressions": 88400},
    "email": {"sessions": 610, "conversions": 21},
    "direct": {"sessions": 1350, "conversions": 19},
    "referral": {"sessions": 220, "conversions": 4},
})
AUG = _pd("2026-08", {
    "organic_search": {"sessions": 3870, "users": 3100, "conversions": 88, "clicks": 2800,
                       "impressions": 95000, "avg_position": 12.1},
    "paid_search": {"sessions": 1950, "conversions": 110, "spend": 5200.0, "clicks": 1800,
                    "impressions": 43000, "revenue": 18200.0},
    "paid_social": {"sessions": 820, "conversions": 41, "spend": 1400.0, "clicks": 1000, "impressions": 80000},
    "email": {"sessions": 540, "conversions": 25},
    "direct": {"sessions": 1300, "conversions": 18},
    "referral": {"sessions": 260, "conversions": 6},
})
SEP_LY = _pd("2025-09", {
    "organic_search": {"sessions": 3100, "conversions": 70},
    "paid_search": {"sessions": 1500, "conversions": 95, "spend": 4800.0, "revenue": 15000.0},
    "paid_social": {"sessions": 700, "conversions": 30, "spend": 1200.0},
    "email": {"sessions": 500, "conversions": 20},
    "direct": {"sessions": 1200, "conversions": 15},
    "referral": {"sessions": 200, "conversions": 5},
})


@pytest.fixture(scope="module")
def sheet():
    return build_facts(SEP, AUG, SEP_LY, target=300, currency="$", conversion_label="leads")


TRUE = [
    # B1 — "N% <comparison> increase"
    "Sessions totaled 9.1k, a 26.4% year-on-year increase.",
    "Leads totaled 302, a 28.5% year-over-year increase.",
    "Organic sessions reached 4,120, a 6.5% month-over-month increase.",
    "Paid search CPL was $44.20, a 6.5% month-on-month decrease.",
    "That represents a 4.9% MoM increase in leads.",
    # B2 — comparisons across channels
    "Organic search drove 31.8% of leads, compared to 41.1% from paid search.",
    "Paid search CPL was $44.20, compared to $40.00 on paid social.",
    "Paid search CPL was $44.20 versus $40.00 for Meta.",
    "Organic search converted at 2.3% vs 6.7% for paid search.",
    "Paid social drove 38 leads, compared with 124 from paid search.",
    "Organic search delivered 96 leads compared to 124 from Google Ads.",
    # B3 — conversion rate phrasing
    "Paid search converted 6.7% of sessions into leads, up from 5.6% in August.",
    "Paid search converted 6.7% of its sessions.",
    "Paid search's conversion rate was 6.7%, up from 5.6% in August.",
    # B4 — comparison phrase must not leak into the next clause
    "Google Ads drove 124 leads, up 12.7% month over month, at a cost per lead of $44.20.",
    "Organic search leads grew by 8 to 96, and sessions are up 32.9% year over year.",
    # B5 — plans, even under a heading
    "## Next month\n\nWe will publish 4 more pages and target a 10% lift in organic sessions.",
    "## Next month\n\nTarget: 160 leads.",
    # B6 — activity counts are not data claims
    "Organic search had a good month. We published 4 new articles and fixed 23 crawl errors.",
    "## Email\n\nThe newsletter went to 4,800 subscribers.",
    # B7 — prior year
    "Organic sessions are up 32.9% on the prior year.",
    "Organic sessions are up 32.9% on the previous year.",
    "Organic sessions are up 32.9% vs. PY.",
    "Organic sessions were 3,100 in 2025.",
    # B8 — ROAS "for every $1"
    "Paid search returned $4.00 for every $1 spent.",
    "Paid search returned $4 in revenue for every $1 of ad spend.",
    "Every dollar spent on paid search returned $4.",
    # B9 — "the account" means the total
    "Paid search had a good month. Across the account, ROAS was 3.13x.",
    # B10 — ranges
    "Leads grew 4–5% month over month.",
    "Leads grew 4-5% month over month.",
    # B11 — "more than"
    "Paid search drove more than 100 leads this month.",
    # B12 — beat the target by N
    "We beat the monthly target of 300 leads by 2.",
    # misc rounding that should pass
    "Paid social spend came to about $1.5k.",
    "Paid search spent roughly $5.5k.",
    "Paid search spent $5.5k.",
]

FALSE = [
    "Paid social spend came to $2k.",            # M1: really $1,520
    "Paid search spend was $5k.",                # M1: really $5,480
    "Paid search spend was £5,480.50.",          # M2: sheet is in dollars
    "Paid social cost per lead was €40.00.",     # M2
    "Paid search was our largest source of traffic, with 1,860 sessions.",                       # M3 (organic is)
    "Paid search was our most cost-efficient paid channel at $44.20 per lead.",                  # M3 (social $40)
    "Email was the only channel where leads fell.",                                              # M3 (also social, referral)
    # Regressions: things that must still be caught
    "Paid search delivered 150 leads.",
    "Organic search delivered 124 leads.",
    "Paid search sessions rose 8.6% month on month.",
    "Leads were up 20% year on year.",
]


@pytest.mark.parametrize("text", TRUE)
def test_true_passes(sheet, text):
    v = verify(text, sheet)
    assert v.ok, [(i.kind, i.quote, i.message) for i in v.issues]


@pytest.mark.parametrize("text", FALSE)
def test_false_flagged(sheet, text):
    assert not verify(text, sheet).ok, f"accepted: {text}"


MORE_TRUE = [
    "Spend was up 16.7% YoY, while leads were up 28.5%.",
    "Paid search returned $4 for every dollar spent.",
    "Leads were 0.7% above target.",
    "Paid search had its most efficient month this year.",
    "Brand campaigns held steady, with impression share above 90%.",
    "Paid search CPL has held in the $44–$48 range for two months.",
    "Email leads were up 5% year over year and direct leads rose 26.7%, while referral leads fell 20%.",
]
MORE_FALSE = [
    "We missed the monthly target of 300 leads by 2.",
    "Leads were 2% below target.",
    "Every channel's leads rose this month.",
    "Paid search was the best channel for ROAS, with 4.00x.",       # true: only paid search has revenue
]


@pytest.mark.parametrize("text", MORE_TRUE)
def test_more_true_passes(sheet, text):
    v = verify(text, sheet)
    assert v.ok, [(i.kind, i.quote, i.message) for i in v.issues]


@pytest.mark.parametrize("text", MORE_FALSE[:3])
def test_more_false_flagged(sheet, text):
    assert not verify(text, sheet).ok, f"accepted: {text}"


def test_ranking_message_names_the_right_channel(sheet):
    i = verify("Paid search was our largest source of traffic.", sheet).issues[0]
    assert i.kind == "wrong_ranking" and "Organic Search" in i.message and "4,120" in i.message


def test_untracked_metrics_are_unchecked_not_errors(sheet):
    v = verify("Impression share on brand terms was 90%.", sheet)
    assert v.ok and any(c.status == "unchecked" for c in v.claims)


def test_activity_counts_are_unchecked(sheet):
    v = verify("We published 4 new articles and fixed 23 crawl errors.", sheet)
    assert v.ok and sum(c.status == "unchecked" for c in v.claims) == 2


def test_currency_mismatch_message(sheet):
    i = verify("Paid search spend was £5,480.50.", sheet).issues[0]
    assert i.kind == "wrong_currency" and "$" in i.message
