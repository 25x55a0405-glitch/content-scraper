"""A realistic demo agency: Northstar Digital and twelve clients.

Every client is built from the platform exports a real agency would download,
and each one exercises something a real month throws at you:

  brightwave-dental     full stack: GA4 + Google Ads + Search Console + Meta
  harbourside-law       no social; Google Ads conversions disagree with GA4
  kestrel-accounting    organic only, no paid media at all
  oakfield-veterinary   Meta paused this month — paid social disappears
  summit-fitness        sign-ups, Ads + Meta, flat month
  verde-landscaping     organic search spike (anomaly)
  lumen-skin-clinic     GA4 comparison export: two months in one file
  copperleaf-coffee     e-commerce: revenue, ROAS, purchase values
  atlas-removals        brand-new client: this month only, no history
  fernhill-care-homes   old GA4 "Conversions" header + UTF-16 Excel export from Google Ads
  northgate-motors      big numbers: six-figure sessions, large spend
  tidewater-yoga        tiny numbers: changes that look huge but are noise

`TRUTH` records the figures each export encodes, so tests can check every
number in every report independently of the importers.
"""

from __future__ import annotations

import hashlib

from ..model import shift_period
from . import exports

AGENCY = {
    "name": "Northstar Digital",
    "brand_color": "#1B4D3E",
    "voice": ("Direct and warm. Plain English, no marketing jargon. Lead with what the numbers mean "
              "for the client's business, then what we are doing next. Never over-claim."),
    "reviewers": ["Priya Raman", "Tom Ellison", "Dani Okafor"],
    "currency": "GBP",
}

PERIOD = "2026-09"
HISTORY = [shift_period(PERIOD, -2), shift_period(PERIOD, -1), PERIOD]   # Jul, Aug, Sep 2026


def _jitter(key: str, spread: float) -> float:
    """Deterministic multiplier in [1-spread, 1+spread] — no randomness, same every run."""
    h = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return 1 + (h * 2 - 1) * spread


