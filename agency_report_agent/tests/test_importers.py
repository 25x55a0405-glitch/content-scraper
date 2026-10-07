"""Importers and the workspace store, against format-accurate exports."""

import pytest

from agency_report_agent.demo import agency as demo
from agency_report_agent.demo import exports
from agency_report_agent.importers import ImportError_, import_file
from agency_report_agent.importers.common import parse_date, parse_number
from agency_report_agent.model import PeriodData, compute_derived
from agency_report_agent.store import Store, StoreError

ALL_MONTHS = [(c["id"], p) for c in demo.CLIENTS for p in demo.periods_for(c)]


# --------------------------------------------------------------------------- #
# Every export for every client and month imports to exactly the encoded truth
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("client_id,period", ALL_MONTHS)
def test_every_export_imports_to_truth(client_id, period):
    c = demo.client_def(client_id)
    files, truth = demo.month(c, period)
    got: dict[str, dict[str, float]] = {}
    for source, data in files.items():
        res = import_file(source, data, period)
        assert period in res.periods, f"{source} produced no figures for {period}"
        for scope, row in res.periods[period].items():
            for m, v in row.items():
                # mimic precedence: GA4 owns sessions/conversions/revenue
                if source != "ga4" and m in ("conversions", "revenue"):
                    continue
                got.setdefault(scope, {})[m] = v
    for scope, row in truth.items():
        for m, v in row.items():
            assert scope in got and m in got[scope], f"missing {scope}.{m}"
            tol = 0.011 if m in ("spend", "revenue", "avg_position") else 0
            assert abs(got[scope][m] - v) <= tol, f"{scope}.{m}: got {got[scope][m]}, truth {v}"


def test_ga4_comparison_export_yields_both_months():
    c = demo.client_def("lumen-skin-clinic")
    data = demo.build_exports(c, demo.PERIOD)["ga4"]
    res = import_file("ga4", data)
    assert set(res.periods) == {"2026-09", "2026-08"}
    aug = demo.truth(c, "2026-08")
    assert res.periods["2026-08"]["paid_search"]["sessions"] == aug["paid_search"]["sessions"]


def test_ga4_old_conversions_header():
    c = demo.client_def("fernhill-care-homes")
    res = import_file("ga4", demo.build_exports(c, demo.PERIOD)["ga4"])
    assert res.periods[demo.PERIOD]["organic_search"]["conversions"] == \
        demo.truth(c, demo.PERIOD)["organic_search"]["conversions"]


def test_google_ads_utf16_excel_csv():
    c = demo.client_def("fernhill-care-homes")
    data = demo.build_exports(c, demo.PERIOD)["google_ads"]
    assert data[:2] in (b"\xff\xfe", b"\xfe\xff")
    res = import_file("google_ads", data)
    assert res.detected_period == demo.PERIOD
    assert res.periods[demo.PERIOD]["paid_search"]["spend"] == pytest.approx(
        demo.truth(c, demo.PERIOD)["paid_search"]["spend"], abs=0.01)


def test_ga4_total_row_is_used_as_total():
    c = demo.client_def("northgate-motors")
    res = import_file("ga4", demo.build_exports(c, demo.PERIOD)["ga4"])
    tr = demo.truth(c, demo.PERIOD)
    assert res.periods[demo.PERIOD]["total"]["sessions"] == sum(r["sessions"] for r in tr.values())


def test_meta_reach_campaign_results_not_counted_as_conversions():
    c = demo.client_def("brightwave-dental")
    res = import_file("meta_ads", demo.build_exports(c, demo.PERIOD)["meta_ads"])
    assert res.periods[demo.PERIOD]["paid_social"]["conversions"] < 1000
    assert any("reach or clicks" in w for w in res.warnings)


def test_search_console_incomplete_month_warns():
    data = exports.search_console_zip("2026-09", 1000, 30000, 8.0, [], days_missing=3)
    res = import_file("search_console", data)
    assert any("27 of 30 days" in w for w in res.warnings)


def test_search_console_queries_only_is_rejected_with_guidance():
    with pytest.raises(ImportError_, match="Dates.csv"):
        import_file("search_console", b"Top queries,Clicks,Impressions,CTR,Position\nfoo,1,2,50%,3\n")


# --------------------------------------------------------------------------- #
# Bad input is rejected with an explanation, never silently mis-read
# --------------------------------------------------------------------------- #
def test_wrong_file_for_ga4_explains():
    with pytest.raises(ImportError_, match="Traffic acquisition"):
        import_file("ga4", b"Campaign,Clicks\nfoo,1\n", "2026-09")


def test_excel_file_rejected():
    with pytest.raises(ImportError_, match="Excel or zip"):
        import_file("ga4", b"PK\x03\x04" + b"\x00" * 100, "2026-09")


def test_multi_month_ga4_export_rejected():
    data = (b"# Start date: 20260801\n# End date: 20260930\n"
            b"Session primary channel group (Default Channel Group),Sessions,Key events\n"
            b"Organic Search,100,5\n")
    res_err = None
    try:
        res = import_file("ga4", data)
        res_err = res
    except ImportError_ as e:
        assert "more than one calendar month" in str(e) or "which month" in str(e)
        return
    assert any("more than one calendar month" in w for w in res_err.warnings)


def test_ga4_without_dates_uses_selected_period():
    data = b"Session primary channel group (Default Channel Group),Sessions,Key events\nOrganic Search,100,5\n"
    res = import_file("ga4", data, "2026-09")
    assert res.periods["2026-09"]["organic_search"] == {"sessions": 100, "conversions": 5}


