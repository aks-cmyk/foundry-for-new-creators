# Foundry — Build Spec

**Version:** 0.1.0 (MVP scaffold) — 2026-11-06
**Hackathon:** Hermes Agent Plugin Hackathon, submissions due
**5 PM EST Wed Nov 11, 2026 (2 PM PST)**
**Status:** Spec + scaffold. Not a submission. No PR, no demo video,
no Typeform — those need Amit's go-ahead.

## 1. Product

Foundry is a Hermes Agent plugin for creators. One plugin, five bots,
one shared memory ledger, one dashboard.

A creator's real job is not "write a post". It is: know who you are,
find what is worth saying, draft it in your voice, learn what landed,
and know whether it made money. Every tool that does one of those
forgets the others. Foundry keeps all five in one place, and — the
point — the five bots share the same memory, so each one learns from
the others instead of starting cold every time.

**Default platform / content type (MVP): X threads.** Chosen because
the hackathon entry itself is an X post + demo video, the audience is
on X, and a thread is a bounded, demoable unit. Other platforms are
backlog, not MVP.

**Non-goals for the hackathon:** auto-posting, auto-sending, auto-buying.
A human approves anything public. Paymaster gives no tax advice and files
nothing. Foundry never invents a fact, a number, a quote or a source.

## 2. Positioning — not Eden

Foundry must not sound like Eden (Dan Koe) or like the Grok Bot
income-streams guide, even though both informed the idea.

| Eden / Grok guide language | Foundry language |
|---|---|
| garden, brand board | workshop, ledger, foundry |
| creative team, one-person creative team | crew, stations, bots |
| intellectual signature | Identity Card |
| brand strategist / content strategist | Patternmaker / Prospector |
| content calendar / scheduling | Proofing Table, Inspector |

Design language: workshop + ledger. Dark, utilitarian, cards with
provenance (who wrote this, from what source, when, what version).
No garden imagery, no "grow your brand" copy.

The differentiator, in one sentence: **the bots talk to each other
through a shared, versioned ledger — not through chat handoffs —
and the money side is a first-class citizen, not an afterthought.**

## 3. The crew

| Bot | Job | Reads | Writes |
|---|---|---|---|
| **Patternmaker** | Interview bot. Maps identity, niche, audience, voice, what you will not say. | Past Identity Cards, top Performance Cards | Identity Card (versioned) |
| **Prospector** | Scout. Sourced research in the niche. | Identity Card, past Performance Cards (what worked) | Evidence Card (with source links) |
| **Smith** | Writer. Drafts only from cited Evidence Cards. | Identity Card, Evidence Card, Revision Cards | Draft Card (v1, v2, …) |
| **Inspector** | Manager. Analytics: what landed, repeat / drop. | Draft Card, Performance Card history | Performance Card |
| **Paymaster** | Business ops. Costs, profit per post/client, partnerships, tax tracking. | Draft Card, Performance Card, deal records | Money Card, Partnership record, Tax record |

Rules that make the crew a system, not a list:

1. **Smith cannot draft without citing an Evidence Card.** A claim
   with no source is cut, not hedged.
2. **Feedback is a card, not a chat message.** Tweak / Reject on
   the Proofing Table writes a Revision Card, linked to the Draft
   Card. Smith reads Revision Cards before writing v2. Approve is
   disabled — the approve tool and the approve feedback route error
   before writing anything, so no Revision Card is ever written for
   an approval.
3. **Performance and money write back.** Inspector and Paymaster write
   Performance / Money Cards linked to the Draft Card. Prospector reads
   them next cycle and avoids dead angles; Smith reads them and
   repeats winning formats.
4. **A human is the editor.** Drafts are drafts until a human approves
   them on the Proofing Table. Nothing posts itself. (Currently
   disabled — 2026-11-11: the approve routes fail closed until a
   trusted human review channel exists; see
   `docs/APPROVAL_CHECKPOINT.md`.)
5. **Onboarding is the front door, not a doc.** A new user says
   "foundry start": Patternmaker asks nine questions (who you help,
   audience, story, pillars, beliefs, what you will never say, voice
   examples, words you never use, mission — only the first is
   required) and writes the Identity Card. Until a real brand exists,
   Smith refuses to draft in the seeded demo brand's voice. The
   brand is visible and editable on the Brand tab. Without this the
   plugin is a skill with a dashboard — the interview is what makes
   it a product. The interview runs one question at a time, in order,
   never front-loaded: the agent completes `foundry_start` as soon as
   the first question (who you help) is answered, which writes a real
   Identity Card immediately, so a dead turn loses nothing; each
   further answer completes again with who_you_help + all answers so
   far and writes a new version. On resume, the agent reads the
   latest Identity Card first and asks only for what's missing.
   (2026-11-11: fixed after a live check timed out mid-interview
   with nothing saved — see `docs/CHANGELOG.md`, interview timeout
   fix.)