CLIENTS = [
    dict(id="brightwave-dental", name="Brightwave Dental", sector="Dental practice",
         label="enquiries", target=240, context="New implants landing page went live 4 September.",
         ga4={"organic_search": (3580, 71), "paid_search": (2900, 120), "organic_social": (990, 20),
              "paid_social": (700, 14), "direct": (1400, 22), "referral": (380, 6), "email": (220, 4)},
         sep={"organic_search": 1.151, "paid_search": 0.914, "organic_social": 1.889, "paid_social": 1.2,
              "direct": 1.03,
              "referral": 0.97, "email": 1.10},
         ads=[("Brand - Exact", 0.3), ("Implants - Phrase", 0.45), ("Emergency Dentist", 0.25)],
         ads_spend=3100, gsc=(2900, 61000, 9.4), meta_spend=650, yoy=True),
    dict(id="harbourside-law", name="Harbourside Law", sector="Law firm",
         label="enquiries", target=80, context="",
         ga4={"organic_search": (1610, 33), "paid_search": (1050, 31), "direct": (520, 9),
              "referral": (140, 3)},
         sep={"organic_search": 1.143, "paid_search": 0.876, "direct": 1.0, "referral": 1.05},
         ads=[("Brand", 0.2), ("Conveyancing", 0.5), ("Family Law", 0.3)],
         ads_spend=2600, ads_conv_bias=1.35, gsc=(1300, 33000, 11.2), meta_spend=None),
    dict(id="kestrel-accounting", name="Kestrel Accounting", sector="Accountancy",
         label="enquiries", target=95, context="Self-assessment season content push starts October.",
         ga4={"organic_search": (2090, 41), "direct": (900, 14), "referral": (300, 5), "email": (160, 3)},
         sep={"organic_search": 1.029, "direct": 0.98, "referral": 1.0, "email": 0.94},
         ads=None, ads_spend=None, gsc=(1750, 52000, 8.1), meta_spend=None),
    dict(id="oakfield-veterinary", name="Oakfield Veterinary", sector="Veterinary practice",
         label="bookings", target=230, context="Meta campaign paused for September while new creative is made.",
         ga4={"organic_search": (4890, 112), "paid_search": (3340, 104), "paid_social": (2610, 34),
              "direct": (1800, 30)},
         sep={"organic_search": 1.076, "paid_search": 0.934, "paid_social": 0.0, "direct": 1.02},
         ads=[("Brand", 0.25), ("Vaccinations", 0.4), ("Emergency Vet", 0.35)],
         ads_spend=4300, gsc=(3900, 88000, 7.6), meta_spend=900, meta_paused_in_sep=True),
    dict(id="summit-fitness", name="Summit Fitness", sector="Gym",
         label="sign-ups", target=300, context="",
         ga4={"organic_search": (3050, 58), "paid_search": (4100, 150), "paid_social": (1300, 29)},
         sep={"organic_search": 0.99, "paid_search": 1.0, "paid_social": 1.01},
         ads=[("Brand", 0.2), ("Gym Near Me", 0.8)], ads_spend=5000, gsc=None, meta_spend=1200),
    dict(id="verde-landscaping", name="Verde Landscaping", sector="Landscaping",
         label="enquiries", target=190, context="Garden design guide published 2 September and picked up by a national paper.",
         ga4={"organic_search": (2480, 64), "paid_search": (1920, 68), "organic_social": (2180, 30)},
         sep={"organic_search": 1.335, "paid_search": 1.031, "organic_social": 1.028},
         ads=[("Brand", 0.3), ("Garden Design", 0.7)], ads_spend=2700, gsc=(2100, 58000, 10.3),
         meta_spend=None),
    dict(id="lumen-skin-clinic", name="Lumen Skin Clinic", sector="Aesthetics clinic",
         label="consultations", target=120, context="",
         ga4={"organic_search": (1900, 38), "paid_search": (2200, 61), "paid_social": (1500, 27),
              "direct": (700, 10)},
         sep={"organic_search": 1.05, "paid_search": 1.12, "paid_social": 0.82, "direct": 1.0},
         ads=[("Brand", 0.2), ("Skin Treatments", 0.8)], ads_spend=2400, gsc=None, meta_spend=1100,
         ga4_compare=True),
    dict(id="copperleaf-coffee", name="Copperleaf Coffee", sector="E-commerce (coffee)",
         label="orders", target=900, context="Autumn blend launched 15 September.",
         ga4={"organic_search": (9800, 210), "paid_search": (6400, 260), "paid_social": (5200, 140),
              "email": (3100, 190), "direct": (4200, 120)},
         sep={"organic_search": 1.04, "paid_search": 1.09, "paid_social": 1.18, "email": 1.22, "direct": 1.0},
         aov=27.5,
         ads=[("Brand", 0.2), ("Shopping - All", 0.8)], ads_spend=4800, gsc=(7600, 210000, 12.4),
         meta_spend=3900),
    dict(id="atlas-removals", name="Atlas Removals", sector="Removals",
         label="quotes", target=60, context="New client — onboarded in September.",
         ga4={"organic_search": (800, 14), "paid_search": (1300, 41), "direct": (300, 5)},
         sep={"organic_search": 1.0, "paid_search": 1.0, "direct": 1.0},
         ads=[("Removals Local", 1.0)], ads_spend=1900, gsc=None, meta_spend=None, new_client=True),
    dict(id="fernhill-care-homes", name="Fernhill Care Homes", sector="Care homes",
         label="enquiries", target=70, context="",
         ga4={"organic_search": (2300, 29), "paid_search": (1600, 33), "direct": (1100, 12),
              "referral": (420, 8)},
         sep={"organic_search": 1.02, "paid_search": 1.06, "direct": 0.97, "referral": 1.1},
         ads=[("Care Homes Near Me", 0.7), ("Respite Care", 0.3)], ads_spend=3300, gsc=None,
         meta_spend=None, ga4_old=True, ads_excel=True),
    dict(id="northgate-motors", name="Northgate Motors", sector="Car dealership",
         label="test drives", target=1500, context="",
         ga4={"organic_search": (58000, 610), "paid_search": (41000, 720), "paid_social": (22000, 180),
              "direct": (31000, 290), "referral": (6000, 40)},
         sep={"organic_search": 0.97, "paid_search": 1.04, "paid_social": 0.93, "direct": 1.0, "referral": 1.0},
         ads=[("Brand", 0.15), ("Used Cars", 0.5), ("New Models", 0.35)], ads_spend=38000,
         gsc=(46000, 1300000, 6.8), meta_spend=14000),
    dict(id="tidewater-yoga", name="Tidewater Yoga", sector="Yoga studio",
         label="class bookings", target=12, context="",
         ga4={"organic_search": (210, 4), "organic_social": (60, 1), "direct": (40, 1)},
         sep={"organic_search": 1.0, "organic_social": 2.0, "direct": 1.5},
         ads=None, ads_spend=None, gsc=(150, 4200, 14.1), meta_spend=None),
]


