"""A whole agency month over HTTP, checked figure by figure against independent truth.

Twelve clients are created through the web forms, every export for every
month is uploaded through the upload form in its real download format, all
September reports are drafted, reviewed and approved, and every number in
every approved report's channel table and headline tiles is compared with
the ground truth the demo encodes (computed without the importers).
"""

import html as h
import re
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from agency_report_agent.demo import agency as demo
from agency_report_agent.model import channel_label
from agency_report_agent.web.app import create_app

P = demo.PERIOD
SOURCE_FILES = {"ga4": "traffic_acquisition.csv", "google_ads": "Campaign report.csv",
                "search_console": "Performance-on-Search.zip", "meta_ads": "Meta-Ads-Campaigns.csv"}


def _csrf(text):
    return re.search(r'name="csrf_token" value="([^"]+)"', text).group(1)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    import os
    os.environ["REPORT_DESK_PASSWORD"] = "agency-pass"
    os.environ.pop("ANTHROPIC_API_KEY", None)
    app = create_app(str(tmp_path_factory.mktemp("agency")))
    with TestClient(app) as c:
        tok = _csrf(c.get("/login").text)
        c.post("/login", data={"name": "Priya Raman", "password": "agency-pass", "csrf_token": tok})
        tok = _csrf(c.get("/settings").text)
        c.post("/settings", data={"csrf_token": tok, "name": "Northstar Digital", "brand_color": "#1B4D3E",
                                  "voice": demo.AGENCY["voice"], "reviewers": "\n".join(demo.AGENCY["reviewers"]),
                                  "currency": "GBP", "drafting": "template", "model": "claude-opus-5-5"})
        ids = {}
        for cl in demo.CLIENTS:
            r = c.post("/clients", data={"csrf_token": tok, "name": cl["name"], "sector": cl["sector"],
                                         "conversion_label": cl["label"], "monthly_target": str(cl["target"]),
                                         "context": cl["context"]})
            ids[cl["id"]] = re.search(r"/clients/([a-z0-9-]+)/settings", r.text).group(1)
        uploads = 0
        for cl in demo.CLIENTS:
            for period in demo.periods_for(cl):
                for source, data in demo.build_exports(cl, period).items():
                    r = c.post(f"/clients/{ids[cl['id']]}/{period}/upload",
                               data={"csrf_token": tok, "source_type": source},
                               files={"file": (SOURCE_FILES[source], data, "application/octet-stream")})
                    assert "Imported" in r.text, (cl["id"], period, source, r.text[:2000])
                    uploads += 1
        r = c.post(f"/month/{P}/draft-all", data={"csrf_token": tok})
        app.state.desk.wait()
        month = c.get(f"/month/{P}").text
        approved = {}
        for cl in demo.CLIENTS:
            cid = ids[cl["id"]]
            review = c.get(f"/clients/{cid}/{P}/review").text
            reviewer = demo.AGENCY["reviewers"][len(approved) % 3]
            r = c.post(f"/clients/{cid}/{P}/review", data={"csrf_token": tok, "action": "approve",
                                                           "reviewer": reviewer})
            assert "Approved. Version 1" in r.text, (cl["id"], r.text[:3000])
            approved[cl["id"]] = {
                "review": review,
                "html": c.get(f"/reports/{cid}/{P}/v1.html").text,
                "pdf": c.get(f"/reports/{cid}/{P}/v1.pdf").content,
                "reviewer": reviewer,
            }
        activity = c.get("/activity").text
        yield {"app": app, "ids": ids, "uploads": uploads, "month": month, "approved": approved,
               "activity": activity, "final_month": c.get(f"/month/{P}").text}
    app.state.desk.close()


def _expected(cl):
    tr = demo.truth(cl, P)
    rows = {}
    for scope, row in tr.items():
        rows[scope] = {"sessions": row.get("sessions"), "conversions": row.get("conversions"),
                       "spend": row.get("spend"), "revenue": row.get("revenue")}
    total = {m: sum((r[m] or 0) for r in rows.values()) for m in ("sessions", "conversions", "spend", "revenue")}
    return rows, total


def _money(v):
    return f"£{v:,.2f}" if v < 100 else f"£{v:,.0f}"