## 4. Shared ledger — summary

Full field-by-field model: `docs/LEDGER.md`.

One SQLite database, six card kinds, all versioned, all with provenance:

- **Identity Card** — who you help, story, pillars, beliefs, what
  you're against, voice rules, words you never use.
- **Evidence Card** — topic, sources (≥2, with links), what is confirmed,
  what is not.
- **Draft Card** — platform, format, text, evidence links, status
  (`draft` / `in_review` / `rejected` / `posted`; `approved` is
  disabled — approval is disabled, so no draft can ever reach that
  status), version, supersedes.
- **Revision Card** — feedback type (`approve` / `tweak` / `reject`),
  note, author (unverified — feedback is never recorded as human),
  linked draft, applied in v(n+1) or not.
- **Performance Card** — views, likes, reposts, replies, saves, and
  the Inspector verdict: repeat / drop / retry-differently.
- **Money Card** — costs (model/tool/time), revenue, profit, per post
  and per client; linked Partnership and Tax records.

Storage: in Hermes, `plugin_db("foundry")` (SQLite, WAL) via
`plugins.plugin_storage` — see `docs/ARCHITECTURE.md`. In this
scaffold, a local SQLite file (`data/foundry.db`, regenerated from
`foundry/data/seed.json`). Never store state in the plugin directory.

## 5. Surfaces — one dashboard shell, four tabs

One web-dashboard extension (`foundry/dashboard/`, manifest +
IIFE bundle + FastAPI backend at `/api/plugins/foundry/`).
One shell, four tabs, all reading the same ledger:

### 5.1 Proofing Table (primary surface)

- One card per draft, in its real format (X thread, numbered).
- Under each draft: its Evidence Card (sources), its Money Card
  (cost so far), its version history (v1 → v2, what changed and why).
- Feedback actions only: **Approve** (disabled — the button is
  disabled with an honest label, and the approve tool errors before
  writing anything) / **Tweak** (one-line note) / **Reject**
  (reason required). Optional inline edit.
- On Tweak/Reject: Smith returns a revised draft; the Revision Card
  is stored; the board updates. No full WYSIWYG editor in the MVP.

### 5.2 Brand tab

- The current Identity Card: who you help, audience, mission,
  story, pillars, beliefs, what you will never say, voice examples,
  words you never use — viewable, and editable in place.
- Editing writes a NEW Identity version (cards are never mutated);
  the old version stays in the ledger. A save from the dashboard is
  recorded as `created_by: "dashboard"`, origin `"dashboard-edit"` —
  the dashboard has no auth channel, so it is never "human" authorship.
- If the current brand is still the seeded demo (`origin: "seed"`),
  the tab says so and points at `foundry start`.

### 5.3 Inspector dashboard

- What worked, by pillar / format / hook. Top posts, underperformers.
- One recommendation per cycle: repeat this, drop that.
- Click a post → its draft, evidence, performance and money in one view.

### 5.4 Paymaster dashboard

- P&L per post, per client, per month. Cost breakdown (model, tools, time).
- Brand-partnership pipeline: pitched → terms → delivered → paid,
  with disclosure flag on every sponsored item.
- Tax ledger: categorised income/expenses, quarterly estimate,
  CSV export. **Tracking only — no advice, no filing.**

Cross-linking is the demo: a post that looks successful in
Inspector but lost money in Paymaster (or vice versa) is a decision
no content-only tool can surface.

## 6. MVP cut vs backlog

### MVP — must work flawlessly by Nov 11, 2 PM PST

- One platform (X), one format (threads), one end-to-end loop:
  Patternmaker (seeded Identity Card) → Prospector (seeded Evidence
  Card) → Smith (Draft v1) → human feedback on Proofing Table →
  Smith (Draft v2) → Inspector (Performance Card) → Paymaster
  (Money Card on the same draft).
- Proofing Table working with seeded data, no live API keys.
- Inspector + Paymaster dashboards as tabs of the same shell, seeded.
- Partnerships/tax as ledger tabs with **one seeded example deal**.
- Plugin loads via `register(ctx)`; tools match `plugin.yaml`;
  `hermes plugins validate` / `doctor` run before any PR (UNVERIFIED
  until run — see RESEARCH.md).

