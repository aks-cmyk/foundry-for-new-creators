# Changelog

All notable changes to Foundry, newest first. Format is
`Keep a Changelog`-style; versions are SemVer.

## [0.1.0] — 2026-11-06 — MVP scaffold

### Added
- Project repo (git, local only — nothing pushed, no remote).
- `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/LEDGER.md`,
  `docs/DEMO.md`, `docs/RESEARCH.md`.
- `foundry/` native Hermes plugin skeleton: `plugin.yaml` (manifest v2),
  `__init__.py` (`register(ctx)`), `schemas.py`, `tools.py`,
  `ledger.py` (SQLite shared ledger), `bots.py` (five bots, deterministic MVP).
- `foundry/dashboard/` web-dashboard extension: `manifest.json`,
  `dist/index.js` (IIFE, SDK React), `dist/style.css`, `plugin_api.py`
  (FastAPI routes at `/api/plugins/foundry/`).
- `foundry/skills/foundry-creator/SKILL.md`.
- Seeded demo data (`foundry/data/seed.json`): 1 Identity Card,
  1 Evidence Card, 2 Draft Cards (v1/v2), 1 Performance Card,
  1 Money Card, 1 seeded brand-partnership deal.
- `scripts/seed.py`, `scripts/render_dashboard.py`, `scripts/demo.py`;
  `Makefile` (`test`, `demo`, `seed`, `clean`); `tests/test_smoke.py`.
- Static dashboard render (`dashboard/index.html`, generated, git-ignored)
  with three tabs: Proofing Table / Scorekeeper / Bursar.

### Verified
- Smoke test passes locally (Python 3.12, stdlib only, no network):
  ledger round-trip, bot loop, dashboard render.
- Plugin format, dashboard format and catalog rules copied from the
  official Hermes docs read 2026-11-06 — see `docs/RESEARCH.md`.

### Known gaps (not yet done)
- `ctx.llm` live completion never run against a real model (wired +
  unit-tested with a fake LLM only); live web research, live
  X/analytics APIs: not implemented (deterministic stubs + seed data).
- Live dashboard load under `hermes dashboard`: not run.
- Desktop (`desktop/plugin.js`) surface: not built at 0.1.0; web dashboard only. (Built in 0.1.2 — see below.)
- No catalog PR, no demo video, no Typeform submission.

## [0.1.1] — 2026-11-06 — Hermes CLI install + validation + live Scribe wiring

### Added
- Hermes CLI installed (official route) in the workspace:
  **v0.23.0**, Python 3.14.9 (`.hermes-src/`, isolated
  `hidden_files/hermes-home/`; git-ignored). Install log:
  `hidden_files/install-2026-11-06.log`.
- `docs/VALIDATION.md`: full validate/doctor record.
- Live Scribe: `scribe_revise(..., llm_complete=None)` calls the host
  LLM via `ctx.llm.complete()` when a ctx is bound
  (`tools.bind_ctx(ctx)` in `register()`), with rule-based fallback on
  any failure; revised cards record `"generation": "llm" | "rule-based"`.

### Fixed
- **Doctor caught a real bug: `register_tool()` was called without
  the required `toolset` argument** (real signature in v0.23.0:
  `register_tool(name, toolset, schema, handler)`). Validate's lenient
  stub had passed with 0 tools registered. Fixed by passing
  `toolset="foundry"` and removing the wrong fallback; doctor now
  passes with 8 tools registered. Smoke test's FakeCtx now requires
  `toolset` so this cannot regress silently.

### Verified
- `hermes plugins validate`: PASS (15/15). `hermes plugins doctor`:
  PASS (8 tools, 0 hooks). Smoke test **23/23 PASS** (5 new checks:
  fake-LLM revise, LLM-failure fallback, toolset assertion).
  `make demo` renders, exit 0. Dashboard backend module-checked:
  `dist/index.js` parses under Hermes's Node 26.12.1; `plugin_api.py`
  router serves `/cards` + `/summary` over the 9 seeded cards.
- `ctx.llm` call shape and trust gate verified from installed source
  (`agent/plugin_llm.py`); `ctx.register_skill` signature verified
  (`hermes_cli/plugins_content.py`); **no `ctx` web-search surface
  exists in v0.23.0** — Lookout stays agent-supplied.

## [0.1.2] — 2026-11-06 — Ledger fix + feedback buttons + Desktop half

