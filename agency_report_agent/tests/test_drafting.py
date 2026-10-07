"""The template writer and the Claude writer (against a local fake of the API)."""

import pytest

from agency_report_agent import llm
from agency_report_agent.anomalies import find_anomalies
from agency_report_agent.demo import agency as demo
from agency_report_agent.drafting import DraftRequest, template_draft
from agency_report_agent.facts import build_facts
from agency_report_agent.model import shift_period
from agency_report_agent.store import Store
from agency_report_agent.verify import verify

from .fake_anthropic import FakeAnthropic, error, message


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    st = Store(tmp_path_factory.mktemp("ws"))
    demo.seed(st)
    return st


def _request(store, cid, **kw) -> DraftRequest:
    c = demo.client_def(cid)
    cur, notes = store.period_data(cid, demo.PERIOD)
    prev, _ = store.period_data(cid, shift_period(demo.PERIOD, -1))
    yago, _ = store.period_data(cid, shift_period(demo.PERIOD, -12))
    sheet = build_facts(cur, prev, yago, target=c["target"], conversion_label=c["label"])
    client = {"name": c["name"], "sector": c["sector"], "context": c["context"]}
    return DraftRequest(sheet, client, demo.AGENCY, find_anomalies(sheet), notes, **kw)


# --------------------------------------------------------------------------- #
# Template writer
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("cid", [c["id"] for c in demo.CLIENTS])
def test_template_draft_is_fully_verified(store, cid):
    req = _request(store, cid)
    draft = template_draft(req).text
    v = verify(draft, req.sheet)
    assert v.ok, [(i.kind, i.sentence, i.message) for i in v.issues]
    assert all(c.status == "verified" for c in v.claims), [c for c in v.claims if c.status != "verified"]
    for heading in ("## Summary", "## Channel by channel"):
        assert heading in draft
    assert ("## Worth a look" in draft) == bool(req.anomalies)
    assert " -" not in draft.replace(" - ", "")          # no stray minus signs
    assert "+" not in draft                              # signs are words, not symbols


def test_template_handles_paused_channel(store):
    draft = template_draft(_request(store, "oakfield-veterinary")).text
    assert "Paid Social:** No sessions this month" in draft


def test_template_new_client_has_no_comparisons(store):
    req = _request(store, "atlas-removals")
    draft = template_draft(req).text
    assert "first month" in draft and "on August" not in draft


def test_template_small_numbers_use_counts_not_percentages(store):
    draft = template_draft(_request(store, "tidewater-yoga")).text
    assert "up from 6 in August" in draft and "shouldn't be over-read" in draft


def test_template_includes_reviewer_explanations_and_next_steps(store):
    req = _request(store, "verde-landscaping", next_steps="Publish the second garden guide.")
    req.anomalies[0].explanation = "The garden guide was featured in a national paper."
    draft = template_draft(req).text
    assert "featured in a national paper" in draft and "## Next month" in draft


# --------------------------------------------------------------------------- #
# Claude writer, through the real SDK against a local fake API
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


def test_claude_request_shape_and_success(store, fake):
    req = _request(store, "brightwave-dental")
    good = template_draft(req).text
    fake.script = [message("Here is the draft:\n\n```markdown\n" + good + "```\nLet me know!")]
    res = llm.write_draft(req, "claude", "claude-opus-5-5")
    assert res.writer == "claude" and not res.fallback_reason
    assert res.text.startswith("## Summary") and "Let me know" not in res.text
    assert verify(res.text, req.sheet).ok
    body = fake.requests[0]
    assert body["model"] == "claude-opus-5-5"
    assert "temperature" not in body and "top_p" not in body
    assert body["thinking"] == {"type": "adaptive"} and body["output_config"] == {"effort": "medium"}
    assert "Northstar Digital" in body["system"] and "Direct and warm" in body["system"]
    user = body["messages"][0]["content"]
    assert "FACT SHEET" in user and "[F1]" in user and "enquiries" in user
    assert "New implants landing page" in user                     # client context
    assert {k.lower(): v for k, v in fake.headers[0].items()}.get("x-api-key") == "test-key"
    assert res.input_tokens == 1200 and res.output_tokens == 450


def test_claude_retries_when_overloaded(store, fake):
    req = _request(store, "summit-fitness")
    fake.script = [error(529, "overloaded_error", "Overloaded"), error(500, "api_error", "boom"),
                   message(template_draft(req).text)]
    res = llm.write_draft(req, "claude")
    assert res.writer == "claude" and len(fake.requests) == 3


@pytest.mark.parametrize("script,reason", [
    ([message("I can't help with that.", stop_reason="refusal")], "declined"),
    ([message("## Summary\nPaid Search", stop_reason="max_tokens")], "cut off"),
    ([error(401, "authentication_error", "invalid x-api-key")], "key was rejected"),
    ([error(404, "not_found_error", "model: nope")], "isn't available"),
    ([message("Sure! Here are some thoughts about the month.")], "format"),
    ([error(529, "overloaded_error", "Overloaded")] * 4, "busy"),
])
def test_claude_failures_fall_back_to_template(store, fake, script, reason):
    req = _request(store, "harbourside-law")
    fake.script = list(script)
    res = llm.write_draft(req, "claude")
    assert res.writer == "template" and reason in res.fallback_reason
    assert verify(res.text, req.sheet).ok


