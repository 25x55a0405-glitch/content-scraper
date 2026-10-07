"""Writers that produce byte-for-byte realistic platform exports.

Used to seed the demo workspace and to drive the end-to-end tests. Each
writer mirrors what the real platform downloads, quirks included: GA4's `#`
header block and decimal rates, Google Ads' title line and "Total:" rows (and
its UTF-16 tab-separated "Excel CSV" variant), Search Console's zip of CSVs
with days in descending order, and Meta's summary row with no campaign name.
"""

from __future__ import annotations

import calendar
import csv
import io
import zipfile
from datetime import date

from ..model import CHANNELS

GA4_HEADER_NEW = ["Session primary channel group (Default Channel Group)", "Sessions", "Engaged sessions",
                  "Engagement rate", "Average engagement time per session", "Events per session",
                  "Event count", "Key events", "Session key event rate", "Total revenue"]
GA4_HEADER_OLD = ["Session default channel group", "Sessions", "Engaged sessions", "Engagement rate",
                  "Average engagement time per session", "Event count", "Conversions", "Total revenue"]


def _month_bounds(period: str) -> tuple[date, date]:
    y, m = (int(x) for x in period.split("-"))
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


def _csv(rows: list[list], delimiter: str = ",") -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delimiter, lineterminator="\n")
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def ga4_traffic_acquisition(account: str, period: str, channels: dict[str, dict],
                            old_names: bool = False, include_total: bool = False,
                            compare_period: str | None = None,
                            compare_channels: dict[str, dict] | None = None) -> bytes:
    """channels: slug -> {sessions, conversions, revenue?}"""
    s, e = _month_bounds(period)
    lines = [
        "# ----------------------------------------",
        "# Traffic acquisition: Session primary channel group (Default Channel Group)",
        f"# Account: {account}",
        f"# Property: {account} - GA4",
        "# ----------------------------------------",
        "# ",
        "# All Users",
        f"# Start date: {s:%Y%m%d}",
        f"# End date: {e:%Y%m%d}",
    ]
    header = list(GA4_HEADER_OLD if old_names else GA4_HEADER_NEW)

    def row_for(slug, v):
        sess = int(v.get("sessions", 0))
        eng = int(round(sess * 0.71))
        conv = v.get("conversions", 0)
        rev = v.get("revenue", 0)
        name = CHANNELS[slug].label if slug != "total" else ""
        if old_names:
            return [name, sess, eng, round(eng / sess, 6) if sess else 0, 48.27, int(sess * 9.1),
                    _num(conv), _money(rev)]
        return [name, sess, eng, round(eng / sess, 6) if sess else 0, 48.27, 9.12, int(sess * 9.1),
                _num(conv), round(conv / sess, 6) if sess else 0, _money(rev)]

    rows: list[list] = []
    if compare_period:
        cs, ce = _month_bounds(compare_period)
        header = [header[0], "Date range"] + header[1:]
        labels = {period: f"{s:%b} {s.day}, {s.year} - {e:%b} {e.day}, {e.year}",
                  compare_period: f"{cs:%b} {cs.day}, {cs.year} - {ce:%b} {ce.day}, {ce.year}"}
        for per, chans in ((period, channels), (compare_period, compare_channels or {})):
            for slug, v in chans.items():
                r = row_for(slug, v)
                rows.append([r[0], labels[per]] + r[1:])
    else:
        rows = [row_for(slug, v) for slug, v in channels.items()]
        if include_total:
            tot = {"sessions": sum(v.get("sessions", 0) for v in channels.values()),
                   "conversions": sum(v.get("conversions", 0) for v in channels.values()),
                   "revenue": sum(v.get("revenue", 0) for v in channels.values())}
            rows.insert(0, row_for("total", tot))
    return ("\n".join(lines) + "\n" + _csv([header] + rows)).encode("utf-8")


def google_ads_campaigns(period: str, campaigns: list[dict], currency: str = "GBP",
                         excel_utf16: bool = False) -> bytes:
    """campaigns: [{name, type, clicks, impressions, cost, conversions, value?}]"""
    s, e = _month_bounds(period)
    rng = f"{s:%B} {s.day}, {s.year} - {e:%B} {e.day}, {e.year}"
    header = ["Campaign status", "Campaign", "Campaign type", "Clicks", "Impr.", "CTR",
              "Currency code", "Avg. CPC", "Cost", "Conversions", "Cost / conv.", "Conv. rate",
              "Conv. value"]
    rows = []
    for c in campaigns:
        clk, imp, cost, conv = c["clicks"], c["impressions"], c["cost"], c["conversions"]
        rows.append(["Enabled", c["name"], c.get("type", "Search"), f"{clk:,}", f"{imp:,}",
                     f"{clk / imp * 100:.2f}%" if imp else "--", currency,
                     f"{cost / clk:.2f}" if clk else "--", f"{cost:,.2f}", f"{conv:.2f}",
                     f"{cost / conv:.2f}" if conv else "--",
                     f"{conv / clk * 100:.2f}%" if clk else "--", f"{c.get('value', 0):,.2f}"])
    tc = sum(c["clicks"] for c in campaigns)
    ti = sum(c["impressions"] for c in campaigns)
    tcost = sum(c["cost"] for c in campaigns)
    tconv = sum(c["conversions"] for c in campaigns)
    total = ["Total: Account", "", "", f"{tc:,}", f"{ti:,}", f"{tc / ti * 100:.2f}%" if ti else "--",
             currency, f"{tcost / tc:.2f}" if tc else "--", f"{tcost:,.2f}", f"{tconv:.2f}",
             f"{tcost / tconv:.2f}" if tconv else "--", "--", "--"]
    body = [["Campaign report"], [rng], header] + rows + [total,
            ["Total: Campaigns", "", "", f"{tc:,}", f"{ti:,}", "", currency, "", f"{tcost:,.2f}",
             f"{tconv:.2f}", "", "", ""]]
    if excel_utf16:
        return _csv(body, delimiter="\t").encode("utf-16")
    return _csv(body).encode("utf-8")