### Post-hackathon backlog (explicitly NOT in the MVP)

- Live Smith via `ctx.llm` (wired, not live-tested); live Prospector web
  search; live X / analytics / money imports.
- Multi-platform (LinkedIn, Substack, YouTube), multi-format.
- Partnership CRM beyond one seeded deal; tax integrations.
- Multi-creator / agency mode (1–3 clients).

## 7. Tools (must match `plugin.yaml` `provides_tools`)

| Tool | What it does |
|---|---|
| `foundry_start` | **Onboarding (front door).** Patternmaker interview: step `begin` returns the 9 questions (ask one at a time); step `complete` with answers writes the Identity Card. Only `who_you_help` is required. Say "foundry start" to run it. |
| `foundry_ledger_list` | List ledger cards, filtered by kind / status |
| `foundry_ledger_get` | Get one card (with its links) by id |
| `foundry_draft_create` | Smith: create a Draft Card from an Evidence Card + Identity Card. Refuses the seeded demo brand — run `foundry_start` first. |
| `foundry_draft_feedback` | Record a Revision Card (tweak / reject) and, on tweak, return a revised draft; approve is disabled (no trusted human review channel yet) |
| `foundry_draft_approve` | Approval is disabled — always errors until a trusted human review channel exists |
| `foundry_scorecard` | Inspector summary for a draft / period |
| `foundry_money_summary` | Paymaster P&L for a draft / client / period |

All handlers return JSON strings, never raise (per the official guide).
(Dropped 2026-11-06: `foundry_dashboard_render` — it imported
`scripts/`, which is not inside an installed plugin folder. Static
rendering for demos lives in `scripts/render_dashboard.py`; the live
boards are the web dashboard and the Desktop half, served by
`plugin_api.py`.)

## 8. 90-second demo script

Full script: `docs/DEMO.md`. Beat sheet:

1. **0–10s — the problem:** "Creator tools forget. Foundry remembers."
   Show the ledger: one Identity Card, shared by all five bots.
2. **10–35s — the loop:** Prospector evidence → Smith draft v1 on the
   Proofing Table. Point at the citations under the draft.
3. **35–60s — the human moment:** Tap "Tweak — sharper hook".
   Smith returns v2 in seconds. Show v1 → v2 diff + Revision Card.
4. **60–80s — the money moment:** Switch to Inspector (this post
   worked) then Paymaster (and it made $X after costs). Same post,
   one view.
5. **80–90s — close:** "Five bots, one memory, one ledger. Foundry."
   Deadline + entry details on screen.

## 9. Submission checklist (needs Amit's go-ahead — do NOT do yet)

- [ ] `hermes plugins validate` passes; `hermes plugins doctor --ci` passes
- [ ] Plugin repo on GitHub (owner repo; this workspace repo is local only)
- [ ] PR to `NousResearch/hermes-agent` adding the catalog entry with a
      full 40-character SHA pin (see RESEARCH.md § Catalog)
- [ ] Demo video < 90s on X, tagging @NousResearch, showing the plugin working
- [ ] Both links submitted via `form.typeform.com/to/FwJLvOln`
- [ ] README disclosure lines: network calls, data read, approvals (per catalog rule 13)

## 10. Day-by-day plan to Nov 11, 2 PM PST

| Day | Focus | Done when |
|---|---|---|
| Thu Nov 5 (evening) | Idea locked; research | Spec v0.1, research notes |
| Fri Nov 6 | Scaffold + spec (this repo) | Smoke test green; dashboard renders from seed |
| Sat Nov 7 | Live Smith + Prospector wiring (stub → `ctx.llm` / search) | Draft loop works with a real model call, not just seed |
| Sun Nov 8 | Dashboard polish; Score/Paymaster tabs real from ledger | All three tabs read live ledger, cross-linked |
| Mon Nov 9 | Hermes validation; fix `validate`/`doctor` findings | Both commands pass; catalog PR draft ready |
| Tue Nov 10 | Demo video (script, record, < 90s); README disclosures | Video reviewed by Amit; PR draft reviewed |
| Wed Nov 11 (AM) | Submit: PR + video + Typeform, **with Amit's go-ahead only** | All three links submitted before 2 PM PST |
| Wed Nov 11, 2 PM PST | Deadline | — |

Times are Pacific. If a day slips, cut backlog first, then Paymaster
depth, then Inspector depth — never cut the Proofing Table loop
or the human-approval gate.
