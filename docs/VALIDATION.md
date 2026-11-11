# Validation — Hermes CLI v0.23.0

Run 2026-11-06 against the installed Hermes (see `docs/RESEARCH.md`
for the install record). Full logs:
`hidden_files/validation-2026-11-06.log` (git-ignored bookkeeping).

Isolated `HERMES_HOME` used for every invocation:
`hidden_files/hermes-home` — the real `~/.hermes` was never touched.

## Environment

- Hermes Agent **v0.23.0** (2026.9.24) · stable · local `2bd378ed1b8d`
  (`hermes --version`; note: `hermes version` is NOT a command —
  `hermes: 'version' is not a hermes command`)
- Python **3.14.9** · OpenAI SDK 2.54.0 · "Up to date"
- Install: `.hermes-src/` (git checkout), launcher `~/.local/bin/hermes`

## `hermes plugins validate <foundry> --install-deps` — PASS (exit 0)

All 15 checks green, before and after the fix:

```
✓ manifest — plugin.yaml parses
✓ manifest fields — name, version, description present
✓ requires_hermes — spec '>=0.21.5' parses
✓ config schema — shape valid
✓ requires_env — all entries UPPER_SNAKE
✓ oauth — not declared
✓ loadable — entry: __init__.py
✓ python dependencies — none declared
✓ capability probe — register() ran in isolation
✓ declared tools — matches registrations
✓ declared hooks — matches registrations
✓ declared middleware — matches registrations
✓ built-in tool collisions — no collisions
✓ security scan — safe
✓ no core override — no runtime rebinds of Hermes core
◆ Isolation — runs in the plugin host (plugins.isolation: host)
  · dashboard backend API is served through the plugin host (buffered responses)

Validation passed.
```

## `hermes plugins doctor <foundry>` — FAIL then PASS

### First run — FAILED (real bug found)

```
Plugin Doctor:
  ERROR: Plugin registration failed: PluginContext.register_tool()
  missing 2 required positional arguments: 'schema' and 'handler'
  registrations: 0 tool(s), 0 hook(s)
```

Root cause: the real signature in v0.23.0
(`hermes_cli/plugins.py:463`) is

```python
def register_tool(self, name: str, toolset: str, schema: dict, handler: Callable, ...)
```

`toolset` is a **required** positional argument. Foundry called
`ctx.register_tool(name=…, schema=…, handler=…)` without it, so the
call raised `TypeError`; the scaffold's fallback
`ctx.register_tool(schema, handler)` was also wrong (2 args, still
missing `toolset`) and the exception propagated out of `register()`.
Bundled `google_meet` uses `toolset="google_meet"` — Foundry now uses
`toolset="foundry"`.

**Lesson: `validate` is NOT a substitute for `doctor`.** Validate
probes `register()` with a lenient stub (`RecordingContext.register_tool`
accepts anything, `hermes_cli/plugin_validate.py:232`), so it passed
with 0 tools actually registered. Doctor runs the real
`PluginContext` and caught it. Both must be run; doctor is the one
that proves registration works.

Note: doctor exits **0** even when registration fails — read its
output, do not trust the exit code.

### Second run (after fix) — PASS (exit 0)

```
Plugin Doctor:
  manifest: foundry 0.1.0 (standalone)
  OK: runtime discovery, manifest parsing, import, and registration passed
  registrations: 8 tool(s), 0 hook(s)
```

## What validate/doctor do NOT cover

- **The dashboard extension** (`foundry/dashboard/`): neither check
  mentions it. Verified separately at module level (2026-11-06):
  `dist/index.js` parses clean under Hermes's own Node 26.12.1
  (`node --check`); `plugin_api.py` imports under FastAPI 0.162.0,
  builds a router with `GET /cards` and `GET /summary`, reads the 9
  seeded cards and returns the summary. A live load under
  `hermes dashboard` is still **UNVERIFIED** — it needs a running
  gateway/model, which this task cannot set up (no credentials).