def _month_values(c: dict, period: str) -> dict:
    """Build the ground-truth channel figures for one client and month."""
    base = c["ga4"]
    if period == PERIOD:
        mult = c["sep"]
    elif period == shift_period(PERIOD, -1):
        mult = {k: 1.0 for k in base}
    else:  # earlier months: deterministic drift around August
        mult = {k: round(_jitter(f"{c['id']}{period}{k}", 0.08), 3) for k in base}
    out = {}
    for slug, (sess, conv) in base.items():
        m = mult.get(slug, 1.0)
        if m == 0:
            continue                       # channel switched off this month
        s = int(round(sess * m))
        v = int(round(conv * m))
        row = {"sessions": s, "conversions": v}
        if c.get("aov"):
            row["revenue"] = round(v * c["aov"] * _jitter(f"{c['id']}{period}{slug}aov", 0.06), 2)
        out[slug] = row
    return out


def month(c: dict, period: str) -> tuple[dict[str, bytes], dict[str, dict[str, float]]]:
    """Every export file for one client-month, plus the ground truth those files encode.

    The truth is computed here, alongside the files, never by parsing them back —
    so tests that compare reports to it are independent of the importers.
    """
    chans = _month_values(c, period)
    truth: dict[str, dict[str, float]] = {slug: dict(v) for slug, v in chans.items()}
    files: dict[str, bytes] = {}
    if c.get("ga4_compare") and period == PERIOD:
        prev = shift_period(period, -1)
        files["ga4"] = exports.ga4_traffic_acquisition(c["name"], period, chans, compare_period=prev,
                                                       compare_channels=_month_values(c, prev))
    else:
        files["ga4"] = exports.ga4_traffic_acquisition(c["name"], period, chans,
                                                       old_names=c.get("ga4_old", False),
                                                       include_total=(c["id"] == "northgate-motors"))
    if c.get("ads") and "paid_search" in chans:
        ps = chans["paid_search"]
        spend_total = round(c["ads_spend"] * ps["sessions"] / c["ga4"]["paid_search"][0], 2)
        clicks_total = int(round(ps["sessions"] * 0.93))
        bias = c.get("ads_conv_bias", 1.04)
        camps, spent, clicked = [], 0.0, 0
        for i, (name, share) in enumerate(c["ads"]):
            last = i == len(c["ads"]) - 1
            clk = clicks_total - clicked if last else int(round(clicks_total * share))
            cost = round(spend_total - spent, 2) if last else round(spend_total * share, 2)
            conv = round(ps["conversions"] * bias * share, 2)
            camps.append(dict(name=name, type="Search", clicks=clk, impressions=int(round(clk / 0.061)),
                              cost=cost, conversions=conv,
                              value=round(conv * c["aov"], 2) if c.get("aov") else 0))
            spent = round(spent + cost, 2)
            clicked += clk
        files["google_ads"] = exports.google_ads_campaigns(period, camps, excel_utf16=c.get("ads_excel", False))
        truth["paid_search"].update(spend=round(sum(x["cost"] for x in camps), 2),
                                    clicks=sum(x["clicks"] for x in camps),
                                    impressions=sum(x["impressions"] for x in camps))
    if c.get("gsc") and "organic_search" in chans:
        clk, imp, pos = c["gsc"]
        m = chans["organic_search"]["sessions"] / c["ga4"]["organic_search"][0]
        gclk, gimp, gpos = int(round(clk * m)), int(round(imp * m)), round(pos / (m ** 0.3), 2)
        files["search_console"] = exports.search_console_zip(
            period, gclk, gimp, gpos,
            queries=[(f"{c['sector'].split()[0].lower()} near me", int(gclk * 0.12), int(gimp * 0.08), 3.2),
                     (c["name"].lower(), int(gclk * 0.09), int(gimp * 0.02), 1.1),
                     (f"best {c['sector'].split()[0].lower()}", int(gclk * 0.04), int(gimp * 0.05), 6.8)])
        truth["organic_search"].update(clicks=gclk, impressions=gimp, avg_position=gpos)
    if c.get("meta_spend") and "paid_social" in chans:
        ps = chans["paid_social"]
        spend = round(c["meta_spend"] * ps["sessions"] / c["ga4"]["paid_social"][0], 2)
        clicks = int(round(ps["sessions"] * 1.12))
        p_spend = round(spend * 0.7, 2)
        p_clicks = int(clicks * 0.7)
        camps = [
            dict(name="Prospecting", results=int(round(ps["conversions"] * 0.77)),
                 impressions=p_clicks * 55, spend=p_spend, link_clicks=p_clicks,
                 value=round(ps.get("revenue", 0) * 0.7, 2)),
            dict(name="Retargeting", results=int(round(ps["conversions"] * 0.33)),
                 impressions=(clicks - p_clicks) * 30, spend=round(spend - p_spend, 2),
                 link_clicks=clicks - p_clicks, value=round(ps.get("revenue", 0) * 0.3, 2)),
            dict(name="Brand Awareness", results=31000, indicator="reach", impressions=40000,
                 spend=0.0, link_clicks=0),
        ]
        files["meta_ads"] = exports.meta_ads_table(period, camps)
        truth["paid_social"].update(spend=round(sum(x["spend"] for x in camps), 2),
                                    clicks=sum(x["link_clicks"] for x in camps),
                                    impressions=sum(x["impressions"] for x in camps))
    return files, truth


def build_exports(c: dict, period: str) -> dict[str, bytes]:
    return month(c, period)[0]


def truth(c: dict, period: str) -> dict[str, dict[str, float]]:
    return month(c, period)[1]


def periods_for(c: dict) -> list[str]:
    if c.get("new_client"):
        return [PERIOD]
    ps = list(HISTORY)
    if c.get("yoy"):
        ps.insert(0, shift_period(PERIOD, -12))
    return ps


def client_def(client_id: str) -> dict:
    return next(c for c in CLIENTS if c["id"] == client_id)


def seed(store, periods: list[str] | None = None) -> list[str]:
    """Create the demo agency and import every client's exports into a workspace."""
    from ..importers import import_file
    store.save_agency(AGENCY)
    ids = []
    for c in CLIENTS:
        rec = store.client(c["id"]) or store.create_client(
            c["name"], sector=c["sector"], conversion_label=c["label"],
            monthly_target=c["target"], context=c["context"])
        ids.append(rec["id"])
        for period in periods_for(c):
            if periods is not None and period not in periods:
                continue
            for source, data in build_exports(c, period).items():
                res = import_file(source, data, period)
                store.add_source(rec["id"], res, period, filename=f"{source}-{period}", raw=data)
    return ids
