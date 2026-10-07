"""Claude as the report writer, through the official Anthropic SDK.

Claude is given the fact sheet (every figure it may use, each with an ID), the
unusual movements, the client's context and the agency's house voice. It must
cite a fact ID after every figure. The fact checker then reads the draft; if
anything is wrong, Claude gets the exact statements back and fixes only those.

If Claude can't be used — no API key, an outage, a refusal, a truncated reply
— the template writer produces the draft instead and the reason is recorded,
so a report is never blocked on the model.
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional

from .drafting import DraftRequest, DraftResult, template_draft
from .facts import singular
from .model import period_label

DEFAULT_MODEL = "claude-opus-5-5"
MODELS = {
    "claude-opus-5-5": "Claude Opus 5.5 — best writing",
    "claude-sonnet-5-5": "Claude Sonnet 5.5 — balanced",
    "claude-haiku-4-5-20251001": "Claude Haiku 4.5 — fastest and cheapest",
}
# Models with adaptive thinking and the effort setting.
_ADAPTIVE = ("claude-opus-5", "claude-sonnet-5", "claude-fable-5")
MAX_TOKENS = 16000
TIMEOUT = 240.0


class DraftError(Exception):
    """A reason Claude could not produce a usable draft, written for the agency."""


def api_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def claude_available() -> bool:
    return bool(api_key())


# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #
def build_prompt(req: DraftRequest) -> tuple[str, str]:
    sh, client, agency = req.sheet, req.client, req.agency
    month = period_label(sh.period)
    label, one = sh.conversion_label, singular(sh.conversion_label)
    agency_name = agency.get("name") or "the agency"
    system = f"""You write the narrative of the monthly marketing performance report that {agency_name} \
sends to its client, {client.get('name', 'the client')}. A person at {agency_name} reviews your draft, \
and an automatic fact checker reads every figure in it before they see it.

RULES FOR FIGURES — the fact checker enforces all of these:
1. Use only figures from the FACT SHEET. Copy them as shown. You may round a percentage to a whole \
number, but never round counts or money, and never compute anything new: no sums of channels, no \
averages, no differences or percentages that are not on the sheet.
2. Put the fact ID in square brackets straight after every figure, e.g. "143 {label} [F31]".
3. Name the channel in every sentence that states a figure. A figure in a sentence with no channel \
is read as the account total ("All channels").
4. A figure is read as {month} unless the sentence says otherwise. When you use a figure from another \
month, say which month ("in August", "a year ago").
5. Get directions right: never say a figure rose when the sheet shows it fell. Changes under 2.5% \
should be described as broadly flat.
6. "{label}" is what this client counts as a conversion. Call them {label}.
7. No figures in the Next month section unless they appear on the fact sheet.

WRITING
- The reader runs a business, not a marketing team. Plain English, no jargon (no "CTR", "ROAS", \
"CPA" or "sessions" without saying what they mean the first time — e.g. "visits to the website \
(sessions)").
- Lead with what the month meant for their business, then the detail.
- Do not guess at causes. Only explain a movement with something from the CLIENT CONTEXT or the \
AGENCY NOTES. Otherwise say plainly what happened.
- Never over-claim. Small numbers move a lot; say so when it matters.
- No greeting, no sign-off, no headline above the first section.