- **Live LLM calls**: doctor runs `register()` only, never the tool
  handlers, so the live Scribe path (`ctx.llm.complete`) is wired and
  unit-tested with a fake LLM, but no real completion has run.

## Fixes made (this validation round)

1. `foundry/__init__.py`: `register_tool` now passes
   `toolset="foundry"`; removed the wrong fallback; binds ctx via
   `tools.bind_ctx(ctx)` so handlers can reach `ctx.llm`.
2. `foundry/bots.py`: `scribe_revise(..., llm_complete=None)` — uses
   the host LLM when a callable is supplied, else the rule-based
   rewrite; records `"generation": "llm" | "rule-based"` on the card.
3. `foundry/tools.py`: `bind_ctx(ctx)` + `_llm_complete()` helper
   (`ctx.llm.complete(messages, temperature=0.7, max_tokens=800,
   timeout=120, purpose="foundry.scribe_revise")`, failures → `None`
   → rule-based fallback, never raises).
4. `tests/test_smoke.py`: 5 new checks (23 total) — fake-LLM revise,
   LLM-failure fallback, and a FakeCtx that **requires** `toolset`
   (guards the doctor bug).

## Re-verification after fixes — first round (2026-11-06)

- Smoke test: **23/23 PASS**
- `make demo`: renders `dashboard/index.html` (3 tabs), exit 0
- `hermes plugins validate`: PASS
- `hermes plugins doctor`: PASS, 8 tools registered

## Second round — ledger + feedback + Desktop (2026-11-06)

Full log: `hidden_files/validation-2026-11-06b.log`.

### Fixes
1. **Ledger location** (`foundry/storage.py`, new): the ledger now lives
   at `plugin_db("foundry")` → `<hermes home>/plugin-data/foundry/data.db`,
   shared by tool handlers and the dashboard backend through one
   resolution (test override + standalone fallback to the local demo DB).
   Verified in the VM: with the isolated `HERMES_HOME`,
   `storage.db_path()` resolves to
   `hidden_files/hermes-home/plugin-data/foundry/data.db` and
   `storage.connect()` creates + seeds it with the 9 demo cards.
   **Caution learned:** running a check under Hermes's own venv python
   *without* `HERMES_HOME` set resolves to the real `~/.hermes` and
   created a seeded `~/.hermes/plugin-data/foundry/data.db` — removed
   afterwards. Always run Hermes-venv checks with the isolated
   `HERMES_HOME` set.
2. **Dashboard buttons**: `POST /feedback` added to `plugin_api.py`
   (writes a real Revision Card; tweak returns a revised draft,
   rule-based in the dashboard process — no `ctx.llm` is bound there).
   `dist/index.js` Approve/Tweak/Reject now call it via
   `SDK.fetchJSON` (POST shape verified from the bundled kanban plugin:
   `fetchJSON(url, { method: "POST", headers: {...}, body: JSON.stringify(...) })`).
   Router registration verified under Hermes's venv python
   (FastAPI 0.133.1): routes are `GET /cards`, `GET /summary`,
   `POST /feedback`. Note: system Python has no FastAPI, so the smoke
   test exercises the endpoint functions directly and checks the router
   only when it exists.
3. **Desktop half** (`foundry/desktop/plugin.js`): single ESM file,
   imports only `@hermes/plugin-sdk`, `react`, `react/jsx-runtime`;
   registers a `/foundry` route + sidebar nav + palette command,
   mirroring the web board over the same backend via `ctx.rest`.
   Verified: parses under Hermes's Node 26.12.1; installed-source
   desktop surface lint clean (`desktop_surface_hits` = []);
   `desktop_source()` resolves `foundry/desktop`;
   `check_desktop_tree` = None. Ships opt-in (`defaultEnabled: false`).
