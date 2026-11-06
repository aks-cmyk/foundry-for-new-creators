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
- `hermes plugins validate` / `hermes plugins doctor` **not run** —
  Hermes CLI is not installed in this workspace (UNVERIFIED).
- `ctx.llm` live drafting, live web research, live X/analytics APIs:
  not implemented in the scaffold (deterministic stubs + seed data).
- Desktop (`desktop/plugin.js`) surface: not built; web dashboard only.
- No catalog PR, no demo video, no Typeform submission.

## [Unreleased]

- Live Scribe via `ctx.llm`; Lookout live search; Scorekeeper/Bursar
  live analytics + money imports; Desktop SDK surface; catalog PR.
