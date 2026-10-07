"""The web app over HTTP, as an agency team member uses it."""

import re

import pytest
from fastapi.testclient import TestClient

from agency_report_agent.demo import agency as demo
from agency_report_agent.demo import exports
from agency_report_agent.web.app import create_app

P = demo.PERIOD


def _csrf(html: str) -> str:
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert m, "no csrf token on page"
    return m.group(1)


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORT_DESK_PASSWORD", "correct horse")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    a = create_app(str(tmp_path / "ws"))
    yield a
    a.state.desk.close()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def login(c, name="Priya Raman", password="correct horse"):
    tok = _csrf(c.get("/login").text)
    return c.post("/login", data={"name": name, "password": password, "csrf_token": tok, "next": "/"},
                  follow_redirects=False)


@pytest.fixture
def signed_in(client):
    r = login(client)
    assert r.status_code == 303
    return client


def token(c, url="/settings"):
    return _csrf(c.get(url).text)


def seed(app):
    demo.seed(app.state.desk.store)


# --------------------------------------------------------------------------- #
# Auth and security
# --------------------------------------------------------------------------- #
def test_pages_need_sign_in(client):
    for url in ("/", f"/month/{P}", "/clients", "/settings", "/activity", f"/clients/x/{P}"):
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"].startswith("/login"), url


def test_wrong_password_and_lockout(client):
    for _ in range(8):
        assert login(client, password="nope").status_code == 401
    assert login(client).status_code == 429


def test_csrf_required_on_posts(signed_in):
    r = signed_in.post("/clients", data={"name": "Sneaky Ltd", "csrf_token": "forged"})
    assert r.status_code == 403
    assert "Sneaky" not in signed_in.get("/clients").text


def test_security_headers(signed_in):
    r = signed_in.get("/clients")
    assert "frame-ancestors 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"


def test_open_redirect_blocked(client):
    tok = _csrf(client.get("/login").text)
    r = client.post("/login", data={"name": "A", "password": "correct horse", "csrf_token": tok,
                                    "next": "//evil.example/"}, follow_redirects=False)
    assert r.headers["location"] == "/"


def test_logout(signed_in):
    tok = token(signed_in)
    signed_in.post("/logout", data={"csrf_token": tok})
    assert signed_in.get("/clients", follow_redirects=False).status_code == 303


def test_html_is_escaped(signed_in):
    tok = token(signed_in)
    signed_in.post("/clients", data={"name": "<script>alert(1)</script>", "csrf_token": tok})
    html = signed_in.get("/clients").text
    assert "<script>alert(1)" not in html and "&lt;script&gt;" in html


def test_path_traversal_404(signed_in):
    assert signed_in.get(f"/clients/..%2F..%2Fetc/{P}").status_code == 404
    assert signed_in.get("/clients/brightwave-dental/2026-13").status_code == 404
    assert signed_in.get("/reports/brightwave-dental/2026-09/v1.exe").status_code == 404


