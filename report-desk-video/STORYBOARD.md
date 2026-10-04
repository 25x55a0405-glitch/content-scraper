---
format: 1920x1080
duration: 30s
message: "It catches its own mistakes, and never sends without you"
arc: Pain → Scale → Self-correction (hero) → Proof → Approval → Lockup
audience: Owners of 5-50 person UK/US marketing agencies
mode: autonomous
music: none
---

## Video direction

**Palette system** (from `frame.md`, never invented). Paper `bg-primary #F6F6F4` is the
only ground — it never changes, in any frame. Ink `text-primary #15181C` is all type.
`text-secondary #717A85` is chrome and labels. `line #E4E6E3` is every rule and border.
**Colour is rationed to exactly two meanings:** `attention #8A5A0B` amber = *a human is
needed*; `accent #136B3F` green = *checked and matched the source data*. Amber appears in
three places in the whole film and green in four. Nothing else is ever coloured — no
coloured chrome, no coloured hairlines, no tinted panels except the single amber wash
`bg-secondary #FBF0DC` behind a "needs you" callout.

**Motion grammar.** Long-tail `power3` settles; smooth over bouncy; one spring only, on
the single approval press in Frame 5. Entrances ease out, exits ease in. No element shares
a start time with another — stagger at irregular offsets.

**Reveal model.** There is no voiceover, so reveals pace to **reading rhythm**: a line
appears, is readable for at least 0.8s before anything competes with it, and the next piece
arrives on that cadence. Never front-load — at t=0 each frame shows only its first idea.
Reveals are spread across the back half of every frame.

**The continuity device — a single hairline.** One 1px `line` rule is the film's spine and
**crosses every cut**: it is the dashboard's row rule in F2, it slides up to underline the
draft sentence in F3, it becomes the stat baseline in F4, it becomes the report's brand rule
in F5, and it settles under the wordmark in F6. It never fades out between frames; it
travels. This is what stops six shots reading as a slideshow.

**Rhythm / held frames.** F3 is the hero and carries the film's one real **dwell** —
1.6s where the camera rests and only the trail resolves. F6 is a held read. F1, F2, F4 and
F5 reveal continuously. Energy must vary: F2 is the busiest, F3 goes quiet so the
correction lands, F4 snaps back.

**UI is rebuilt as live DOM, not pasted screenshots.** The three staged PNGs are **layout
and content truth only** — real wording, real numbers, real status language. Workers rebuild
those surfaces in HTML so rows, pills and figures can actually animate. (The PNGs were
captured where webfonts were blocked, so their typography is wrong; type follows `frame.md`.)

**Negative list.** Never: purple/blue gradients, neon, glassmorphism, dark mode, glow
bloom, drop shadows of any kind, rounded corners above 2px, stock-photo texture, browser
chrome, nav bars, scrollbars, floating bokeh. Never the two motion failure modes —
**slideshow** (everything dumped at t=0 then frozen) and **screensaver** (elements drifting
independently with nothing driving them). No sound of any kind: this cut is silent.

**Numbers are real.** 41 figures checked and 6 corrected are the actual eval output of the
shipped product. Never inflate a figure in this film.

## Frame 1 — Twenty clients, three days

- src: compositions/frames/01-twenty-clients.html
- scene: "20 clients." "Monthly reports." "Three days gone." slam in over a faint roster forming
- duration: 4.5s
- transition_in: cut
- status: outline
- blueprint: kinetic-type-beats (Reproduce)
- focal: the three-beat statement
- roles: statement = cutout · faint roster column = background (dim ~18%)
- handoff_out: the faint roster's topmost 1px `line` row-rule sits at y=62% of frame, x spanning 18%–82%, opacity 1, scale 1, drifting left at ~6px/s
- rules: kinetic-beat-slam, waterfall-entry

No captured assets — this frame is typographic; the roster behind is drawn.

The cost, stated before the cure. Three short declaratives, each its own beat, over a roster
that is quietly accumulating behind them — the viewer feels the pile before they read it.

Scene 1 (0.0–1.1s): paper ground, empty. "20 clients." slams in dead-centre, Archivo display
weight, ink — Centered template, type occupying ~46% of frame width. Nothing else exists yet.
Scene 2 (1.1–2.3s): the first line lifts to the upper third and dims to `text-secondary`;
"Monthly reports." slams into the vacated centre. Behind both, a faint column of 20 thin
client rows begins cascading in from the top at ~18% opacity — layered-depth, the roster is
the background plane, type is foreground.
Scene 3 (2.3–3.6s): both prior lines stack and dim; "Three days gone." slams in, the only
full-ink line. The roster finishes its cascade and its topmost row rule settles into a crisp
1px `line` at y=62% — this is the rule that will travel the whole film.
Scene 4 (3.6–4.5s): held read. The three lines sit still; the only motion is the roster rule
drifting left a few pixels. No breathing on the type — stillness is the point.

