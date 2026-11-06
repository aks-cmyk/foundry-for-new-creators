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
- Desktop (`desktop/plugin.js`) surface: not built; web dashboard only.
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

## [Unreleased]

- Lookout live search (needs a `ctx` surface or MCP route — none
  verified); Scorekeeper/Bursar live analytics + money imports;
  Desktop SDK surface; catalog PR (needs catalog entry format read +
  a real repo URL for `homepage`); demo video; Typeform submission.
