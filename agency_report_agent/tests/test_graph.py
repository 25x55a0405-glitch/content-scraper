"""The agent graph and the desk, through every path a real month takes."""

import re
import threading

import pytest

from agency_report_agent import graph as g
from agency_report_agent.demo import agency as demo
from agency_report_agent.desk import Desk, DeskError
from agency_report_agent.drafting import DraftRequest, template_draft
from agency_report_agent.verify import verify

from .fake_anthropic import FakeAnthropic, message

P = demo.PERIOD


@pytest.fixture
def desk(tmp_path):
    d = Desk(tmp_path / "ws")
    demo.seed(d.store)
    yield d
    d.close()


def _review(desk, cid, **decision):
    return desk.review(cid, P, decision, actor=decision.get("reviewer", ""))


def test_start_reaches_review_with_a_checked_draft(desk):
    st = desk.start("brightwave-dental", P, actor="Priya Raman")
    v = st["values"]
    assert st["status"] == g.NEEDS_REVIEW
    assert v["verification"]["ok"] and v["verification"]["checked"] > 30
    assert len(v["anomalies"]) == 2 and v["draft"].startswith("## Summary")
    assert len(v["history"]) == 1 and v["history"][0]["issues"] == 0
    assert any("Fact check passed" in line for line in v["log"])


def test_approve_needs_a_reviewer(desk):
    desk.start("kestrel-accounting", P)
    st = _review(desk, "kestrel-accounting", action="approve")
    assert st["status"] == g.NEEDS_REVIEW and "who is reviewing" in st["values"]["review_message"]


def test_approve_renders_and_saves_report(desk):
    desk.start("copperleaf-coffee", P)
    st = _review(desk, "copperleaf-coffee", action="approve", reviewer="Tom Ellison", comment="Looks good")
    assert st["status"] == g.APPROVED
    rep = st["reports"][-1]
    assert rep["version"] == 1 and rep["reviewer"] == "Tom Ellison" and rep["checked"] > 30
    html = desk.store.report_file("copperleaf-coffee", P, 1, "html").read_text()
    assert "Copperleaf Coffee" in html and "September 2026" in html and "Northstar Digital" in html
    assert "[F" not in html and "Reviewed and approved by Tom Ellison" in html
    assert "1,018" in html                                   # orders, straight from the data
    pdf = desk.store.report_file("copperleaf-coffee", P, 1, "pdf")
    assert pdf is not None and pdf.read_bytes()[:5] == b"%PDF-", rep.get("pdf_error")
    actions = [e["action"] for e in desk.store.audit_log(client_id="copperleaf-coffee")]
    assert "approved" in actions and "started report" in actions


def test_edit_is_rechecked_and_wrong_edit_blocks_approval(desk):
    st = desk.start("harbourside-law", P)
    draft = st["values"]["draft"]
    bad = draft.replace("## Summary\n\n", "## Summary\n\nPaid search delivered 999 enquiries. ", 1)
    st = _review(desk, "harbourside-law", action="approve", reviewer="Dani Okafor", text=bad)
    assert st["status"] == g.NEEDS_REVIEW
    assert "can't back" in st["values"]["review_message"]
    assert not st["values"]["verification"]["ok"]
    assert "999" in st["values"]["verification"]["issues"][0]["quote"]
    # a correct edit passes
    good = draft.replace("## Summary\n\n", "## Summary\n\nA steady month for the firm. ", 1)
    st = _review(desk, "harbourside-law", action="edit", reviewer="Dani Okafor", text=good)
    assert st["status"] == g.NEEDS_REVIEW and st["values"]["verification"]["ok"]
    st = _review(desk, "harbourside-law", action="approve", reviewer="Dani Okafor")
    assert st["status"] == g.APPROVED
    assert "A steady month for the firm." in desk.store.report_file("harbourside-law", P, 1, "html").read_text()


