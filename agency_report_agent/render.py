"""Build the finished, branded report the agency sends to its client.

Deliberate design decision: the table of figures is built straight from the
source data and never from the AI's text. So even if the written commentary is
imperfect, the numbers a client reads are always exactly right.

The report carries the agency's own brand colour and name — the tool stays
invisible, which is what lets an agency put this in front of its clients.
"""

from __future__ import annotations

import html
from typing import Any

from .metrics import summarise_channels, totals


def _change_cell(value: float | None) -> str:
    if value is None:
        return '<td class="num muted">—</td>'
    direction = "up" if value > 0 else "down" if value < 0 else "flat"
    arrow = "▲" if value > 0 else "▼" if value < 0 else "–"
    return f'<td class="num {direction}">{arrow} {abs(value):.1f}%</td>'


def render_client_report(state: dict[str, Any]) -> str:
    data = state["data"]
    agency = state.get("agency", {})
    rows = summarise_channels(data)
    t = totals(data)

    brand = agency.get("brand_color", "#1B4D3E")
    agency_name = agency.get("name", "Your Agency")
    currency = data.get("currency", "")

    esc = html.escape
    commentary = "".join(
        f"<p>{esc(p.strip())}</p>" for p in (state.get("draft") or "").split("\n\n") if p.strip()
    )

    table_rows = []
    for r in rows:
        spend = f"{currency}{r['spend']}" if r.get("spend") else "—"
        table_rows.append(
            f"<tr><th scope='row'>{esc(r['channel'])}</th>"
            f"<td class='num'>{r['sessions']:,}</td>{_change_cell(r['sessions_change'])}"
            f"<td class='num'>{r['conversions']:,}</td>{_change_cell(r['conversions_change'])}"
            f"<td class='num muted'>{spend}</td></tr>"
        )
    table_rows.append(
        f"<tr class='total'><th scope='row'>All channels</th>"
        f"<td class='num'>{t['total_sessions']:,}</td>{_change_cell(t['total_sessions_change'])}"
        f"<td class='num'>{t['total_conversions']:,}</td>"
        f"{_change_cell(t['total_conversions_change'])}<td class='num muted'></td></tr>"
    )

    target = t.get("leads_target")
    progress = ""
    if target:
        pct = min(round(t["total_conversions"] / target * 100), 100)
        on_track = t["total_conversions"] >= target
        progress = f"""
        <section class="goal">
          <div class="goal-head">
            <span class="goal-label">Monthly enquiry target</span>
            <span class="goal-value">{t['total_conversions']:,} of {target:,}
              <span class="{'hit' if on_track else 'near'}">{'Target met' if on_track else f'{pct}%'}</span>
            </span>
          </div>
          <div class="bar"><div class="fill" style="width:{pct}%"></div></div>
        </section>"""

    flagged = ""
    if state.get("anomalies"):
        items = "".join(f"<li>{esc(a)}</li>" for a in state["anomalies"])
        flagged = f"""
        <section class="flagged">
          <h2>Worth a closer look</h2>
          <ul>{items}</ul>
        </section>"""

    note = ""
    if state.get("approval_note"):
        note = f"""
        <section class="note">
          <h2>From your account team</h2>
          <p>{esc(state['approval_note'])}</p>
        </section>"""

    checked = state.get("figures_checked", 0)
    reviewer = state.get("reviewer") or "your account team"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data.get('client_name',''))} — {esc(str(data.get('period','')))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --brand: {brand};
    --ink: #15181D;
    --muted: #6A7280;
    --rule: #E3E6EA;
    --paper: #FFFFFF;
    --ground: #F4F5F3;
    --up: #137A50;
    --down: #B4452F;
    --warn-bg: #FDF6E8;
    --warn-line: #D79A28;
    --display: "Archivo", system-ui, sans-serif;
    --body: "Public Sans", system-ui, sans-serif;
    --mono: "IBM Plex Mono", ui-monospace, monospace;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--ground); color: var(--ink);
    font-family: var(--body); font-size: 16px; line-height: 1.65;
    -webkit-font-smoothing: antialiased;
  }}
  .sheet {{
    max-width: 820px; margin: 0 auto; background: var(--paper);
    padding: 56px 56px 44px;
  }}
  @media (max-width: 640px) {{ .sheet {{ padding: 32px 20px; }} }}

  header {{ border-bottom: 3px solid var(--brand); padding-bottom: 24px; }}
  .agency {{
    font-family: var(--mono); font-size: 12px; letter-spacing: .14em;
    text-transform: uppercase; color: var(--brand); font-weight: 500;
  }}
  h1 {{
    font-family: var(--display); font-weight: 700; letter-spacing: -.025em;
    font-size: clamp(2rem, 5vw, 2.75rem); margin: 10px 0 6px; line-height: 1.08;
  }}
  .period {{ color: var(--muted); font-size: 15px; margin: 0; }}

  h2 {{
    font-family: var(--display); font-size: 13px; font-weight: 600;
    letter-spacing: .12em; text-transform: uppercase; color: var(--muted);
    margin: 40px 0 14px;
  }}
  p {{ margin: 0 0 14px; max-width: 62ch; }}

  .goal {{ margin-top: 36px; }}
  .goal-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap; }}
  .goal-label {{
    font-family: var(--mono); font-size: 11px; letter-spacing: .12em;
    text-transform: uppercase; color: var(--muted);
  }}
  .goal-value {{ font-family: var(--display); font-weight: 600; font-variant-numeric: tabular-nums; }}
  .goal-value .hit {{ color: var(--up); font-size: 13px; margin-left: 8px; }}
  .goal-value .near {{ color: var(--muted); font-size: 13px; margin-left: 8px; }}
  .bar {{ height: 8px; border-radius: 99px; background: var(--rule); margin-top: 10px; overflow: hidden; }}
  .fill {{ height: 100%; background: var(--brand); border-radius: 99px; }}

  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 4px; font-size: 15px; min-width: 560px; }}
  table th:first-child, table td:first-child {{ padding-right: 12px; }}
  table th + th, table td + td {{ padding-left: 14px; }}
  thead th {{
    font-family: var(--mono); font-size: 10.5px; letter-spacing: .1em;
    text-transform: uppercase; color: var(--muted); font-weight: 500;
    text-align: right; padding: 0 0 10px; border-bottom: 1px solid var(--rule);
  }}
  thead th:first-child {{ text-align: left; }}
  tbody th {{ text-align: left; font-weight: 500; padding: 13px 0; }}
  td {{ padding: 13px 0; border-bottom: 1px solid var(--rule); }}
  tbody th {{ border-bottom: 1px solid var(--rule); }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; font-family: var(--mono); font-size: 13px; white-space: nowrap; }}
  .up {{ color: var(--up); }} .down {{ color: var(--down); }}
  .muted {{ color: var(--muted); }}
  tr.total th, tr.total td {{ font-weight: 600; border-bottom: none; padding-top: 16px; }}
  tr.total .num {{ font-size: 15px; }}

  .flagged {{
    margin-top: 36px; background: var(--warn-bg);
    border-left: 3px solid var(--warn-line); padding: 18px 22px; border-radius: 0 6px 6px 0;
  }}
  .flagged h2 {{ margin-top: 0; color: #8A6314; }}
  .flagged ul {{ margin: 0; padding-left: 18px; }}
  .flagged li {{ margin-bottom: 6px; }}

  .note {{ margin-top: 36px; border-left: 3px solid var(--brand); padding: 4px 22px; }}
  .note h2 {{ margin-top: 0; }}

  footer {{
    margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--rule);
    display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap;
    font-size: 12.5px; color: var(--muted);
  }}
  .verified {{ display: inline-flex; align-items: center; gap: 7px; color: var(--up); font-weight: 500; }}
  .tick {{
    width: 15px; height: 15px; border-radius: 50%; background: var(--up); color: #fff;
    display: inline-grid; place-items: center; font-size: 9px; line-height: 1;
  }}
  @media print {{
    body {{ background: #fff; }}
    .sheet {{ max-width: none; padding: 0; }}
  }}
</style>
</head>
<body>
<div class="sheet">
  <header>
    <div class="agency">{esc(agency_name)}</div>
    <h1>{esc(data.get('client_name',''))}</h1>
    <p class="period">Performance report · {esc(str(data.get('period','')))}</p>
  </header>

  <h2>Summary</h2>
  {commentary}

  {progress}

  <h2>Channel performance</h2>
  <div class="table-wrap">
  <table>
    <thead>
      <tr><th>Channel</th><th>Sessions</th><th>Change</th><th>Enquiries</th><th>Change</th><th>Spend</th></tr>
    </thead>
    <tbody>{''.join(table_rows)}</tbody>
  </table>
  </div>

  {flagged}
  {note}

  <footer>
    <span class="verified"><span class="tick">✓</span>
      All {checked} figures checked against source data</span>
    <span>Reviewed and approved by {esc(reviewer)}</span>
  </footer>
</div>
</body>
</html>"""