4. **Dropped `foundry_dashboard_render` tool** (8 → 7 tools): it did
   `from scripts.render_dashboard import render`, but `scripts/` is
   not inside an installed plugin folder. Static rendering for demos
   still lives in `scripts/render_dashboard.py` (`make demo`).

### Re-verification after these fixes
- Smoke test: **34/34 PASS** (system Python 3.12 and Hermes venv
  Python 3.14 — the storage-resolution check is hermetic across both).
- `make demo`: renders, exit 0.
- `hermes plugins validate`: **PASS, 16 checks** (was 15 — new check
  "desktop surface — stays inside the plugin SDK surface" ✓; "loadable"
  now lists `__init__.py, desktop/plugin.js`).
- `hermes plugins doctor`: **PASS, 7 tools registered**, 0 hooks.

### Still NOT covered by validate/doctor
- Live load of the web dashboard under `hermes dashboard` and of the
  Desktop half in a live `hermes desktop` — neither runs in this
  workspace. Both need Amit's Mac Studio.
- Live `ctx.llm` completion against a real model (wired, fake-LLM
  tested only).

## Third round — Mac Studio adoption + fixture fixes (2026-11-11)

Adoption commit `d257c2b` (candidate `bde3c03`); fixture fixes commit
`4948d7f`. Full logs: `hidden_files/adoption-2026-11-10/`.

### What changed
- Adopted 7 files from the Mac Studio return: `foundry/bots.py`
  (kind checks in `scribe_draft`), `foundry/tools.py` (approve
  fail-closed, authorship `human` → `unverified`),
  `foundry/memory.py` (new — role-bound SQLite memory-candidate
  store, unintegrated), `tests/test_integrity.py` (4 methods),
  `tests/test_memory.py` (5 methods),
  `docs/APPROVAL_CHECKPOINT.md`, `docs/SCOPED_MEMORY_CHECKPOINT.md`.
- Must-fix items (same work, commit `4948d7f`): seed `draft-002`
  `approved` → `in_review`, `revision-001` authorship → `unverified`;
  Approve buttons disabled with an honest label on web, Desktop, and
  static render; `plugin.yaml` description + tool schemas stop
  claiming human approval; docs/render wording corrected; 3 new
  fixture regression tests.

### Re-verification on the fixed tree
- `python3 -I tests/test_memory.py`: **5/5 OK**
- `python3 -I tests/test_integrity.py`: **7/7 OK** (4 adopted +
  3 new fixture tests)
- `python3 -I tests/test_smoke.py`: **34/34 PASS**
- `hermes plugins validate <copy>/foundry --json`: **PASS, 16/16,
  0 warnings** — run on a copy of the plugin tree under
  `hidden_files/adoption-2026-11-10/validate-copy/` (copy deleted
  after; logs kept). Lesson from the review: the capability probe can
  write a demo DB into the probed tree — always validate a copy and
  clean the tree after. No probe DB appeared in the copy this run.
- `hermes plugins doctor <copy>/foundry --ci`: **PASS, 7 tools,
  0 hooks**
- Environment: system Python 3.12.3; Hermes v0.23.0; isolated
  `HERMES_HOME` (`hidden_files/hermes-home`); real `~/.hermes`
  untouched (`plugin-data` still empty, mtime Nov 6).
- Also verified: `make demo` re-renders from the fixed seed —
  `dashboard/index.html` shows `v2 (in_review)` and the disabled
  Approve label, with no `approved` wording.

### Still NOT covered after adoption
- Live Scribe via `ctx.llm`: VERIFIED on Mac Studio Nov 10, 2026 (draft-003, `generation: "llm"`). Live web dashboard load: blank page on first Mac Studio run; root cause found in the host source and fixed (Tabs render-prop — see "Fourth round" below); live re-test done Nov 10, 11:15 PM — tabs render (three tabs at the time). Redesign + Brand tab confirmed live Nov 11 — Amit: all four tabs render. Live Desktop load — wired and statically verified only.
- **Trusted human approval — explicitly NOT provided.** Approval is
  disabled, not implemented. See `docs/APPROVAL_CHECKPOINT.md`.