FORMAT — markdown with exactly these sections, in this order:
## Summary
(one paragraph, 3–5 sentences)
## What stood out
(2–4 bullets)
## Channel by channel
(one bullet per channel on the fact sheet, starting with the channel name in bold, e.g. \
"- **Paid Search:** …")
## Worth a look
(only if UNUSUAL MOVEMENTS lists something: one bullet each, including the reviewer's \
explanation when one is given)
## Next month
(only if AGENCY NOTES FOR NEXT MONTH is not empty: rewrite those notes clearly, adding nothing)

Keep the whole draft between 250 and 450 words."""
    if agency.get("voice"):
        system += f"\n\nHOUSE VOICE — write the way {agency_name} writes: {agency['voice']}"

    parts: list[str] = [f"CLIENT: {client.get('name', '')} ({client.get('sector', '') or 'no sector given'})",
                        f"REPORTING MONTH: {month}"]
    if sh.previous_period:
        parts.append(f"COMPARED WITH: {period_label(sh.previous_period)}"
                     + (f" and {period_label(sh.year_ago_period)}" if sh.year_ago_period else ""))
    else:
        parts.append("COMPARED WITH: nothing — this is the first month of data. Say so; do not imply trends.")
    parts.append(f"CONVERSIONS ARE CALLED: {label} (one {one})")
    parts.append("CLIENT CONTEXT: " + (client.get("context", "").strip() or "none given"))
    parts.append("\nFACT SHEET (the only figures you may use):\n" + sh.sheet_text())
    if req.anomalies:
        lines = []
        for a in req.anomalies:
            line = f"- [{a.id}] {a.text}"
            if a.explanation.strip():
                line += f" Reviewer's explanation: {a.explanation.strip()}"
            lines.append(line)
        parts.append("\nUNUSUAL MOVEMENTS:\n" + "\n".join(lines))
    else:
        parts.append("\nUNUSUAL MOVEMENTS: none — leave out the Worth a look section.")
    if req.data_notes:
        parts.append("\nDATA NOTES (for your understanding; do not repeat them in the report):\n"
                     + "\n".join(f"- {n}" for n in req.data_notes))
    parts.append("\nAGENCY NOTES FOR NEXT MONTH: " + (req.next_steps.strip() or "none — leave out the section."))
    if req.previous_draft and req.verifier_feedback:
        parts.append("\nYOUR PREVIOUS DRAFT:\n" + req.previous_draft)
        parts.append("\n" + req.verifier_feedback +
                     "\nRewrite the draft fixing exactly these statements. Keep everything else as it was.")
    elif req.previous_draft and req.change_request:
        parts.append("\nTHE CURRENT DRAFT:\n" + req.previous_draft)
        parts.append("\nTHE REVIEWER ASKED FOR THESE CHANGES:\n" + req.change_request.strip() +
                     "\nRewrite the draft to make these changes. All the rules still apply.")
    else:
        parts.append("\nWrite the draft now.")
    return system, "\n".join(parts)


# --------------------------------------------------------------------------- #
# Calling Claude
# --------------------------------------------------------------------------- #
def _params(model: str, system: str, user: str, rich: bool = True) -> dict[str, Any]:
    p: dict[str, Any] = {"model": model, "max_tokens": MAX_TOKENS, "system": system,
                         "messages": [{"role": "user", "content": user}]}
    if rich and model.startswith(_ADAPTIVE):
        p["thinking"] = {"type": "adaptive"}
        p["output_config"] = {"effort": "medium"}
    return p


def _client():
    import anthropic

    key = api_key()
    if not key:
        raise DraftError("No Anthropic API key is set, so the template writer was used.")
    kwargs: dict[str, Any] = {"api_key": key, "max_retries": 3, "timeout": TIMEOUT}
    base = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    if base:
        kwargs["base_url"] = base
    return anthropic.Anthropic(**kwargs)


def _call(client, params: dict[str, Any]):
    import anthropic

    try:
        return client.messages.create(**params)
    except anthropic.BadRequestError as e:
        msg = str(e).lower()
        if ("thinking" in params or "output_config" in params) and \
                any(k in msg for k in ("thinking", "output_config", "effort", "not supported")):
            # An older model behind this ID: retry once without the newer settings.
            slim = {k: v for k, v in params.items() if k not in ("thinking", "output_config")}
            return _call(client, slim)
        raise DraftError(f"Claude rejected the request: {_short(e)}") from e
    except anthropic.AuthenticationError as e:
        raise DraftError("The Anthropic API key was rejected. Check it in the environment settings.") from e
    except anthropic.PermissionDeniedError as e:
        raise DraftError("This API key isn't allowed to use that model.") from e
    except anthropic.NotFoundError as e:
        raise DraftError(f"The model \"{params['model']}\" isn't available to this API key.") from e
    except anthropic.RateLimitError as e:
        raise DraftError("Claude's rate limit was reached; try again in a minute.") from e
    except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
        raise DraftError("Couldn't reach Claude (network or timeout).") from e
    except anthropic.APIStatusError as e:
        raise DraftError(f"Claude returned an error ({e.status_code}); it may be busy.") from e


def _short(e: Exception) -> str:
    s = str(e)
    return s if len(s) < 200 else s[:200] + "…"


def clean_draft(text: str) -> str:
    """Strip anything around the draft itself: code fences, preambles, trailing chatter."""
    t = text.strip()
    i = t.find("## ")
    if i > 0:
        t = t[i:]
    end = t.find("\n```")
    if end >= 0:
        t = t[:end]
    return t.strip() + "\n"


def claude_draft(req: DraftRequest, model: Optional[str] = None, client=None) -> DraftResult:
    model = model or os.environ.get("REPORT_DESK_MODEL") or DEFAULT_MODEL
    system, user = build_prompt(req)
    client = client or _client()
    resp = _call(client, _params(model, system, user))
    stop = getattr(resp, "stop_reason", None)
    if stop == "refusal":
        raise DraftError("Claude declined to write this draft.")
    if stop in ("max_tokens", "model_context_window_exceeded"):
        raise DraftError("Claude's draft was cut off before it finished.")
    text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
    text = clean_draft(text)
    if "## Summary" not in text or "## Channel by channel" not in text:
        raise DraftError("Claude's draft didn't follow the report format.")
    usage = getattr(resp, "usage", None)
    return DraftResult(text, "claude", getattr(resp, "model", model),
                       input_tokens=getattr(usage, "input_tokens", 0) or 0,
                       output_tokens=getattr(usage, "output_tokens", 0) or 0)


def write_draft(req: DraftRequest, writer: str = "template", model: Optional[str] = None,
                client=None) -> DraftResult:
    """Draft with the chosen writer; fall back to the template writer if Claude can't be used."""
    if writer == "claude":
        try:
            return claude_draft(req, model, client)
        except DraftError as e:
            result = template_draft(req)
            result.fallback_reason = str(e)
            return result
    return template_draft(req)


__all__ = ["DEFAULT_MODEL", "MODELS", "DraftError", "build_prompt", "claude_available", "claude_draft",
           "clean_draft", "write_draft"]