## Frame 2 — It drafts all twenty

- src: compositions/frames/02-drafts-all-twenty.html
- scene: the real dashboard rebuilt live; 20 rows fill with status, the "Needs you" count climbs
- duration: 5.5s
- transition_in: cut
- status: outline
- blueprint: agent-progress-theater (Adapt)
- asset_candidates: assets/screen-dashboard.png
- focal: assets/screen-dashboard.png
- roles: screen-dashboard = supporting (layout + content truth; rebuilt as live DOM, never pasted)
- handoff_in: the 1px `line` row-rule enters exactly where F1 left it — y=62%, x 18%–82%, opacity 1, scale 1, still drifting left at ~6px/s; it becomes the first row rule of the table as the table assembles around it
- handoff_out: that same rule has risen to y=30%, x spanning 14%–86%, opacity 1, scale 1, motion arrested (0px/s)
- rules: waterfall-entry, spring-pop-entrance, counting-dynamic-scale

Adapt: keep agent-progress-theater's signature — **the receipt cascade, rows arriving and
resolving into state** — but there is no trigger click and no loader spinner; the work is
already underway when we cut in, and the table assembles *around* the inherited hairline.

Scene 1 (0.0–1.0s): the inherited hairline is on screen alone, then column headers and the
first client rows waterfall down from it — the dashboard building itself around the rule.
Asymmetric 70/30, table left-weighted, KPI rail reserved right.
Scene 2 (1.0–2.6s): rows continue cascading to twenty. As each lands, its figure count writes
in (`7 figures`, `6 figures`) in `text-secondary` mono — a staggered, irregular arrival, never
a single synchronized dump.
Scene 3 (2.6–4.1s): status pills spring-pop onto the rows in a scattered order, amber
"Needs you" dominating — the first and heaviest use of `attention` in the film. The right rail's
"Needs you" counter counts up alongside, scale growing slightly with the value.
Scene 4 (4.1–5.5s): the table recedes (dims to ~55%, no blur) and the inherited row rule
rises to y=30% and stops dead, carrying the eye upward into the next frame. Content holds;
only the rule moves.

## Frame 3 — It catches its own mistake  ★ HERO

- src: compositions/frames/03-catches-its-mistake.html
- scene: a draft sentence beside its fact-check trail; a figure is flagged amber, rewritten, verified green
- duration: 8s
- transition_in: crossfade
- status: outline
- blueprint: panel-edit-live-sync (Adapt)
- asset_candidates: assets/screen-review.png
- focal: assets/screen-review.png
- roles: screen-review = supporting (trail wording + layout truth; rebuilt as live DOM)
- handoff_in: the 1px `line` rule enters at y=30%, x 14%–86%, opacity 1, scale 1, motion arrested; it drops to sit directly under the draft sentence
- handoff_out: the rule sits under the resolved sentence at y=46%, x 14%–62%, opacity 1, scale 1, static
- rules: control-target-sync, discrete-text-sequence, depth-of-field-blur

Adapt: keep panel-edit-live-sync's signature — **a bound panel and surface changing in the
same beat** — but no cursor and no human touches it. The agent is the one operating the
control, which is the entire argument of the film. This frame gets the dwell.

Scene 1 (0.0–1.4s): the draft sentence types into the left two-thirds under the inherited
rule, ink on paper, generous measure — asymmetric 65/35. The right third holds an empty
"Fact-check trail" panel, hairline-bordered, no fill.
Scene 2 (1.4–2.8s): "Draft 1 — 7 figures checked" writes into the trail. In the same beat,
seven small tick marks stamp along the sentence's figures, left to right.
Scene 3 (2.8–4.2s): the final tick fails. The figure `95.0%` in the sentence turns
`attention` amber and the trail writes "1 did not match the source data" with an amber node —
the panel and the sentence change together, one beat, bound.
Scene 4 (4.2–5.8s): **the dwell.** Everything stops. Off-focus planes rack to a soft blur;
only the amber figure stays sharp. 1.6 seconds of near-stillness while the mistake sits there,
admitted. No camera move, no breathing.
Scene 5 (5.8–7.0s): the figure rewrites in place — `95.0%` steps to `88.9%` through a short
discrete sequence, not a fade — and settles `accent` green. "Draft 2 — Every figure matched
the source data" writes into the trail below, green node. Blur racks back off.
Scene 6 (7.0–8.0s): held read, fully resolved and still. The corrected sentence and the
two-step trail read together as one picture.

