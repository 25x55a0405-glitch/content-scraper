"""Variants real agencies produce that once imported wrong figures silently."""

import pytest

from agency_report_agent.importers import ImportError_, import_file

GA4_HEAD = "# Start date: 20260901\n# End date: 20260930\n"


def test_european_numbers_semicolon_ga4():
    data = (GA4_HEAD + "Session primary channel group (Default Channel Group);Sessions;Key events;Total revenue\n"
            "Organic Search;2.900;82;1.234,56\n").encode()
    r = import_file("ga4", data, "2026-09").periods["2026-09"]["organic_search"]
    assert r == {"sessions": 2900, "conversions": 82, "revenue": 1234.56}


def test_uk_numbers_unaffected():
    data = (GA4_HEAD + 'Session primary channel group (Default Channel Group),Sessions,Key events,Total revenue\n'
            'Organic Search,"2,900",82,"1,234.56"\n').encode()
    r = import_file("ga4", data, "2026-09").periods["2026-09"]["organic_search"]
    assert r == {"sessions": 2900, "conversions": 82, "revenue": 1234.56}


def test_ga4_second_dimension_rows_add_up():
    data = (GA4_HEAD + "Session primary channel group (Default Channel Group),Device category,Sessions,Key events\n"
            "Organic Search,desktop,1500,40\nOrganic Search,mobile,1300,38\nOrganic Search,tablet,100,4\n").encode()
    res = import_file("ga4", data, "2026-09")
    assert res.periods["2026-09"]["organic_search"] == {"sessions": 2900, "conversions": 82}
    assert any("more than one row" in w for w in res.warnings)


def test_generic_repeated_rows_add_up():
    res = import_file("generic", b"channel,spend,conversions\nPaid Social,600,40\nPaid Social,300,20\n", "2026-09")
    assert res.periods["2026-09"]["paid_social"] == {"spend": 900, "conversions": 60}


def test_two_month_files_are_refused():
    ads = b'Campaign report\n"August 1, 2026 - September 30, 2026"\nCampaign,Clicks,Impr.,Cost\nBrand,10,100,5.00\n'
    with pytest.raises(ImportError_, match="more than one calendar month"):
        import_file("google_ads", ads, "2026-09")
    meta = (b"Reporting starts,Reporting ends,Campaign name,Amount spent (GBP),Impressions\n"
            b"2026-08-15,2026-09-14,A,500,1000\n")
    with pytest.raises(ImportError_, match="more than one calendar month"):
        import_file("meta_ads", meta, "2026-09")


def test_us_dates_search_console_dates_csv():
    rows = ["Date,Clicks,Impressions,CTR,Position"] + \
        [f"9/{d}/2026,10,300,3.33%,8.0" for d in range(1, 31)]
    res = import_file("search_console", "\n".join(rows).encode(), "2026-09")
    assert set(res.periods) == {"2026-09"} and res.periods["2026-09"]["organic_search"]["clicks"] == 300
    assert not res.warnings


def test_search_console_comparison_export_refused_clearly():
    data = b"Date,Last 28 days Clicks,Previous period Clicks,Last 28 days Impressions\n2026-09-01,1,1,10\n"
    with pytest.raises(ImportError_, match="compares two date ranges"):
        import_file("search_console", data, "2026-09")


def test_ga4_resaved_by_excel_with_trailing_commas():
    data = ("# Start date: 20260901,,\n# End date: 20260930,,\n"
            "Session primary channel group (Default Channel Group),Sessions,Key events\nOrganic Search,100,5\n").encode()
    assert import_file("ga4", data, "2026-09").periods["2026-09"]["organic_search"]["sessions"] == 100


def test_performance_max_spend_goes_where_ga4_puts_its_conversions():
    ads = (b'Campaign report\n"September 1, 2026 - September 30, 2026"\n'
           b"Campaign,Campaign type,Clicks,Impr.,Cost\nBrand,Search,100,1000,\"2,000.00\"\nPMax,Performance Max,90,6000,\"1,200.00\"\n")
    p = import_file("google_ads", ads, "2026-09").periods["2026-09"]
    assert p["paid_search"]["spend"] == 2000 and p["cross_network"]["spend"] == 1200


def test_roas_column_is_not_read_as_revenue():
    ads = (b'Campaign report\n"September 1, 2026 - September 30, 2026"\n'
           b"Campaign,Clicks,Impr.,Cost,Conv. value / cost\nBrand,100,1000,500,4.25\n")
    assert "revenue" not in import_file("google_ads", ads, "2026-09").periods["2026-09"]["paid_search"]


def test_meta_messaging_results_are_not_leads():
    meta = (b"Reporting starts,Reporting ends,Campaign name,Results,Result indicator,Amount spent (GBP)\n"
            b"2026-09-01,2026-09-30,A,440,actions:onsite_conversion.messaging_conversation_started_7d,300\n"
            b"2026-09-01,2026-09-30,B,60,actions:offsite_conversion.fb_pixel_lead,600\n")
    assert import_file("meta_ads", meta, "2026-09").periods["2026-09"]["paid_social"]["conversions"] == 60