def test_flagged_figures_can_be_confirmed_and_are_audited(desk):
    st = desk.start("summit-fitness", P)
    bad = st["values"]["draft"] + "\nGym visits from the new poster campaign were 412.\n"
    _review(desk, "summit-fitness", action="edit", reviewer="Priya Raman", text=bad)
    st = _review(desk, "summit-fitness", action="approve", reviewer="Priya Raman")
    assert st["status"] == g.NEEDS_REVIEW
    st = _review(desk, "summit-fitness", action="approve", reviewer="Priya Raman", confirm_flagged=True)
    assert st["status"] == g.APPROVED and st["reports"][-1]["confirmed_flags"] == 1
    assert any(e["action"] == "confirmed flagged figure" for e in desk.store.audit_log())


def test_template_writer_refuses_free_text_requests(desk):
    desk.start("summit-fitness", P)
    with pytest.raises(DeskError, match="template writer"):
        _review(desk, "summit-fitness", action="request_changes", reviewer="Tom", change_request="Shorter")


def test_reviewer_explanations_and_next_steps_redraft(desk):
    st = desk.start("verde-landscaping", P)
    aid = st["values"]["anomalies"][0]["id"]
    st = _review(desk, "verde-landscaping", action="update_notes", reviewer="Tom Ellison",
                 explanations={aid: "The garden design guide was covered by a national paper."},
                 next_steps="Publish part two of the guide and add a booking form.")
    v = st["values"]
    assert st["status"] == g.NEEDS_REVIEW and v["verification"]["ok"]
    assert "covered by a national paper" in v["draft"] and "## Next month" in v["draft"]
    assert "part two of the guide" in v["draft"]


def test_reject(desk):
    desk.start("tidewater-yoga", P)
    st = _review(desk, "tidewater-yoga", action="reject", reviewer="Dani Okafor", reason="Client paused")
    assert st["status"] == g.REJECTED and st["reports"] == []
    assert any(e["action"] == "rejected" for e in desk.store.audit_log())


def test_no_data_blocks_with_reason(desk):
    st = desk.start("brightwave-dental", "2026-10")
    assert st["status"] == g.BLOCKED
    assert "No data has been uploaded for October 2026" in st["values"]["problems"][0]


def test_missing_source_is_warned(desk):
    cid = "summit-fitness"
    for s in desk.store.sources(cid, P):
        if s["type"] == "google_ads":
            desk.store.delete_source(cid, P, s["id"])
    st = desk.start(cid, P)
    assert st["status"] == g.NEEDS_REVIEW
    assert any("Google Ads was uploaded for August 2026 but not for September 2026" in w
               for w in st["values"]["warnings"])


def test_new_client_warns_no_comparisons(desk):
    st = desk.start("atlas-removals", P)
    assert any("no month-on-month comparisons" in w for w in st["values"]["warnings"])
    assert st["values"]["verification"]["ok"]


def test_start_all_drafts_every_client_in_parallel(desk):
    queued = desk.start_all(P, actor="Priya Raman")
    assert len(queued) == 12
    desk.wait()
    rows = desk.overview(P)
    assert {r["status"] for r in rows} == {g.NEEDS_REVIEW}
    assert all(r["issues"] == 0 and r["checked"] > 10 for r in rows)
    assert desk.start_all(P) == []                     # nothing new to do


def test_review_survives_restart(tmp_path):
    d1 = Desk(tmp_path / "ws")
    demo.seed(d1.store)
    d1.start("fernhill-care-homes", P)
    d1.close()
    d2 = Desk(tmp_path / "ws")
    assert d2.status("fernhill-care-homes", P) == g.NEEDS_REVIEW
    st = d2.review("fernhill-care-homes", P, {"action": "approve", "reviewer": "Tom Ellison"})
    assert st["status"] == g.APPROVED
    d2.close()