def search_console_zip(period: str, clicks: int, impressions: int, position: float,
                       queries: list[tuple[str, int, int, float]], days_missing: int = 0) -> bytes:
    s, e = _month_bounds(period)
    n = e.day - days_missing
    # Spread the month's totals across days deterministically, exact sums preserved.
    weights = [1.0 + 0.25 * ((d * 7) % 5) / 4 - (0.15 if date(s.year, s.month, d).weekday() >= 5 else 0)
               for d in range(1, n + 1)]
    tw = sum(weights)
    day_clicks = _spread(clicks, weights, tw)
    day_impr = _spread(impressions, weights, tw)
    dates = [["Date", "Clicks", "Impressions", "CTR", "Position"]]
    for d in range(n, 0, -1):             # GSC lists newest first
        c, i = day_clicks[d - 1], day_impr[d - 1]
        dates.append([f"{s.year:04d}-{s.month:02d}-{d:02d}", c, i, f"{c / i * 100:.2f}%" if i else "0%",
                      f"{position:.2f}"])
    q = [["Top queries", "Clicks", "Impressions", "CTR", "Position"]]
    for text, c, i, p in queries:
        q.append([text, c, i, f"{c / i * 100:.2f}%" if i else "0%", f"{p:.1f}"])
    filters = [["Filter", "Value"], ["Search type", "Web"],
               ["Date", f"{s:%Y-%m-%d} - {e:%Y-%m-%d}"]]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Queries.csv", _csv(q))
        z.writestr("Pages.csv", _csv([["Top pages", "Clicks", "Impressions", "CTR", "Position"]]))
        z.writestr("Dates.csv", _csv(dates))
        z.writestr("Filters.csv", _csv(filters))
    return buf.getvalue()


def meta_ads_table(period: str, campaigns: list[dict], currency: str = "GBP") -> bytes:
    """campaigns: [{name, results, indicator?, impressions, spend, link_clicks, value?}]"""
    s, e = _month_bounds(period)
    header = ["Reporting starts", "Reporting ends", "Campaign name", "Campaign delivery", "Results",
              "Result indicator", "Reach", "Impressions", "Cost per results",
              f"Amount spent ({currency})", "Link clicks", f"CPC (cost per link click) ({currency})",
              "CTR (link click-through rate)", "Purchases conversion value", "Ends"]
    rows = []
    for c in campaigns:
        res = c["results"]
        rows.append([f"{s:%Y-%m-%d}", f"{e:%Y-%m-%d}", c["name"], "inactive", res,
                     c.get("indicator", "actions:offsite_conversion.fb_pixel_lead"),
                     int(c["impressions"] * 0.62), c["impressions"],
                     f"{c['spend'] / res:.2f}" if res else "", f"{c['spend']:.2f}", c["link_clicks"],
                     f"{c['spend'] / c['link_clicks']:.2f}" if c["link_clicks"] else "",
                     f"{c['link_clicks'] / c['impressions'] * 100:.4f}" if c["impressions"] else "",
                     f"{c.get('value', 0):.2f}" if c.get("value") else "", "Ongoing"])
    summary = [f"{s:%Y-%m-%d}", f"{e:%Y-%m-%d}", "", "", "", "", "",
               sum(c["impressions"] for c in campaigns), "",
               f"{sum(c['spend'] for c in campaigns):.2f}", sum(c["link_clicks"] for c in campaigns),
               "", "", "", ""]
    return _csv([header, summary] + rows).encode("utf-8")


def _spread(total: int, weights: list[float], tw: float) -> list[int]:
    raw = [total * w / tw for w in weights]
    out = [int(x) for x in raw]
    rem = total - sum(out)
    for i in sorted(range(len(raw)), key=lambda i: -(raw[i] - out[i]))[:rem]:
        out[i] += 1
    return out


def _num(v) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


def _money(v) -> str:
    return "0" if not v else f"{v:.2f}"