def test_ga4_without_dates_and_no_period_explains():
    data = b"Session primary channel group (Default Channel Group),Sessions,Key events\nOrganic Search,100,5\n"
    with pytest.raises(ImportError_, match="which month"):
        import_file("ga4", data)


def test_empty_file():
    with pytest.raises(ImportError_, match="empty"):
        import_file("generic", b"", "2026-09")


def test_generic_wide_and_long():
    wide = b"channel,sessions,conversions,spend\nOrganic Search,1000,20,\nEmail,300,9,\n"
    r = import_file("generic", wide, "2026-09")
    assert r.periods["2026-09"]["email"] == {"sessions": 300, "conversions": 9}
    long = b"period,channel,metric,value\n2026-09,Paid Social,spend,\"1,250.50\"\n2026-08,Paid Social,spend,900\n"
    r = import_file("generic", long)
    assert r.periods["2026-09"]["paid_social"]["spend"] == 1250.5
    assert r.periods["2026-08"]["paid_social"]["spend"] == 900


def test_generic_bad_period():
    with pytest.raises(ImportError_, match="YYYY-MM"):
        import_file("generic", b"period,channel,sessions\nSept 2026,Email,3\n")


def test_generic_unknown_channel_warns_not_crashes():
    r = import_file("generic", b"channel,sessions\nEmail,10\nCarrier pigeon,4\n", "2026-09")
    assert "Carrier pigeon" in r.warnings[0]


@pytest.mark.parametrize("raw,want", [
    ("£1,234.56", 1234.56), ("$12", 12), ("57.32%", 57.32), ("--", None), ("", None),
    ("(45.10)", -45.10), ("1 234", 1234), ("GBP 99.50", 99.5), ("< 10", None), ("abc", None),
])
def test_parse_number(raw, want):
    assert parse_number(raw) == want


@pytest.mark.parametrize("raw,want", [
    ("20260901", (2026, 9, 1)), ("2026-09-30", (2026, 9, 30)), ("30/09/2026", (2026, 9, 30)),
    ("September 1, 2026", (2026, 9, 1)), ("Sep 1, 2026", (2026, 9, 1)), ("1 Sept 2026", (2026, 9, 1)),
])
def test_parse_date(raw, want):
    d = parse_date(raw)
    assert (d.year, d.month, d.day) == want


# --------------------------------------------------------------------------- #
# Store: precedence, conflicts, derived metrics, safety
# --------------------------------------------------------------------------- #
@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "ws")


def test_seeded_store_resolves_to_truth(store):
    demo.seed(store, periods=[demo.PERIOD])
    for c in demo.CLIENTS:
        pd, notes = store.period_data(c["id"], demo.PERIOD)
        tr = demo.truth(c, demo.PERIOD)
        for scope, row in tr.items():
            for m, v in row.items():
                assert pd.get(scope, m) == pytest.approx(v, abs=0.011), f"{c['id']} {scope}.{m}"


def test_precedence_conflict_is_reported(store):
    demo.seed(store, periods=[demo.PERIOD])
    pd, notes = store.period_data("harbourside-law", demo.PERIOD)
    # Ads over-reports conversions by 35% vs GA4 for this client
    assert any("Paid Search conversions" in n and "Using GA4" in n for n in notes)
    tr = demo.truth(demo.client_def("harbourside-law"), demo.PERIOD)
    assert pd.get("paid_search", "conversions") == tr["paid_search"]["conversions"]


def test_derived_metrics(store):
    demo.seed(store, periods=[demo.PERIOD])
    pd, _ = store.period_data("copperleaf-coffee", demo.PERIOD)
    ps = pd.values["paid_search"]
    assert ps["cpa"] == pytest.approx(ps["spend"] / ps["conversions"])
    assert ps["ctr"] == pytest.approx(ps["clicks"] / ps["impressions"] * 100)
    assert pd.values["total"]["revenue"] == pytest.approx(
        sum(r.get("revenue", 0) for s, r in pd.values.items() if s != "total"))


def test_totals_never_mix_clicks_across_channels(store):
    demo.seed(store, periods=[demo.PERIOD])
    pd, _ = store.period_data("brightwave-dental", demo.PERIOD)
    assert "clicks" not in pd.values["total"]
    assert pd.values["total"]["spend"] == pytest.approx(
        pd.get("paid_search", "spend") + pd.get("paid_social", "spend"))


def test_reupload_replaces_same_source(store):
    demo.seed(store, periods=[demo.PERIOD])
    c = demo.client_def("summit-fitness")
    data = demo.build_exports(c, demo.PERIOD)["google_ads"]
    store.add_source("summit-fitness", import_file("google_ads", data), demo.PERIOD, raw=data)
    assert sum(1 for s in store.sources("summit-fitness", demo.PERIOD) if s["type"] == "google_ads") == 1


def test_path_traversal_blocked(store):
    for bad in ("../etc", "a/b", "..", "A B", ""):
        with pytest.raises(StoreError):
            store.client(bad)
    with pytest.raises(StoreError):
        store.sources("x", "2026-13")


def test_client_names_unique_ids(store):
    a = store.create_client("Acme & Co")
    b = store.create_client("Acme & Co")
    assert a["id"] == "acme-co" and b["id"] == "acme-co-2"


def test_svg_logo_with_script_rejected(store):
    with pytest.raises(StoreError, match="scripts"):
        store.save_logo(b'<svg onload="alert(1)"></svg>', "image/svg+xml")


def test_compute_derived_handles_zeros():
    pd = PeriodData("2026-09", {"paid_search": {"sessions": 0, "conversions": 0, "spend": 0, "clicks": 0,
                                                "impressions": 0}})
    compute_derived(pd)
    assert set(pd.values["paid_search"]) == {"sessions", "conversions", "spend", "clicks", "impressions"}