# --------------------------------------------------------------------------- #
# A new agency from scratch: settings, client, uploads, draft, review, approve
# --------------------------------------------------------------------------- #
def test_new_agency_full_month(signed_in, app):
    c = signed_in
    assert "Load the demo agency" in c.get("/").text                      # empty workspace onboarding
    tok = token(c)
    r = c.post("/settings", data={"csrf_token": tok, "name": "Harbour Lane Marketing", "brand_color": "#7A1F5C",
                                  "voice": "Friendly and plain.", "reviewers": "Sam Patel\nPriya Raman",
                                  "currency": "GBP", "drafting": "template", "model": "claude-opus-5-5"},
               files={"logo": ("logo.png", b"\x89PNG\r\n\x1a\n" + b"0" * 100, "image/png")})
    assert r.status_code == 200 and "Settings saved" in r.text, (r.url, r.text[-800:])
    r = c.post("/clients", data={"csrf_token": tok, "name": "Seaview Physio", "sector": "Physiotherapy",
                                 "conversion_label": "bookings", "monthly_target": "90", "context": ""})
    assert "Seaview Physio" in r.text and "Upload" in r.text
    url = f"/clients/seaview-physio/{P}"
    ch = {"organic_search": {"sessions": 2100, "conversions": 41}, "paid_search": {"sessions": 1500, "conversions": 52},
          "direct": {"sessions": 600, "conversions": 9}}
    ga4 = exports.ga4_traffic_acquisition("Seaview", P, ch)
    r = c.post(f"{url}/upload", data={"csrf_token": tok, "source_type": "ga4"},
               files={"file": ("traffic.csv", ga4, "text/csv")})
    assert "Imported GA4" in r.text
    ads = exports.google_ads_campaigns(P, [{"name": "Physio Near Me", "clicks": 1400, "impressions": 30000,
                                            "cost": 1890.55, "conversions": 50}])
    r = c.post(f"{url}/upload", data={"csrf_token": tok, "source_type": "google_ads"},
               files={"file": ("Campaign report.csv", ads, "text/csv")})
    assert "Imported Google Ads" in r.text and "1,890.55" in r.text
    # draft (runs in the background), then wait
    c.post(f"{url}/draft", data={"csrf_token": tok})
    app.state.desk.wait()
    page = c.get(url).text
    assert "Review the draft" in page and "All" in page
    review = c.get(f"{url}/review").text
    assert 'class="claim ok"' in review and "Paid Search" in review and "first month" in review.lower()
    # approve
    r = c.post(f"{url}/review", data={"csrf_token": _csrf(review), "action": "approve", "reviewer": "Sam Patel"})
    assert "Approved. Version 1" in r.text
    pdf = c.get(f"/reports/seaview-physio/{P}/v1.pdf")
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"
    assert 'filename="Seaview-Physio-2026-09-report-v1.pdf"' in pdf.headers["content-disposition"]
    html = c.get(f"/reports/seaview-physio/{P}/v1.html").text
    assert "Harbour Lane Marketing" in html and "Seaview Physio" in html and "data:image/png;base64" in html
    assert "#7A1F5C" in html and "Sam Patel" in html
    act = c.get("/activity").text
    for what in ("uploaded GA4", "uploaded Google Ads", "started report", "approved", "added client"):
        assert what in act


def test_upload_errors_are_explained(signed_in, app):
    seed(app)
    c, tok = signed_in, token(signed_in)
    url = f"/clients/kestrel-accounting/{P}"
    r = c.post(f"{url}/upload", data={"csrf_token": tok, "source_type": "ga4"},
               files={"file": ("x.xlsx", b"PK\x03\x04" + b"\0" * 50, "application/octet-stream")})
    assert "Excel or zip" in r.text
    aug = exports.ga4_traffic_acquisition("K", "2026-08", {"organic_search": {"sessions": 10, "conversions": 1}})
    r = c.post(f"{url}/upload", data={"csrf_token": tok, "source_type": "ga4"},
               files={"file": ("aug.csv", aug, "text/csv")})
    assert "covers August 2026, not September 2026" in r.text
    r = c.post(f"{url}/upload", data={"csrf_token": tok, "source_type": "bogus"},
               files={"file": ("a.csv", b"a,b\n1,2\n", "text/csv")})
    assert "Choose which platform" in r.text


def test_manual_entry_overrides(signed_in, app):
    seed(app)
    c, tok = signed_in, token(signed_in)
    url = f"/clients/tidewater-yoga/{P}"
    r = c.post(f"{url}/manual", data={"csrf_token": tok, "v__email__sessions": "120", "v__email__conversions": "3"})
    assert "Saved" in r.text
    pd, _ = app.state.desk.store.period_data("tidewater-yoga", P)
    assert pd.get("email", "sessions") == 120
    r = c.post(f"{url}/manual", data={"csrf_token": tok, "v__email__sessions": "lots"})
    assert "a number (Email Sessions)" in r.text.replace('&#39;', "'")


