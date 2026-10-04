# Asset inventory

No website was captured (no-capture mode — the product has no public site yet).
Three real product screenshots were supplied by the user and staged into `assets/`.

| Asset | What it is | Where it belongs |
|---|---|---|
| `assets/screen-dashboard.png` | The real Report Desk dashboard: client roster, status pills ("Needs you", "Approved"), KPI row including "Figures checked 41 / 6 corrected before you saw them". | Beat 2 — the roster drafting at once. Reference for layout; rebuilt as live DOM so rows can animate. |
| `assets/screen-review.png` | The real review screen, including the "Fact-check trail" panel: "Draft 1 — 7 figures checked / 1 did not match the source data, so the agent rewrote it" then "Draft 2 — Every figure matched the source data." | Beat 3 (HERO) — the self-correction loop. Reference for the trail's wording and layout. |
| `assets/screen-client-report.png` | The real branded client report for "Brightwave Dental" by "Northstar Digital": summary prose, channel performance table, "Worth a closer look" callout, and the footer "All 7 figures checked against source data". | Beat 5 — the approved report going out. |

Note: screenshots were taken in a sandbox where Google Fonts were blocked, so they
show fallback typography. Use them for layout and content truth only — type in the
film follows `frame.md`, not the screenshots.
