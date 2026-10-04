# Agency Report Agent

An AI **agent graph** (built with LangGraph + LangChain) that writes a marketing
agency's monthly client report, checks its own numbers, flags anything unusual
for a human, and only "sends" the report after a person approves it.

This is the demo for the Agency Report Agent offer. You can run it **for free,
with no API key**, and watch the whole thing work.

---

## What makes it an agent graph (not just a script)

It has a **loop**, **branches**, and a **human-in-the-loop** approval step:

```
 fetch_data ──(data ok?)──> detect_anomalies ──> draft_commentary
     │  ▲ no                                            │
     └──┘ retry (max 2)                                 ▼
                                                 verify_numbers
                                                  │        ▲
                       (numbers match?) no, retry │        │  loop
                               ┌──────────────────┘        │
                               ▼                           │
                        draft_commentary ─────────────────┘
                               │ yes (or gave up after N tries)
                               ▼
                        human_approval ──(approved?)──> render_report ──> END
                               │ rejected
                               └──────────────────────────────────────> END
```

- **Loop:** if the draft contains a number that isn't in the client's data, the
  agent rewrites it — up to 3 tries — until every figure checks out.
- **Branches:** retry if the data won't load; rewrite or move on after the
  number check; render or stop after the human decides.
- **Human-in-the-loop:** nothing is "sent" until a person approves it.

---

## Run it (free, no API key)

1. Install the one dependency for free mode:
   ```
   pip install langgraph
   ```
2. From the repository's top folder (`content-scraper/`), run:
   ```
   python -m agency_report_agent.cli --demo-glitch
   ```
   The `--demo-glitch` flag makes the first draft contain one wrong number **on
   purpose**, so you can watch the verification loop catch it and fix it. This is
   the moment to capture for your demo video.

3. Approve the draft when prompted (`y`). The finished report appears in
   `agency_report_agent/output/`.

Other ways to run:
```
python -m agency_report_agent.cli                    # normal free run (asks for approval)
python -m agency_report_agent.cli --auto-approve     # free run, no prompt
python -m agency_report_agent.cli --client path/to/your_client.json
```

## Run the quality checks (the "eval sheet" you show clients)

```
python -m agency_report_agent.tests.run_evals
```

This proves the agent catches made-up numbers and corrects itself. Showing a
prospect a passing eval sheet answers their biggest worry: *"Can I trust what
the AI writes?"*

## Run it live with Claude (costs a few cents)

1. Install the live dependencies:
   ```
   pip install langgraph langchain-anthropic python-dotenv
   ```
2. Copy `.env.example` to `.env` and add your Anthropic API key.
3. Run:
   ```
   python -m agency_report_agent.cli --live
   ```

**Cost:** one report is well under a cent of tokens. The default model is
`claude-opus-5-5`. For this simple drafting job you can cut cost by roughly 20x
by setting `AGENT_MODEL=claude-haiku-4-5` in your `.env`.

---

## Use your own (or a prospect's) data

Copy `sample_data/brightwave_dental.json`, change the numbers, and pass it with
`--client`. For a real demo to a specific agency, fill it with one of *their*
clients' public figures — a personalized demo gets far more replies.

## How this maps to the business

- **What you sell:** this agent, set up on the agency's own accounts.
- **Entry offer:** a ~$900 fixed pilot on 3 of their clients, money-back if the
  drafts aren't usable.
- **Why it's safe to deliver:** it only *reads* marketing data and never sends
  anything without a human approving it — so even though it's built with help
  from AI coding tools, the blast radius is tiny.

See `../reports/Agent graph offers for first client.md` for the full plan.

---

## Honest limitations (v1)

- The number-checker validates figures that come straight from the data, plus
  month-over-month changes and conversion rates. If the draft cites some other
  derived metric, it will be flagged — add it to the allowed sets in
  `metrics.py` if you want the agent to use it.
- `fetch_data` reads a local JSON file. Connecting live GA4 / Search Console /
  ad accounts is the next step, and is best done through the agency's own
  credentials.
- Approval here is a terminal prompt. In production, move it to Slack (LangGraph
  supports pausing a run for outside approval).
- This is a demo, not audited production software. Before a paying client goes
  live, run a security review and keep every credential on the client's accounts.