# --------------------------------------------------------------------------- #
# The demo agency's month: draft everything, review, edit, notes, reject
# --------------------------------------------------------------------------- #
def test_demo_month_dashboard_and_review_actions(signed_in, app):
    c = signed_in
    tok = token(c)
    r = c.post("/setup/demo", data={"csrf_token": tok})
    assert "Draft 12 reports" in r.text
    r = c.post(f"/month/{P}/draft-all", data={"csrf_token": tok})
    app.state.desk.wait()
    month = c.get(f"/month/{P}").text
    assert month.count(">Review</a>") == 12 and "figures backed by data" in month
    # edit with a wrong figure: highlighted and blocks approval
    url = f"/clients/harbourside-law/{P}"
    review = c.get(f"{url}/review").text
    draft = re.search(r'<textarea name="text"[^>]*>(.*?)</textarea>', review, re.S).group(1)
    import html as h
    draft = h.unescape(draft)
    bad = draft.replace("## Summary\n\n", "## Summary\n\nOrganic search delivered 999 enquiries. ", 1)
    r = c.post(f"{url}/review", data={"csrf_token": tok, "action": "edit", "text": bad})
    assert 'class="claim bad"' in r.text and "couldn't back" in r.text
    r = c.post(f"{url}/review", data={"csrf_token": tok, "action": "approve", "reviewer": "Priya Raman"})
    assert "Fix them, or confirm" in r.text
    r = c.post(f"{url}/review", data={"csrf_token": tok, "action": "approve", "reviewer": "Priya Raman",
                                      "confirm_flagged": "1"})
    assert "Approved" in r.text
    assert "confirmed flagged figure" in c.get("/activity").text
    # notes and explanations redraft (background)
    url = f"/clients/oakfield-veterinary/{P}"
    review = c.get(f"{url}/review").text
    aid = re.search(r'name="expl_(A\d+)"', review).group(1)
    c.post(f"{url}/review", data={"csrf_token": tok, "action": "update_notes",
                                  f"expl_{aid}": "Meta campaign paused for new creative.",
                                  "next_steps": "Relaunch Meta with the new creative on 6 October."})
    app.state.desk.wait()
    review = c.get(f"{url}/review").text
    assert "Meta campaign paused for new creative." in review and "Relaunch Meta" in review
    # template writer: free-text change requests are refused with a reason
    r = c.post(f"{url}/review", data={"csrf_token": tok, "action": "request_changes", "change_request": "Shorter"})
    assert "template writer can" in r.text
    # reject
    r = c.post(f"/clients/tidewater-yoga/{P}/review", data={"csrf_token": tok, "action": "reject",
                                                           "reviewer": "Tom Ellison", "reason": "Studio closed"})
    assert "Not sending" in r.text
    # preview renders the draft in client form
    prev = c.get(f"/clients/brightwave-dental/{P}/preview").text
    assert "Draft — not yet approved." in prev and "[F" not in prev


def test_client_settings_and_archive(signed_in, app):
    seed(app)
    c, tok = signed_in, token(signed_in)
    r = c.post("/clients/kestrel-accounting/settings", data={"csrf_token": tok, "name": "Kestrel Accountants",
                                                            "sector": "Accountancy", "conversion_label": "leads",
                                                            "monthly_target": "abc", "context": ""})
    assert "must be a number" in r.text
    c.post("/clients/kestrel-accounting/settings", data={"csrf_token": tok, "name": "Kestrel Accountants",
                                                        "sector": "Accountancy", "conversion_label": "leads",
                                                        "monthly_target": "100", "context": "", "archived": "1"})
    month = c.get(f"/month/{P}").text
    assert "Kestrel" not in month
    assert "archived" in c.get("/clients").text


def test_settings_validation(signed_in):
    tok = token(signed_in)
    r = signed_in.post("/settings", data={"csrf_token": tok, "name": "A", "brand_color": "red", "drafting": "template"})
    assert "Brand colour must look like" in r.text
    r = signed_in.post("/settings", data={"csrf_token": tok, "name": "A", "brand_color": "#112233"},
                       files={"logo": ("x.svg", b'<svg onload="alert(1)"/>', "image/svg+xml")})
    assert "scripts" in r.text


def test_review_markup_is_well_formed(signed_in, app):
    seed(app)
    desk = app.state.desk
    desk.start("oakfield-veterinary", P)
    html = signed_in.get(f"/clients/oakfield-veterinary/{P}/review").text
    view = html.split('class="card-body draft-view">', 1)[1].split("</div>", 1)[0]
    assert 'data-fact="' in view and '" data-fact=' not in view.replace('" data-fact="F', "")
    assert "data-fact=&#34;" not in view and '&#34;' not in view
    assert view.count("<mark") == view.count("</mark>") > 20
    assert re.search(r'<mark class="claim ok" title="[^"<>]+" data-fact="F\d+">', view)
