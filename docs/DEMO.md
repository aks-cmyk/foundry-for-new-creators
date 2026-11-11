# Demo — 90-second script

**Length:** under 90 seconds. **Show the plugin working, don't describe it.**
Record the dashboard + one Hermes chat turn. No slides.

Reconciled to v3 (HEAD `e776ce2`, Nov 11, 2026): four dashboard tabs
(Proofing Table, Brand, Inspector, Paymaster); live Smith verified on
Mac Studio (draft-003, `generation: "llm"`). The operative shot list is
`hidden_files/submission-prep/demo-script.md` — this file is its beat
sheet and must match it.

## Setup (before recording)

- `make demo` — seeded ledger + dashboard at `dashboard/index.html`.
- Open the dashboard in a browser, Proofing Table tab visible.
- Have the X post ready to quote only if asked — do not read it aloud.

## Script (with timings)

| Time | Say (approx.) | Show |
|---|---|---|
| 0–10s | "Creator tools forget. Foundry remembers — five bots, one memory." | Brand tab: Identity Card. Point at it: one card, shared by all five bots. |
| 10–35s | "Prospector brings back sourced evidence. Smith drafts from it — nothing without a citation." | Evidence Card (2 sources) → Draft v1 on the Proofing Table. Point at the citations under the draft. |
| 35–60s | "Here's the human moment. Sharper hook." | Click **Tweak**, type "sharper hook". Seeded/static flow shows the v1 → v2 diff and the Revision Card that stored the feedback. Live flow returns draft-003 (v3) — use it only with the corrected Foundry framing (option 1), not the drifted Hermes-plugins wording. |
| 60–80s | "Inspector says this format worked. Paymaster says it made money after costs. Same post, one view." | Inspector tab (verdict: repeat) → Paymaster tab (cost, revenue, profit on the same draft). |
| 80–90s | "Five bots, one ledger. Foundry." | Back to Proofing Table, draft v2 (in review — seeded demo data). End card: name + "Hermes Agent Plugin Hackathon". |

## What not to do

- Do not read the whole draft aloud. Show it.
- Do not claim live X / analytics numbers — the seed data is
  labelled `estimated` on the dashboard. Say "seeded demo data"
  if you mention numbers at all.
- Do not show the catalog PR, Typeform, or any submission step —
  the video is the demo, the submission is separate.
- Do not show the drifted draft-003 wording (Hermes-plugins framing,
  uncited hackathon claim) on screen — it is not in the draft's
  evidence. Use the seeded v1 → v2 moment, or the corrected draft
  once option 1 is applied on the Mac.
- Do not go over 90 seconds. Cut the Paymaster partnership tab first
  if you are running long; keep the Tweak → v2 moment at all costs.

## Checklist before recording

- [ ] `make test` green
- [ ] `make demo` renders; all four tabs open; cross-links work
- [ ] Tweak → v2 works in the rendered dashboard (client-side)
- [ ] No real API keys / personal data visible on screen
- [ ] Audio clear; screen text readable at 1080p