## Frame 4 — Forty-one figures checked

- src: compositions/frames/04-figures-checked.html
- scene: "41" counts up over a hairline baseline; "6 corrected before you saw them" stamps under it
- duration: 4.5s
- transition_in: cut
- status: outline
- blueprint: dataviz-countup (Reproduce)
- asset_candidates: assets/screen-dashboard.png
- focal: the 41 count-up
- roles: screen-dashboard = background (the KPI row is the source of truth for these figures; not shown, informs wording only)
- handoff_in: the 1px `line` rule enters at y=46%, x 14%–62%, opacity 1, scale 1, static; it extends rightward to become the stat's baseline
- handoff_out: the rule sits as a full-width baseline at y=58%, x 10%–90%, opacity 1, scale 1, static
- rules: counting-dynamic-scale, waterfall-entry

The proof beat. One number, large, with the harder second number underneath it — the
correction count is the claim that actually matters, so it lands last.

Scene 1 (0.0–0.5s): the inherited rule extends rightward across the frame and stops — the
baseline is laid before anything sits on it. Centered template.
Scene 2 (0.5–2.2s): "41" counts up from 0 above the baseline at display scale, tabular
figures, scale growing slightly with the value, settling on a long tail. The label "FIGURES
CHECKED" is already set small in `text-secondary` beneath — it does not animate.
Scene 3 (2.2–3.3s): "6 corrected before you saw them" waterfalls in below the baseline,
the word "corrected" in `accent` green — the fourth and last green in the film.
Scene 4 (3.3–4.5s): held read, entirely still. The two figures and the baseline read as one
composed unit.

## Frame 5 — Nothing goes out until you approve it

- src: compositions/frames/05-approve.html
- scene: a cursor presses Approve; the branded client report rises into frame
- duration: 5s
- transition_in: cut
- status: outline
- blueprint: cursor-ui-demo (Adapt)
- asset_candidates: assets/screen-review.png, assets/screen-client-report.png
- focal: assets/screen-client-report.png
- roles: screen-review = supporting (the approve control) · screen-client-report = cutout (the deliverable; rebuilt as live DOM)
- handoff_in: the 1px `line` rule enters as a full-width baseline at y=58%, x 10%–90%, opacity 1, scale 1, static; the approve control sits on it and the report rises from behind it
- handoff_out: the rule has settled to y=70%, x 36%–64%, opacity 1, scale 1, static
- rules: cursor-click-ripple, press-release-spring, nudge-curve

Adapt: keep cursor-ui-demo's signature — **a cursor driving a real surface through a state
change** — compressed to one deliberate press. This is the only spring in the film, and the
only place a human acts.

Scene 1 (0.0–1.0s): an ink "Approve & generate report" control sits on the inherited baseline,
centred. A simple cursor travels in from lower-right on a long tail. Centered template,
generous empty paper around it — the restraint is the point.
Scene 2 (1.0–1.6s): the press. Control and cursor compress together and spring back; one
quiet ripple. The only spring in the film.
Scene 3 (1.6–3.4s): the branded client report rises from behind the baseline on a
slow-fast-slow nudge and seats in the upper two-thirds — the agency's own green brand rule at
its head, the channel table legible, the "All 7 figures checked against source data" footer
line visible. Asymmetric, report occupying ~62% of frame.
Scene 4 (3.4–5.0s): "Nothing goes out until you approve it." writes in beside the report in
ink, and everything holds still. The baseline rule shortens toward centre, preparing the lockup.

## Frame 6 — Report Desk

- src: compositions/frames/06-lockup.html
- scene: the mark draws, the wordmark sets, the promise line holds beneath the rule
- duration: 2.5s
- transition_in: crossfade
- status: outline
- blueprint: titlecard-reveal (Reproduce)
- focal: the Report Desk lockup
- roles: lockup = cutout
- handoff_in: the 1px `line` rule enters at y=70%, x 36%–64%, opacity 1, scale 1, static — it is already the lockup's underline when the frame opens
- rules: svg-path-draw, waterfall-entry

No captured assets — this frame is a typographic lockup.

The lockup lands on the rule that has carried the whole film. Low motion is the payload.

Scene 1 (0.0–0.9s): the square Report Desk mark draws itself on above the inherited rule —
a single stroke outline completing, ink. Centered.
Scene 2 (0.9–1.6s): "Report Desk" sets beside the mark in Archivo display, ink, one
restrained slide-up.
Scene 3 (1.6–2.5s): "It writes your monthly client reports, double-checks its own numbers,
and waits for your approval." waterfalls in beneath the rule in `text-secondary` at reading
size, then the whole lockup holds entirely still to the last frame. No drift, no breathing —
the film ends as composed as it began.