def test_claude_unsupported_setting_is_retried_without_it(store, fake):
    req = _request(store, "kestrel-accounting")
    fake.script = [error(400, "invalid_request_error", "thinking.type: adaptive is not supported on this model"),
                   message(template_draft(req).text, thinking=False)]
    res = llm.write_draft(req, "claude", "claude-opus-5-5")
    assert res.writer == "claude"
    assert "thinking" in fake.requests[0] and "thinking" not in fake.requests[1]


def test_haiku_gets_no_thinking_settings(store, fake):
    req = _request(store, "kestrel-accounting")
    fake.script = [message(template_draft(req).text, thinking=False, model="claude-haiku-4-5-20251001")]
    llm.write_draft(req, "claude", "claude-haiku-4-5-20251001")
    assert "thinking" not in fake.requests[0] and "output_config" not in fake.requests[0]


def test_no_api_key_falls_back(store, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = llm.write_draft(_request(store, "kestrel-accounting"), "claude")
    assert res.writer == "template" and "No Anthropic API key" in res.fallback_reason


def test_revision_prompt_carries_feedback_and_previous_draft(store):
    req = _request(store, "brightwave-dental", previous_draft="## Summary\nOld draft.",
                   verifier_feedback="1. \"Organic search delivered 143 enquiries.\" — wrong channel")
    _, user = llm.build_prompt(req)
    assert "Old draft." in user and "wrong channel" in user and "fixing exactly these" in user
    req2 = _request(store, "brightwave-dental", previous_draft="## Summary\nOld.", change_request="Shorter please")
    _, user2 = llm.build_prompt(req2)
    assert "Shorter please" in user2 and "REVIEWER ASKED" in user2


def test_new_client_prompt_says_no_comparisons(store):
    _, user = llm.build_prompt(_request(store, "atlas-removals"))
    assert "first month of data" in user


# --------------------------------------------------------------------------- #
# An OpenAI-compatible endpoint (Mistral, OpenRouter, a gateway) behind the same checks
# --------------------------------------------------------------------------- #
class _Resp:
    def __init__(self, status, payload):
        self.status_code, self._p = status, payload

    def json(self):
        return self._p


def test_compatible_endpoint_success_and_request_shape(store, monkeypatch):
    monkeypatch.setenv("REPORT_DESK_LLM_BASE_URL", "https://llm.example/v1/")
    monkeypatch.setenv("REPORT_DESK_LLM_KEY", "k-test")
    req = _request(store, "brightwave-dental")
    seen = {}

    def post(url, json, headers, timeout):
        seen.update(url=url, json=json, headers=headers)
        return _Resp(200, {"model": "mistralai/mistral-large-4-0", "usage": {"prompt_tokens": 9, "completion_tokens": 7},
                           "choices": [{"finish_reason": "stop", "message": {"content": template_draft(req).text}}]})

    res = llm.compatible_draft(req, "mistralai/mistral-large-4-0", post=post)
    assert res.writer == "claude" and verify(res.text, req.sheet).ok
    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer k-test"
    assert seen["json"]["messages"][0]["role"] == "system" and "temperature" not in seen["json"]


@pytest.mark.parametrize("status,payload,reason", [
    (401, {}, "rejected the API key"), (404, {}, "isn't available"), (429, {}, "rate limit"),
    (500, {}, "returned an error"), (200, {"nope": 1}, "expected format"),
    (200, {"choices": [{"finish_reason": "length", "message": {"content": "## Summary"}}]}, "cut off"),
    (200, {"choices": [{"finish_reason": "stop", "message": {"content": "Sure, here you go."}}]}, "format"),
])
def test_compatible_endpoint_failures(store, monkeypatch, status, payload, reason):
    monkeypatch.setenv("REPORT_DESK_LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("REPORT_DESK_LLM_KEY", "k")
    with pytest.raises(llm.DraftError, match=reason):
        llm.compatible_draft(_request(store, "kestrel-accounting"), "m/x", post=lambda *a, **k: _Resp(status, payload))


def test_non_claude_model_without_endpoint_falls_back(store, monkeypatch):
    for v in ("REPORT_DESK_LLM_BASE_URL", "REPORT_DESK_LLM_KEY", "REPORT_DESK_LLM_MODEL"):
        monkeypatch.delenv(v, raising=False)
    res = llm.write_draft(_request(store, "kestrel-accounting"), "claude", "mistralai/mistral-large-4-0")
    assert res.writer == "template" and "No endpoint" in res.fallback_reason


def test_extra_model_appears_in_settings_choices(monkeypatch):
    monkeypatch.setenv("REPORT_DESK_LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("REPORT_DESK_LLM_KEY", "k")
    monkeypatch.setenv("REPORT_DESK_LLM_MODEL", "mistralai/mistral-large-4-0")
    assert "mistralai/mistral-large-4-0" in llm.available_models() and llm.claude_available()
