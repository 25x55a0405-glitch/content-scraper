"""The one place the agent talks to Claude.

In mock mode (the default, and free) this module is never imported, so you can
run the whole graph with no API key and no cost. It is imported lazily by the
draft node only when you turn live mode on.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Default model. Claude Opus 5.5 is the most capable general model.
# For this report-drafting job you can cut the cost dramatically by setting
#   AGENT_MODEL=claude-haiku-4-5
# in your .env file — see the README.
DEFAULT_MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """You write the commentary section of a monthly marketing \
report that a digital agency sends to its client. Write in a clear, confident, \
client-friendly voice. Explain what the numbers mean for the client's business, \
not just what they are.

Hard rules:
- Only state numbers that appear in the data you are given. Never invent or \
estimate a figure.
- If you mention a percentage change, it must be one from the data.
- Keep it to 3 short paragraphs.
- Do not include a greeting or sign-off."""


def draft_commentary(
    data: dict[str, Any],
    previous_issues: list[str] | None = None,
    model: str | None = None,
) -> str:
    """Ask Claude to draft the report commentary from the client's metrics.

    `previous_issues` carries the feedback from a failed number-check so the
    model can fix its mistakes on the next pass — this is what makes the
    verification loop actually improve the draft.
    """
    from langchain_anthropic import ChatAnthropic  # imported only in live mode

    model = model or os.environ.get("AGENT_MODEL", DEFAULT_MODEL)

    user_parts = [
        "Here is the client's data for this reporting period as JSON:",
        json.dumps(data, indent=2),
        "",
        "Write the commentary now, following every rule.",
    ]
    if previous_issues:
        user_parts.insert(
            0,
            "Your previous draft contained numbers that were not in the data. "
            "Fix these problems and use only real figures this time:\n- "
            + "\n- ".join(previous_issues)
            + "\n",
        )

    llm = ChatAnthropic(model=model, max_tokens=1500, temperature=0)
    response = llm.invoke(
        [("system", SYSTEM_PROMPT), ("user", "\n".join(user_parts))]
    )

    content = response.content
    if isinstance(content, str):
        return content.strip()
    # Some responses come back as a list of content blocks; join the text parts.
    return "".join(
        block.get("text", "") for block in content if isinstance(block, dict)
    ).strip()