def _table(report_html):
    body = report_html.split('<table class="channels">', 1)[1].split("</table>", 1)[0]
    head = [h.unescape(re.sub("<[^>]+>", "", x)).strip()
            for x in re.findall(r"<th scope=\"col\"[^>]*>(.*?)</th>", body)]
    out = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body.split("<tbody>", 1)[1], re.S):
        name = h.unescape(re.search(r'<th scope="row">(.*?)</th>', tr).group(1))
        cells = [h.unescape(re.sub("<[^>]+>", "", c.split("<br>")[0])).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        out[name] = dict(zip(head[1:], cells))
    return out


def test_every_upload_was_accepted(run):
    expected = sum(len(demo.build_exports(cl, p)) for cl in demo.CLIENTS for p in demo.periods_for(cl))
    assert run["uploads"] == expected > 100
    assert "Draft 12 reports" not in run["month"] and run["month"].count(">Review</a>") == 12


@pytest.mark.parametrize("cid", [c["id"] for c in demo.CLIENTS])
def test_report_table_matches_truth(run, cid):
    cl = demo.client_def(cid)
    rows, total = _expected(cl)
    table = _table(run["approved"][cid]["html"])
    label = cl["label"].capitalize()
    for scope, exp in list(rows.items()) + [("total", total)]:
        name = "All channels" if scope == "total" else channel_label(scope)
        got = table[name]
        assert got["Sessions"] == f"{exp['sessions']:,.0f}", (cid, name)
        assert got[label] == f"{exp['conversions']:,.0f}", (cid, name)
        if "Spend" in got:
            want = _money(exp["spend"]) if exp.get("spend") else "—"
            assert got["Spend"] == want, (cid, name, got["Spend"], exp.get("spend"))
        if "Revenue" in got:
            want = _money(exp["revenue"]) if exp.get("revenue") else "—"
            assert got["Revenue"] == want, (cid, name)
    # channels in the table but not in the truth were switched off: they must show zero
    for name, got in table.items():
        if name != "All channels" and name not in {channel_label(s) for s in rows}:
            assert got["Sessions"] == "0" and got[label] == "0", (cid, name)


@pytest.mark.parametrize("cid", [c["id"] for c in demo.CLIENTS])
def test_report_headline_and_branding(run, cid):
    cl = demo.client_def(cid)
    rows, total = _expected(cl)
    page = run["approved"][cid]["html"]
    tile = re.search(r'<div class="tile-label">' + re.escape(cl["label"].capitalize()) +
                     r'</div><div class="tile-value">([^<]+)</div>', page)
    assert tile and tile.group(1) == f"{total['conversions']:,.0f}"
    assert "Northstar Digital" in page and "#1B4D3E" in page and cl["name"] in h.unescape(page)
    assert f"Reviewed and approved by {run['approved'][cid]['reviewer']}" in page
    assert "[F" not in page and "Every figure in this report was checked" in page
    target = re.search(r"Monthly target: ([\d,]+)", page)
    assert target and target.group(1) == f"{cl['target']:,}"


@pytest.mark.parametrize("cid", [c["id"] for c in demo.CLIENTS])
def test_every_narrative_figure_was_checked(run, cid):
    review = run["approved"][cid]["review"].split('class="card-body draft-view">', 1)[1].split("</div>", 1)[0]
    assert 'class="claim bad"' not in review and "claim unchecked" not in review
    assert review.count('class="claim ok"') >= 15


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="pdftotext not installed")
@pytest.mark.parametrize("cid", [c["id"] for c in demo.CLIENTS])
def test_pdf_contains_the_report(run, cid, tmp_path):
    cl = demo.client_def(cid)
    _, total = _expected(cl)
    pdf = run["approved"][cid]["pdf"]
    assert pdf[:5] == b"%PDF-"
    f = tmp_path / "r.pdf"
    f.write_bytes(pdf)
    text = subprocess.run(["pdftotext", "-layout", str(f), "-"], capture_output=True, text=True).stdout
    assert cl["name"] in text and "September 2026" in text
    assert f"{total['conversions']:,.0f}" in text and "Reviewed and approved by" in text


def test_audit_trail_and_dashboard(run):
    act = run["activity"]
    assert act.count("approved") >= 12 and "uploaded GA4" in act and "started report" in act
    assert run["final_month"].count("Approved") >= 12
