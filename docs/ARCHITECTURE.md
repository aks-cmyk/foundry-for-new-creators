# Architecture

## Overview

```
                 ┌──────────────────────────────┐
                 │  Hermes Agent (host)         │
                 │  plugin.yaml + register(ctx) │
                 └──────────────┬───────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
     ┌────────▼──────┐  ┌──────▼───────┐  ┌──────▼────────┐
     │  Tools (8)    │  │  Skills      │  │  Dashboard    │
     │  schemas.py   │  │  foundry-    │  │  dashboard/   │
     │  tools.py     │  │  creator     │  │  manifest.json│
     └───────┬───────┘  └──────────────┘  │  dist/index.js│
             │                             │  plugin_api.py│
             └──────────────┬──────────────┘
                            │
                   ┌────────▼────────┐
                   │  Bots (bots.py) │
                   │  Cartographer   │
                   │  Lookout        │
                   │  Scribe         │
                   │  Scorekeeper    │
                   │  Bursar         │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  Ledger         │
                   │  ledger.py      │
                   │  SQLite: cards, │
                   │  links, events  │
                   └─────────────────┘
```

## Components

### Plugin entry (`foundry/__init__.py`)
`register(ctx)` only. It registers the 8 tools (schema + handler)
and the bundled skill. It does no work at import time, opens no
network connections, and never raises on registration failure —
a failed registration is logged and the plugin loads degraded.
This matches the official guide's `register(ctx)` pattern.

### Tools (`foundry/schemas.py`, `foundry/tools.py`)
Schemas are what the model sees; handlers are what runs. Handlers
take `args: dict, **kwargs`, return a JSON string, and catch all
exceptions into error JSON. Tools are thin: they validate arguments,
call a bot function in `bots.py`, and return its result. No bot
logic lives in `tools.py`.

### Bots (`foundry/bots.py`)
Pure functions over the ledger (plus, in the live version, model
calls). Each bot has one job, one input card kind, one output card
kind (see SPEC.md §3). Bots never talk to each other directly —
they only read/write ledger cards. That is the architectural rule
that makes the shared memory real: if two bots need to coordinate,
there is a card for it, with provenance.

**MVP implementation note (honest):** the scaffold's bots are
deterministic and template-based. Scribe's v2 "sharper hook"
revision is a rule-based rewrite of the seeded v1, not a live LLM
call. Lookout does not fetch the web in the scaffold — Evidence
Cards come from seed data or from user-supplied sources. The live
wiring (Scribe via `ctx.llm`, Lookout via a search provider) is
the Sat Nov 7 step in the plan, and its exact `ctx.llm` call shape
is UNVERIFIED — see RESEARCH.md.

### Ledger (`foundry/ledger.py`)
SQLite, one database, three tables (`cards`, `links`, `events`).
Field model: `docs/LEDGER.md`. In Hermes, the database lives at
`plugin_db("foundry")` (via `plugins.plugin_storage`); in this
scaffold, at `data/foundry.db`, regenerated from `foundry/data/seed.json`
by `scripts/seed.py`. The ledger module accepts an explicit path so
tests use a temp file and never touch the demo DB.

Ledger invariants enforced in code:
- Every card has a unique id, a kind, a version, a status, a
  `created_by` (bot name or `human`), and a `created_at` timestamp.
- A Draft Card must reference ≥1 Evidence Card (`links` with
  relation `cites`). `draft_create` refuses otherwise.
- A Revision Card must reference the Draft Card it revises.
- Versions never mutate in place: v2 is a new card with
  `supersedes_id` pointing at v1; v1 stays readable.
- Money numbers are stored as integer cents where they are money,
  to avoid float rounding; display converts to dollars.

### Dashboard (`foundry/dashboard/`)
Web-dashboard extension, per the official dashboard guide:
`manifest.json` (tab `/foundry`, label "Foundry", icon `Sparkles`,
entry `dist/index.js`), an IIFE JS bundle using only
`window.__HERMES_PLUGIN_SDK__` (React + components from the SDK,
never bundled), and `plugin_api.py` (FastAPI router, mounted at
`/api/plugins/foundry/`).

The scaffold also ships `scripts/render_dashboard.py`, which renders
a **static, self-contained** `dashboard/index.html` from the ledger
for demoing without a Hermes install. That static file is a demo
artifact, not the dashboard extension itself: the extension is the
`dist/index.js` + `plugin_api.py` pair. Both read the same ledger
shape, so the demo and the real surface cannot drift apart silently
— the smoke test renders from the same seed the extension serves.

**UNVERIFIED:** the dashboard bundle has not been loaded in a live
`hermes dashboard`. The SDK component names used (`Card`,
`CardHeader`, `CardTitle`, `CardContent`, `Button`, `Badge`, `Tabs`,
etc.) are copied from the official dashboard guide; whether the
installed Hermes version exposes exactly those names has not been
executed against a live dashboard.

### Skills (`foundry/skills/foundry-creator/SKILL.md`)
One bundled skill, registered via `ctx.register_skill`, namespaced
`foundry:foundry-creator`. It tells the agent how to run a Foundry
cycle: interview → research → draft → review → score → money.
Read-only, as the guide requires.

## Data flow — one loop

1. Cartographer writes Identity Card v1 (seeded in the demo).
2. Lookout writes Evidence Card E1 (seeded; 2 sources, links).
3. Scribe writes Draft Card D1 citing E1.
4. Human, on the Proofing Table, writes Revision Card R1
   ("Tweak — sharper hook").
5. Scribe writes Draft Card D2 (supersedes D1), citing E1 + R1.
6. Human approves D2. Scorekeeper writes Performance Card P1.
7. Bursar writes Money Card M1 for D2 (costs, revenue, profit).
8. Next cycle: Lookout reads P1 + M1 before writing E2.

## What is verified vs unverified

| Piece | Status |
|---|---|
| Plugin manifest / `register(ctx)` / tool-handler shape | Verified from docs (RESEARCH.md) |
| Dashboard manifest / IIFE / SDK / FastAPI mount | Verified from docs |
| `plugin_data_dir` / `plugin_db` durable-state pattern | Verified from docs (exact import quoted) |
| Catalog rules (SHA pin, validate, disclosures) | Verified from docs |
| Ledger, bots, dashboard render, smoke test | Verified by running them here (see test output in report) |
| `hermes plugins validate` / `doctor` on Foundry | **UNVERIFIED** — no Hermes CLI in this workspace |
| `ctx.llm` live drafting; live search; live X/analytics | **Not implemented** in scaffold (stubs + seed) |
| Dashboard bundle in a live `hermes dashboard` | **UNVERIFIED** |
| Desktop SDK surface | Not built (backlog) |

## Security / safety notes

- No auto-post, no auto-send, no auto-buy. Approval is a human action.
- No credentials in the repo or in ledger seed data. Any future
  third-party key must come through Hermes secret scope / OAuth
  (catalog rule 11), never a `.env` read by the plugin.
- No self-updating code, no binaries, no `.pyc` in the repo
  (catalog rules 3, 17). Dependencies: none in the MVP (stdlib only)
  — `pyproject.toml` declares `dependencies = []` explicitly.
- Tax: tracking/export only. No advice, no filing, no "you owe $X"
  as a definitive claim — estimates are labelled estimates.
