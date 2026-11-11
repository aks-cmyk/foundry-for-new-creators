# Demo — 90-second script

**Length:** under 90 seconds. **Show the plugin working, don't describe it.**
Record the dashboard + one Hermes chat turn. No slides.

## Setup (before recording)

- `make demo` — seeded ledger + dashboard at `dashboard/index.html`.
- Open the dashboard in a browser, Proofing Table tab visible.
- Have the X post ready to quote only if asked — do not read it aloud.

## Script (with timings)

| Time | Say (approx.) | Show |
|---|---|---|
| 0–10s | "Creator tools forget. Foundry remembers — five bots, one memory." | Dashboard: Identity Card. Point at it: one card, shared by all five bots. |
| 10–35s | "Lookout brings back sourced evidence. Scribe drafts from it — nothing without a citation." | Evidence Card (2 sources) → Draft v1 on the Proofing Table. Point at the citations under the draft. |
| 35–60s | "Here's the human moment. Sharper hook." | Click **Tweak**, type "sharper hook". Scribe returns v2. Show v1 → v2 diff and the Revision Card that stored the feedback. |
| 60–80s | "Scorekeeper says this format worked. Bursar says it made money after costs. Same post, one view." | Scorekeeper tab (verdict: repeat) → Bursar tab (cost, revenue, profit on the same draft). |
| 80–90s | "Five bots, one ledger. Foundry." | Back to Proofing Table, draft v2 (in review — seeded demo data). End card: name + "Hermes Agent Plugin Hackathon". |

## What not to do

- Do not read the whole draft aloud. Show it.
- Do not claim live X / analytics numbers — the seed data is
  labelled `estimated` on the dashboard. Say "seeded demo data"
  if you mention numbers at all.
- Do not show the catalog PR, Typeform, or any submission step —
  the video is the demo, the submission is separate.
- Do not go over 90 seconds. Cut the Bursar partnership tab first
  if you are running long; keep the Tweak → v2 moment at all costs.

## Checklist before recording

- [ ] `make test` green
- [ ] `make demo` renders; all three tabs open; cross-links work
- [ ] Tweak → v2 works in the rendered dashboard (client-side)
- [ ] No real API keys / personal data visible on screen
- [ ] Audio clear; screen text readable at 1080p