- **Scoped memory as a product capability** — module only; nothing
  imports it, `retrieve()` returns `[]` by design, no promotion, no
  host integration. Do not present it as a shipped feature.
- **Licensing/provenance** — MIT claimed in one metadata field
  (`plugin.yaml`); no LICENSE file, no copyright holder. Amit's
  decision, still open.
- Typeform fields — still unverified (JS-rendered form).
- `requires_hermes >=0.21.5` — docs' example floor, not a bisected
  minimum.

## Fourth round — dashboard Tabs fix (2026-11-11)

Symptom (Mac Studio, Nov 10, 2026): `hermes dashboard` → Foundry tab
loads a blank page; page HTML only `<div id="root"></div>`, no console
errors seen. The tab itself registered (manifest read, route exists).

Root cause (host source, `.hermes-src`): the host's `Tabs`
(`@nous-research/ui`, `web/src/plugins/registry.ts`) is a render-prop
component — `children(active, setActive)` — while
`foundry/dashboard/dist/index.js` passed elements as children
(Radix-style, assumed from the component names; the official dashboard
guide lists the names but shows no Tabs usage example). First render
throws `children is not a function`, which unmounts the whole dashboard
app — hence blank page + empty root. Every other component used
(Card, Button, Badge, TabsList, TabsTrigger) matches the host exactly.

Fix: `Tabs` now uses the render-prop form (`defaultValue: "proofing"`);
triggers get `active` + `value`. The component's own tab state still
drives which body renders. Static render unaffected (plain HTML).

Verification (VM, Hermes v0.23.0, 2026-11-11):
- Old code reproduced the exact throw in a server-side render against
  the REAL host UI components (`RENDER THREW: children is not a
  function`); fixed code renders (`RENDER OK`, Proofing Table trigger
  active). Harness `/tmp/foundry-dashboard-ssr.mjs` (Node 24,
  React 19.3.0, real `@nous-research/ui` dist). Effects don't run in
  SSR, so this proves the first-render path; the data-loaded branch
  uses the same Tabs element plus plain Card/Button/Badge.
- `tests/test_memory.py` 5/5; `tests/test_integrity.py` 7/7; smoke
  34/34; `hermes plugins validate` PASS 16/16;
  `hermes plugins doctor` PASS 7 tools, 0 hooks (isolated
  `HERMES_HOME`).
