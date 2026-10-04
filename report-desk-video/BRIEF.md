---
workflow: product-launch-video
flow: automation
storyboard: no
message: "It catches its own mistakes, and never sends without you"
destination: website-hero
aspect: 1920x1080
language: en
audience: "Owners of 5-50 person UK/US marketing agencies"
length: 30s
angle: trust
---

## Intent

A ~30 second product film for **Report Desk** — an AI agent that writes a
marketing agency's monthly client reports, checks every figure it wrote against
the source data, and waits for a human to approve before anything is sent.

It plays on a one-page site and on LinkedIn, where it runs muted and on
autoplay, so it carries its whole argument visually. The feeling is quiet
confidence: Swiss, editorial, ink on paper. The hero moment is the agent
catching its *own* wrong number and correcting it — that is the proof of
trustworthiness the whole film is built to deliver.

## Assets

- /home/user/content-scraper/docs/screen-dashboard.png — the real product dashboard; reference for the roster/queue beat.
- /home/user/content-scraper/docs/screen-review.png — the real review screen with the fact-check trail; reference for the hero beat.
- /home/user/content-scraper/docs/screen-client-report.png — the real branded client report; reference for the delivery beat.

## Customizations

- Count-up on the "41 figures checked" stat.
- The fact-check loop is the hero beat and gets the film's one real dwell.
- Status colour is rationed: amber #8A5A0B only for "needs you", green #136B3F
  only for "verified". Everything else is ink on paper.

## Notes

- Silent by design (`music: none`, no SCRIPT.md). Not signed in to HeyGen, and
  the local Kokoro/MusicGen engines are missing their dependencies — but the
  destinations autoplay muted, so a silent cut is the correct deliverable, not
  a compromise.
- Explicitly avoid the AI-startup look: no purple/blue gradients, no neon, no
  glassmorphism, no dark-mode-with-glow.
- Numbers shown must match the real product's eval output (41 figures checked,
  6 corrected) — this film must not overstate what was built.