def test_double_approval_is_safe(desk):
    desk.start("northgate-motors", P)
    results, errors = [], []

    def approve():
        try:
            results.append(_review(desk, "northgate-motors", action="approve", reviewer="Tom Ellison"))
        except DeskError as e:
            errors.append(str(e))

    threads = [threading.Thread(target=approve) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 1 and len(errors) == 2
    assert len(desk.store.reports("northgate-motors", P)) == 1


def test_rerun_after_approval_makes_a_new_version(desk):
    desk.start("kestrel-accounting", P)
    _review(desk, "kestrel-accounting", action="approve", reviewer="Tom")
    st = desk.start("kestrel-accounting", P, fresh=True)
    assert st["status"] == g.NEEDS_REVIEW and st["run"] == 2
    _review(desk, "kestrel-accounting", action="approve", reviewer="Tom")
    assert [r["version"] for r in desk.store.reports("kestrel-accounting", P)] == [1, 2]


# --------------------------------------------------------------------------- #
# Claude in the loop (local fake API)
# --------------------------------------------------------------------------- #
@pytest.fixture
def fake(monkeypatch):
    f = FakeAnthropic()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f.url)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    yield f
    f.close()


def _good_draft(desk, cid):
    st = desk.start(cid, P, writer="template", fresh=True)
    return st["values"]["draft"]


def test_claude_wrong_figure_is_sent_back_and_fixed(desk, fake):
    good = _good_draft(desk, "brightwave-dental")
    wrong = good.replace("## Summary\n\n", "## Summary\n\nOrganic search delivered 110 enquiries [F57]. ", 1)
    fake.script = [message(wrong), message(good)]
    st = desk.start("brightwave-dental", P, writer="claude", fresh=True)
    v = st["values"]
    assert st["status"] == g.NEEDS_REVIEW and v["verification"]["ok"]
    assert [h["issues"] for h in v["history"]][-2:] == [1, 0]
    retry_prompt = fake.requests[1]["messages"][0]["content"]
    assert "fact-checker rejected" in retry_prompt and "Organic search delivered 110 enquiries" in retry_prompt
    assert "Paid Search" in retry_prompt                       # the hint names the right channel
    assert v["draft_info"]["writer"] == "claude"


def test_claude_that_never_gets_it_right_goes_to_a_person(desk, fake):
    good = _good_draft(desk, "summit-fitness")
    wrong = good.replace("## Summary\n\n", "## Summary\n\nSign-ups doubled this month. ", 1)
    fake.script = [message(wrong)] * 3
    st = desk.start("summit-fitness", P, writer="claude", fresh=True)
    assert st["status"] == g.NEEDS_REVIEW and len(fake.requests) == 3
    assert not st["values"]["verification"]["ok"]
    st = _review(desk, "summit-fitness", action="approve", reviewer="Tom")
    assert st["status"] == g.NEEDS_REVIEW                       # can't approve unchecked figures silently


def test_claude_follows_change_requests(desk, fake):
    good = _good_draft(desk, "lumen-skin-clinic")
    shorter = re.sub(r"## What stood out.*?(?=## Channel by channel)", "", good, flags=re.S)
    fake.script = [message(good), message(shorter)]
    desk.start("lumen-skin-clinic", P, writer="claude", fresh=True)
    st = _review(desk, "lumen-skin-clinic", action="request_changes", reviewer="Priya",
                 change_request="Drop the What stood out section.")
    assert st["status"] == g.NEEDS_REVIEW and "What stood out" not in st["values"]["draft"]
    prompt = fake.requests[1]["messages"][0]["content"]
    assert "Drop the What stood out section." in prompt and "THE CURRENT DRAFT" in prompt


def test_claude_outage_falls_back_and_says_why(desk, fake):
    from .fake_anthropic import error
    fake.script = [error(529, "overloaded_error", "Overloaded")] * 4
    st = desk.start("kestrel-accounting", P, writer="claude", fresh=True)
    v = st["values"]
    assert st["status"] == g.NEEDS_REVIEW and v["draft_info"]["writer"] == "template"
    assert "busy" in v["draft_info"]["fallback_reason"]
    assert any("template writer" in line for line in v["log"])
