"""The one place the agent talks to Claude.

In mock mode (the default, and free) this file is never even imported, so the
whole product runs with no API key and no cost. The draft step imports it only
when live mode is switched on.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Claude Opus 5.5 is the most capable general model. For this drafting job you
# can cut cost by roughly 20x by setting AGENT_MODEL=claude-haiku-4-5 in .env.
DEFAULT_MODEL = "claude-opus-5-5"

BASE_RULES = """You write the summary section of a monthly performance report \
that a marketing agency sends to its client.

Hard rules, in order of importance:
1. Only state figures that appear in the data you are given. Never invent, \
round differently, or estimate a number.
2. Any percentage you write must be either a month-on-month change or a \
conversion rate that follows from the data.
3. Write three short paragraphs: what happened, what stood out, what happens next.
4. Write for a busy business owner, not a marketer. No jargon, no hype.
5. No greeting and no sign-off."""


def draft_commentary(
    data: dict[str, Any],
    agency: dict[str, Any] | None = None,
    previous_issues: list[str] | None = None,
    model: str | None = None,
) -> str:
    """Ask Claude to write the report summary from the client's figures.

    `previous_issues` carries the specific figures a previous draft got wrong.
    Passing them back is what makes the rewrite a real correction rather than
    just another roll of the dice.
    """
    from langchain_anthropic import ChatAnthropic  # imported only in live mode

    model = model or os.environ.get("AGENT_MODEL", DEFAULT_MODEL)
    agency = agency or {}

    system = BASE_RULES
    if agency.get("voice"):
        system += f"\n\nWrite in {agency.get('name', 'the agency')}'s house voice: {agency['voice']}"

    parts: list[str] = []
    if previous_issues:
        parts.append(
            "Your previous draft stated figures that are not in the data. "
            "Correct these and use only real figures:\n- " + "\n- ".join(previous_issues) + "\n"
        )
    parts.append("The client's data for this period:")
    parts.append(json.dumps(data, indent=2))
    parts.append("\nWrite the summary now, following every rule.")

    llm = ChatAnthropic(model=model, max_tokens=1500, temperature=0)
    response = llm.invoke([("system", system), ("user", "\n".join(parts))])

    content = response.content
    if isinstance(content, str):
        return content.strip()
    return "".join(b.get("text", "") for b in content if isinstance(b, dict)).strip()
