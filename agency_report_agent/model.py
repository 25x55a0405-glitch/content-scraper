"""The vocabulary of a marketing report: channels, metrics, and periods.

Everything else in Report Desk speaks in these terms. A client's month is a
table of `scope -> metric -> value`, where scope is a channel slug (or
"total") and metric is one of the names below. Each channel and metric also
carries the words people use for it in prose — the fact-checker uses those to
work out what a sentence is claiming.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

TOTAL = "total"


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetricDef:
    key: str
    label: str
    unit: str                 # "count" | "currency" | "percent" | "ratio" | "number"
    words: tuple[str, ...]    # how prose refers to it
    additive: bool = True     # can channel values be summed into a total?
    higher_is_better: bool = True
    decimals: int = 0


METRICS: dict[str, MetricDef] = {
    m.key: m
    for m in [
        MetricDef("sessions", "Sessions", "count",
                  ("sessions", "session", "visits", "visit", "traffic")),
        MetricDef("users", "Users", "count",
                  ("users", "user", "visitors", "visitor", "people"), additive=False),
        MetricDef("conversions", "Conversions", "count",
                  ("conversions", "conversion", "enquiries", "enquiry", "inquiries",
                   "inquiry", "leads", "lead", "key events", "bookings", "booking",
                   "sign-ups", "signups", "sign ups", "orders", "order",
                   "appointments", "appointment", "calls", "form fills",
                   "submissions", "results", "sales")),
        MetricDef("revenue", "Revenue", "currency",
                  ("revenue", "income", "sales value", "turnover", "takings"),
                  decimals=2),
        MetricDef("spend", "Spend", "currency",
                  ("spend", "spent", "spending", "cost", "costs", "budget",
                   "investment", "invested", "ad spend"),
                  higher_is_better=False, decimals=2),
        MetricDef("clicks", "Clicks", "count", ("clicks", "click")),
        MetricDef("impressions", "Impressions", "count",
                  ("impressions", "impression", "views", "visibility")),
        MetricDef("avg_position", "Avg. position", "number",
                  ("position", "ranking", "rankings", "rank", "average position"),
                  additive=False, higher_is_better=False, decimals=1),
        # Derived — computed from the base metrics, never imported.
        MetricDef("conv_rate", "Conversion rate", "percent",
                  ("conversion rate", "conv rate", "conversion rates", "converted at",
                   "converted", "converting at", "conversion"),
                  additive=False, decimals=1),
        MetricDef("cpa", "Cost per conversion", "currency",
                  ("cost per", "cpa", "cpl", "cost per acquisition", "cost per lead",
                   "cost per enquiry", "cost per conversion", "cost per booking",
                   "cost per result", "cost per order"),
                  additive=False, higher_is_better=False, decimals=2),
        MetricDef("roas", "ROAS", "ratio",
                  ("roas", "return on ad spend", "return on spend", "return"),
                  additive=False, decimals=1),
        MetricDef("ctr", "Click-through rate", "percent",
                  ("ctr", "click-through rate", "click through rate", "clickthrough rate"),
                  additive=False, decimals=1),
        MetricDef("cpc", "Cost per click", "currency",
                  ("cpc", "cost per click", "cost-per-click"),
                  additive=False, higher_is_better=False, decimals=2),
    ]
}

BASE_METRICS = ("sessions", "users", "conversions", "revenue", "spend",
                "clicks", "impressions", "avg_position")
DERIVED_METRICS = ("conv_rate", "cpa", "roas", "ctr", "cpc")


# --------------------------------------------------------------------------- #
# Channels
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ChannelDef:
    slug: str
    label: str
    words: tuple[str, ...]
    order: int


CHANNELS: dict[str, ChannelDef] = {
    c.slug: c
    for c in [
        ChannelDef("organic_search", "Organic Search",
                   ("organic search", "organic", "seo", "search engines",
                    "natural search", "unpaid search", "google organic",
                    "search console", "free search"), 10),
        ChannelDef("paid_search", "Paid Search",
                   ("paid search", "ppc", "google ads", "search ads", "adwords",
                    "sponsored search", "bing ads", "microsoft ads", "paid ads",
                    "pay-per-click", "pay per click"), 20),
        ChannelDef("organic_social", "Organic Social",
                   ("organic social", "social media", "social"), 30),
        ChannelDef("paid_social", "Paid Social",
                   ("paid social", "meta ads", "facebook ads", "instagram ads",
                    "linkedin ads", "tiktok ads", "social ads", "meta", "social"), 40),
        ChannelDef("email", "Email",
                   ("email", "e-mail", "newsletter", "newsletters", "emails"), 50),
        ChannelDef("direct", "Direct", ("direct",), 60),
        ChannelDef("referral", "Referral", ("referral", "referrals", "referring sites"), 70),
        ChannelDef("display", "Display", ("display", "banner", "banners"), 80),
        ChannelDef("paid_video", "Paid Video", ("paid video", "youtube ads", "video ads"), 90),
        ChannelDef("organic_video", "Organic Video", ("organic video", "youtube"), 95),
        ChannelDef("paid_shopping", "Paid Shopping", ("paid shopping", "shopping ads"), 100),
        ChannelDef("organic_shopping", "Organic Shopping", ("organic shopping",), 105),
        ChannelDef("affiliates", "Affiliates", ("affiliates", "affiliate"), 110),
        ChannelDef("cross_network", "Cross-network", ("cross-network", "cross network", "performance max", "pmax"), 120),
        ChannelDef("sms", "SMS", ("sms", "text message", "text messages"), 130),
        ChannelDef("unassigned", "Unassigned", ("unassigned", "not set"), 900),
        ChannelDef("other", "Other", ("other",), 950),
    ]
}

# Words that refer to the whole account rather than one channel.
TOTAL_WORDS = ("the account", "the account as a whole", "the business", "overall", "in total", "total", "across all channels", "all channels",
               "account-wide", "site-wide", "sitewide", "the website", "the site",
               "combined", "altogether", "whole account", "across the board",
               "every channel", "all sources")

# GA4 default channel group names and common variants → slug.
_CHANNEL_ALIASES = {
    "organic search": "organic_search",
    "paid search": "paid_search",
    "organic social": "organic_social",
    "paid social": "paid_social",
    "email": "email",
    "e-mail": "email",
    "direct": "direct",
    "referral": "referral",
    "display": "display",
    "paid video": "paid_video",
    "organic video": "organic_video",
    "paid shopping": "paid_shopping",
    "organic shopping": "organic_shopping",
    "affiliates": "affiliates",
    "affiliate": "affiliates",
    "cross-network": "cross_network",
    "cross network": "cross_network",
    "sms": "sms",
    "unassigned": "unassigned",
    "(not set)": "unassigned",
    "(other)": "other",
    "other": "other",
    "audio": "other",
    "mobile push notifications": "other",
    "paid other": "other",
    "seo": "organic_search",
    "ppc": "paid_search",
    "google ads": "paid_search",
    "social": "organic_social",
    # Platform names people use in their own spreadsheets (paid only: "Facebook" alone is ambiguous)
    "facebook ads": "paid_social", "meta ads": "paid_social", "instagram ads": "paid_social",
    "linkedin ads": "paid_social", "tiktok ads": "paid_social", "pinterest ads": "paid_social",
    "snapchat ads": "paid_social", "x ads": "paid_social", "twitter ads": "paid_social",
    "paid facebook": "paid_social", "paid instagram": "paid_social", "paid linkedin": "paid_social",
    "adwords": "paid_search", "bing ads": "paid_search", "microsoft ads": "paid_search",
    "microsoft advertising": "paid_search", "performance max": "cross_network", "pmax": "cross_network",
    "newsletter": "email", "emails": "email", "organic": "organic_search",
}


def normalize_channel(name: str) -> Optional[str]:
    """Map a channel name from any export to a slug, or None if unknown."""
    if name is None:
        return None
    key = re.sub(r"\s+", " ", str(name)).strip().lower()
    if not key:
        return None
    if key in CHANNELS:
        return key
    if key in _CHANNEL_ALIASES:
        return _CHANNEL_ALIASES[key]
    slug = key.replace(" ", "_").replace("-", "_")
    if slug in CHANNELS:
        return slug
    return None


def channel_label(slug: str) -> str:
    if slug == TOTAL:
        return "All channels"
    c = CHANNELS.get(slug)
    return c.label if c else slug.replace("_", " ").title()


def channel_order(slug: str) -> int:
    c = CHANNELS.get(slug)
    return c.order if c else 999


# --------------------------------------------------------------------------- #
# Periods — monthly, written "YYYY-MM"
# --------------------------------------------------------------------------- #
_PERIOD_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def is_period(value: str) -> bool:
    return bool(value) and bool(_PERIOD_RE.match(value))


def shift_period(period: str, months: int) -> str:
    y, m = (int(x) for x in period.split("-"))
    idx = y * 12 + (m - 1) + months
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def period_label(period: str) -> str:
    y, m = (int(x) for x in period.split("-"))
    return f"{MONTHS[m - 1]} {y}"


# --------------------------------------------------------------------------- #
# A month of data for one client
# --------------------------------------------------------------------------- #
@dataclass
class PeriodData:
    """Resolved figures for one client and one month."""

    period: str
    values: dict[str, dict[str, float]] = field(default_factory=dict)   # scope -> metric -> value
    origin: dict[str, dict[str, str]] = field(default_factory=dict)     # scope -> metric -> source label

    def get(self, scope: str, metric: str) -> Optional[float]:
        return self.values.get(scope, {}).get(metric)

    def set(self, scope: str, metric: str, value: float, origin: str = "") -> None:
        self.values.setdefault(scope, {})[metric] = float(value)
        if origin:
            self.origin.setdefault(scope, {})[metric] = origin

    def channels(self) -> list[str]:
        return sorted((s for s in self.values if s != TOTAL), key=channel_order)

    def metrics_present(self) -> set[str]:
        out: set[str] = set()
        for row in self.values.values():
            out.update(row)
        return out

    def is_empty(self) -> bool:
        return not any(self.values.values())

    def to_dict(self) -> dict:
        return {"period": self.period, "values": self.values, "origin": self.origin}

    @classmethod
    def from_dict(cls, d: dict) -> "PeriodData":
        return cls(period=d["period"], values={k: dict(v) for k, v in d.get("values", {}).items()},
                   origin={k: dict(v) for k, v in d.get("origin", {}).items()})


def compute_derived(pd: PeriodData) -> None:
    """Add derived metrics (rates and ratios) wherever their inputs exist."""
    for scope, row in list(pd.values.items()):
        s, c, sp, r = row.get("sessions"), row.get("conversions"), row.get("spend"), row.get("revenue")
        clk, imp = row.get("clicks"), row.get("impressions")
        if s and c is not None and s > 0:
            row["conv_rate"] = c / s * 100
        if sp is not None and c and c > 0 and sp > 0:
            row["cpa"] = sp / c
        if r is not None and sp and sp > 0:
            row["roas"] = r / sp
        if imp and clk is not None and imp > 0:
            row["ctr"] = clk / imp * 100
        if sp is not None and clk and clk > 0 and sp > 0:
            row["cpc"] = sp / clk


# Only these are meaningful summed across channels. Clicks and impressions are
# left out on purpose: organic search clicks and ad clicks are different things.
TOTAL_FILL = ("sessions", "conversions", "revenue", "spend")


def fill_totals(pd: PeriodData) -> None:
    """Sum additive metrics into a total row where no source supplied one."""
    total = pd.values.setdefault(TOTAL, {})
    for key in TOTAL_FILL:
        if key in total:
            continue
        vals = [row[key] for scope, row in pd.values.items() if scope != TOTAL and key in row]
        if vals:
            total[key] = float(sum(vals))
            pd.origin.setdefault(TOTAL, {})[key] = "sum of channels"
    if not total:
        pd.values.pop(TOTAL, None)