- Server-side chain in the VM: after `hermes plugins enable foundry`
  + rescan, `/api/dashboard/plugins` lists `foundry` and the entry
  serves HTTP 200. Side finding: a not-enabled plugin is absent from
  the manifest list entirely (the isolated home had Foundry "not
  enabled" until this round).
- Live re-test on Amit's Mac Studio: done Nov 10, 11:15 PM — tabs render (three tabs at the time). Redesign + Brand tab confirmed live Nov 11 — Amit: all four tabs render.

### Fifth round — onboarding (foundry_start + Brand tab)

Amit's call, same evening: the interview existed as a function
nobody could call, and the brand was invisible. `foundry_start`
(8th tool, two-step interview → Identity Card), origin marking
(seed/interview/dashboard-edit), draft guard refusing the demo
brand, Brand tab on web + Desktop with a real edit form backed by
POST /brand (new version, dashboard authorship, never "human").
Verified: new tests/test_onboarding.py 14/14; full suite 26/26;
smoke 34/34; validate 16/16; doctor 8 tools; SSR renders all four
tabs incl. the Brand tab. Live check pending on Mac Studio — the
interview needs a live model (see docs/MAC_STUDIO_CHECK.md §6).

### Redesign — vertical card feed (same evening, Amit's call)

After the Tabs fix rendered live, Amit asked for all drafts (not
just the latest), properly formatted buttons, and a vertical card
design like a phone. `foundry/dashboard/dist/index.js` now lists all
drafts newest-first in a vertical stack inside a narrow centered
column (max-width 560px); each card has its own buttons in a flex row
(disabled Approve shows "Approval unavailable", full reason in the
title); feedback is per-draft. Verified by SSR against the real host
UI components with seeded state (2 drafts render, v3 before v2;
score/money tabs render); tests 12/12, smoke 34/34, validate 16/16,
doctor 7 tools. Live re-test pending (single file).

### Sixth round — pre-origin demo fix (`e776ce2`, 2026-11-11)

Amit's existing Mac install seeded identity-001 before origin marking
existed, so its payload has no `origin` field — and the draft guard and
`is_onboarded` treated a missing origin as a real brand. Fix: only
origin `"interview"` or `"dashboard-edit"` counts as a real brand;
missing origin is treated the same as `"seed"` by the guard and by
`is_onboarded`; the Brand tab shows the demo banner and a `(demo)`
label for a missing origin. Regression test added to
tests/test_onboarding.py (14/14). Verified: full suite 26/26; smoke
34/34; validate 16/16; doctor 8 tools, 0 hooks.

### Seventh round — branding (`bd38cf8`, 2026-11-11)

Amit picked Logo D — Constellation. The mark was finalized from the
chosen sheet (deterministic crop, transparent background) as
`foundry/assets/logo-constellation-dark.png` /
`logo-constellation-light.png`, plus dark/light wordmark lockups
(`logo-constellation-wordmark-dark/light.png`). `foundry/README.md`
created (wordmark-light at top, quick start, rule-13 disclosures, MIT
line). The dashboard header was deliberately NOT rebranded
(`dist/index.js` untouched). Verified: full suite 26/26; smoke 34/34;
validate 16/16; doctor 8 tools, 0 hooks.

### Eighth round — interview timeout fix (`9eafe44`, 2026-11-11)

Live check on Amit's Mac: the agent asked all nine interview
questions up front; the turn timed out while he was typing and
nothing was saved. Fix: the skill's step 1 is now an interview
protocol — ask ONE question at a time, in order, never front-load all
nine; complete `foundry_start` as soon as who_you_help is answered
(that writes a real Identity Card immediately, so a dead turn loses
nothing); keep asking one at a time, each complete carrying
who_you_help + all answers so far and writing a new version; on
resume, read the latest Identity Card first and ask only for what's
missing; never treat the seeded demo identity (origin `"seed"`) as
the user's voice. The `foundry_start` begin instruction carries the
same protocol, and the skill's Proofing Table step no longer promises
an approval step (approval is disabled). Verified: full suite 26/26;
smoke 34/34; validate 16/16 (on a copy); doctor 8 tools, 0 hooks
(isolated home re-synced).

### Ninth round — demo labeling (`86b2a24`, 2026-11-11)

Amit's follow-up to the timeout: seeded content should be labeled as
Demo. It was only half-labeled — the demo identity carried origin
`"seed"` and the Brand tab showed a demo banner, but the other eight
seeded cards had no origin at all and plain titles, and
`foundry_ledger_list` hid the origin even where it existed. Fix: every
seeded card is now titled `Demo: …` and carries `"origin": "seed"` in
its payload (`foundry/data/seed.json`); `foundry_ledger_list` returns
`origin` and `demo` per card; the skill states demo cards are sample
data. No dashboard-code change — the Proofing Tables render `d.title`,
so the Demo titles show automatically. `foundry/README.md` gained
"How a cycle flows" and "Demo content" sections; the root README's
stale facts were fixed (four tabs, 8 tools, live Scribe verified).
Known limit: the ledger lives in `plugin_db("foundry")`, which survives
plugin updates — an existing install keeps its old seeded cards (old
titles, no origin); the draft guard and Brand-tab banner still apply
to them. Fresh installs get the labeled seed. Verified: full suite
26/26; smoke 34/34; validate 16/16; doctor 8 tools, 0 hooks.