### Fixed
- **Ledger location bug: the ledger no longer lives inside the plugin
  folder.** New `foundry/storage.py` resolves it to
  `plugin_db("foundry")` → `<hermes home>/plugin-data/foundry/data.db`
  (survives update/remove, follows the active profile), shared by tool
  handlers and the dashboard backend through one resolution, with a
  test override (`tools.set_db_path()`) and a standalone fallback to
  the local demo DB. First use seeds the 9 demo cards. Verified in the
  VM with the isolated `HERMES_HOME`.
- **Dashboard Approve / Tweak / Reject buttons were `alert()` stubs.**
  New `POST /feedback` in `plugin_api.py` writes a real Revision Card
  (tweak returns a revised draft, rule-based in the dashboard process);
  `dist/index.js` buttons now call it via `SDK.fetchJSON`. Same
  endpoint serves the Desktop half.
- **Dropped `foundry_dashboard_render` tool (8 → 7 tools).** It did
  `from scripts.render_dashboard import render`, but `scripts/` is not
  inside an installed plugin folder, so the tool failed in a live
  install. Static rendering for demos still lives in
  `scripts/render_dashboard.py` (`make demo`).

### Added
- **Desktop GUI half** (`foundry/desktop/plugin.js`): single ESM file
  per the Desktop Plugin SDK ("One package, both SDKs") — `/foundry`
  full page + sidebar nav + palette command, mirroring the web board
  (Proofing / Score / Money) over the same backend via `ctx.rest`.
  Ships opt-in (`defaultEnabled: false`). Verified: parses under
  Hermes's Node 26.12.1; desktop surface lint clean; `hermes plugins
  validate` now passes 16 checks including the desktop surface check.
  Live Desktop load still UNVERIFIED — needs Amit's Mac Studio.

### Verified
- Smoke test **34/34 PASS** (system Python 3.12 and Hermes venv
  Python 3.14). `hermes plugins validate`: PASS (16 checks).
  `hermes plugins doctor`: PASS (7 tools, 0 hooks). `make demo`
  renders, exit 0. FastAPI router verified under Hermes's venv
  (FastAPI 0.133.1): `GET /cards`, `GET /summary`, `POST /feedback`.
  Full log: `hidden_files/validation-2026-11-06b.log`.

## [Unreleased]

### Branding — Constellation logo — 2026-11-11 (Amit's pick)

Amit picked Logo D — Constellation (five dots joined by one rising
line: the shared memory connecting five bots) over the earlier
anvil/bars rounds, which he called too basic and uninteresting.
Assets in `foundry/assets/`: `logo-constellation-dark.png` /
`-light.png` (transparent-background marks, cut from the chosen
sheet — no regeneration) and
`logo-constellation-wordmark-dark.png` / `-light.png` (mark +
letterspaced FOUNDRY lockups, for the README and the video title
card). `foundry/README.md` added (closes the catalog pre-PR flag)
with the rule-13 disclosures. Catalog entry `image` now points at
the light mark via raw.githubusercontent.com (owner + SHA filled at
PR time). The dashboard header was deliberately NOT changed — the
verified `dist/index.js` stays untouched on deadline day.

### Onboarding — foundry_start + Brand tab — 2026-11-11 (Amit's call)

Amit's user-flow notes: a first run should offer "foundry start",
the plugin should be invokable, the interview's brand should be in a
dashboard tab (viewable + editable), and onboarding must be complete
— without it the plugin is "just a skill lite". Verified in code
before building: `cartographer_interview` existed but nothing called
it; the only Identity Card was the seeded demo one; the dashboard had
no Brand tab. Built, no shortcuts:
- **`foundry_start` tool (8th tool).** Two steps, one tool: step
  `begin` returns the 9 Cartographer interview questions (ask one at
  a time; only `who_you_help` required); step `complete` with answers
  writes the Identity Card (versioned, supersedes the previous).
  Lists arrive as arrays or comma-separated strings.
- **Origin marking.** Identity payloads carry `origin`: `"seed"`
  (demo data), `"interview"` (foundry_start), `"dashboard-edit"`
  (Brand tab save). `is_onboarded` is true once a non-seed brand
  exists. The seeded identity-001 is marked `"seed"` in seed.json.
  Identities seeded before the origin field existed (no origin at
  all — e.g. a live Mac Studio DB from Nov 10) count as demo too,
  so the guard and the Brand tab treat them the same way.
- **Draft guard.** `foundry_draft_create` refuses the seeded demo
  brand and points at `foundry_start`. Drafting with a real brand
  works unchanged; the demo and the tests call `bots.scribe_draft`
  directly and are unaffected.
- **Brand tab (4th tab, web + Desktop).** Shows the current brand
  (with a demo-brand banner when it is still the seed) and an edit
  form; saving POSTs to a new `/brand` endpoint that merges fields
  and writes a NEW Identity version (`created_by: "dashboard"`,
  origin `"dashboard-edit"` — never "human"). Unknown fields and an
  empty `who_you_help` are rejected.
- **Desktop mirrors it:** Brand tab + the same all-drafts vertical
  stack with per-draft note boxes (the Desktop Proofing Table had
  the same latest-only shape as the web one).
- `plugin.yaml` description leads with "say 'foundry start'";
  `docs/SPEC.md` (§3 rule 5, §5.2, §7) and `docs/ARCHITECTURE.md`
  updated; smoke test's tool count 7 → 8.

#### Verified (VM, Hermes v0.23.0, Python 3.12, 2026-11-11)
- New `tests/test_onboarding.py`: 13 tests — begin/complete,
  required-field and list handling, onboarded state, draft guard
  (refuses demo brand, allows interview brand), Brand save (new
  version, old untouched, dashboard authorship, rejects empty
  who_you_help / unknown fields / wrong kind), seed marked demo.
- Full suite: unittest 25/25 (12 + 13 new); smoke 34/34;
  `hermes plugins validate` PASS 16/16; `hermes plugins doctor`
  PASS 8 tools, 0 hooks.
- SSR render against the real host UI components: proofing (both
  drafts, newest first), **brand tab (v2 interview card, all fields,
  Edit button)**, score, money — all render.
- Live check still pending on Amit's Mac Studio: the interview
  itself needs a live model (the VM has none), plus the Brand tab
  edit in the real dashboard. Steps added to
  `docs/MAC_STUDIO_CHECK.md` (§6).

### Dashboard redesign — vertical card feed — 2026-11-11 (Amit's call)

After the Tabs fix, the live dashboard rendered on Mac Studio (three
tabs show). Amit's feedback: the Proofing Table showed only the latest
draft ("shouldn't it show all?"), the approval buttons were not
formatted properly, and a vertical card design mimicking a phone would
be nicer. Redone in `foundry/dashboard/dist/index.js` (same file):
- Proofing Table lists **all** drafts as a vertical card stack,
  newest first (feed order); each card carries its own buttons.
- Buttons laid out in a flex row with gaps; the disabled Approve
  button's visible label is short ("Approval unavailable") with the
  full reason in the title tooltip.
- The page is a narrow centered column (max-width 560px) — a
  phone-like feed; draft text wraps (`pre-wrap`) inside it.
- Feedback is per-draft now (`sendFeedback(draftId, ...)`); each
  card's Tweak/Reject acts on its own draft.
- Scorekeeper/Bursar tabs use the same vertical stack.

#### Verified (VM, Hermes v0.23.0, Python 3.12, 2026-11-11)
- SSR render against the REAL host UI components, state seeded with
  2 drafts + 1 performance + 1 money card: proofing renders both
  drafts, v3 before v2; score and money tabs render. Harness
  `/tmp/foundry-dashboard-ssr.mjs`.
- `tests/test_memory.py` 5/5; `tests/test_integrity.py` 7/7; smoke
  test 34/34; `hermes plugins validate` PASS 16/16;
  `hermes plugins doctor` PASS 7 tools, 0 hooks.
- Live re-test on Amit's Mac Studio pending (single file, same as
  the Tabs fix delivery).

### Dashboard Tabs fix — 2026-11-11 (live blank-page root cause)

First live run on Mac Studio (Nov 10, 2026): the Foundry tab loaded a
blank page, empty `#root`, no console errors seen. Root cause, found by
reading the host source (`web/src/plugins/registry.ts` + the real
`@nous-research/ui` Tabs): the host's `Tabs` is a **render-prop**
component — `children(active, setActive)` — while
`foundry/dashboard/dist/index.js` passed elements as children, the
Radix-style shape. That throws `children is not a function` on first
render and unmounts the whole dashboard app. The official dashboard
guide lists the component names but shows no Tabs usage example; the
Radix shape was assumed, wrongly. (The SDK globals and every other
component used — Card, Button, Badge, TabsList, TabsTrigger — match the
host exactly; only `Tabs`' children contract differed.)

#### Fixed
- `foundry/dashboard/dist/index.js`: `Tabs` now uses the render-prop
  form (`defaultValue: "proofing"`, `children(active, setActive)`);
  triggers get `active` + `value` props. The component's own tab state
  still drives which body renders. The static render
  (`scripts/render_dashboard.py`) is unaffected — plain HTML, no SDK Tabs.

#### Verified (VM, Hermes v0.23.0, Python 3.12, 2026-11-11)
- Old code reproduced the throw in a server-side render against the
  REAL host UI components: `RENDER THREW: children is not a function`.
  Fixed code renders: `RENDER OK` (Proofing Table trigger active).
  Harness: `/tmp/foundry-dashboard-ssr.mjs` (Node 24, React 19.3.0,
  real `@nous-research/ui` dist).
- `tests/test_memory.py` 5/5; `tests/test_integrity.py` 7/7; smoke
  test 34/34; `hermes plugins validate` PASS 16/16;
  `hermes plugins doctor` PASS 7 tools, 0 hooks (isolated
  `HERMES_HOME`, real `~/.hermes` untouched).
- Server-side chain confirmed in the VM: plugin enabled → manifest
  list includes `foundry` → entry serves HTTP 200. (Side finding: an
  un-enabled plugin is absent from `/api/dashboard/plugins` entirely
  — the isolated home had Foundry "not enabled" until now.)
- Live re-test on Amit's Mac Studio still pending (fresh zip v3).

### Adopted 2026-11-11 — Mac Studio integrity + scoped-memory work (candidate bde3c03)

Adopted as `d257c2b`; fixture fixes as `4948d7f`. The Mac Studio
Hermes found real flaws (review verdict: ADOPT WITH FIXES —
`hidden_files/mac-studio-return-2026-11-10/REVIEW_VERDICT.md`); the
Mac git history was NOT adopted (different lineage + a local author
identity that must never go public).

#### Added
- `foundry/memory.py`: role-bound SQLite memory-candidate store
  (tested module; **NOT integrated** — nothing imports it,
  `retrieve()` returns `[]` by design; do not present as a feature).
- `tests/test_integrity.py` (4 methods), `tests/test_memory.py`
  (5 methods); `docs/APPROVAL_CHECKPOINT.md`,
  `docs/SCOPED_MEMORY_CHECKPOINT.md`.

#### Fixed
- **Wrong-kind draft inputs rejected.** `scribe_draft` now checks
  the evidence/identity cards are of the right kind before any write.
- **Spoofable approval closed.** All three approve routes
  (`foundry_draft_approve`, `foundry_draft_feedback` with
  `feedback_type="approve"`, dashboard `POST /feedback`) fail closed
  with no writes; feedback authorship is `unverified`, never `human`.
- **Seed fixture honesty.** `draft-002` status `approved` →
  `in_review`; `revision-001` author/created_by `human` →
  `unverified`. Regression tests added (seed has no `approved`
  status; render labels the fixture as seeded demo-only).
- **Approve buttons disabled** with an honest label ("Approval
  unavailable — trusted human review not wired") on the web
  dashboard, Desktop app, and static render.
- **`plugin.yaml` description + tool schemas stop claiming human
  approval.** Approval is disabled, not implemented — no trusted
  human review channel exists yet.

#### Verified (VM, Hermes v0.23.0, Python 3.12.3, 2026-11-11)
- `tests/test_memory.py` 5/5; `tests/test_integrity.py` 7/7 (4
  adopted + 3 new fixture tests); smoke test 34/34.
- `hermes plugins validate` (run on a copy — the capability probe
  can write a demo DB into the plugin tree): PASS, 16/16, 0 warnings.
- `hermes plugins doctor`: PASS, 7 tools, 0 hooks.
- Full logs: `hidden_files/adoption-2026-11-10/`.

#### Known gaps (not yet done)
- **LICENSE / copyright holder: DECIDED Nov 10, 2026** — MIT,
  Copyright (c) 2026 Amit Srivastava; LICENSE file added (commit
  `8279a3c`).
- Live Scribe via `ctx.llm`: VERIFIED on Mac Studio (draft-003, `generation: "llm"`, Nov 10, 2026); the draft-003 correction (back to Foundry framing) is pending Amit's pick. Live web dashboard load: blank page on first run, root cause found + fixed (Tabs render-prop, see top of this section) — live re-test pending. Live Desktop load: still unverified.
- Trusted human approval: explicitly not provided (see above).
- Lookout live search (needs a `ctx` surface or MCP route — none
  verified); Scorekeeper/Bursar live analytics + money imports;
  catalog PR (needs catalog entry format read + a real repo URL for
  `homepage`); demo video; Typeform submission.
