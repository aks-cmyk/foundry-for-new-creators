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

## Re-verification after fixes (2026-11-06)

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
