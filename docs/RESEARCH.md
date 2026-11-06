# Research — what was verified from primary sources

Read 2026-11-06 from the official Hermes Agent docs. Anything marked
**UNVERIFIED** was not run / not seen in a primary source and must not be
presented as fact.

## Sources read

| Source | What it established |
|---|---|
| https://hermes-agent.nousresearch.com/docs/developer-guide/plugins | Native plugin format, manifest, `register(ctx)`, tools, hooks, skills, durable state, validate/doctor |
| https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission | Catalog admission rules (18 rules, mirrored from `plugin-catalog/README.md`) |
| https://hermes-agent.nousresearch.com/docs/user-guide/features/extending-the-dashboard | Web-dashboard plugin format: `manifest.json` + IIFE bundle + FastAPI backend |
| https://x.com/NousResearch/status/2118094256438936062 (read live in a browser task, 2026-11-05) | Hackathon post itself: 7 days, $20,000, deadline 5 PM EST Nov 11, entry route, judging criteria |
| Installed Hermes v0.23.0 source (`.hermes-src/`, 2026-11-06) | Exact `register_tool` signature, `ctx.llm` call shape, trust gate, `register_skill` signature; dashboard loader not in CLI code |
| https://hermes-agent.nousresearch.com/docs/getting-started/installation (read 2026-11-06) | Official install route: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh \| bash` |

## Hermes CLI install — verified 2026-11-06

- Install command (official route, flags from the docs page):
  `bash hidden_files/install.sh --dir "$PWD/.hermes-src" --hermes-home "$PWD/hidden_files/hermes-home" --non-interactive --skip-browser --skip-computer-use`
  (installer script saved at `hidden_files/install.sh`; full log at
  `hidden_files/install-2026-11-06.log` — both git-ignored bookkeeping).
- Installed: **Hermes Agent v0.23.0** (2026.9.24), stable, local commit
  `2bd378ed1b8d`; **Python 3.14.9**; uv 0.13.5; OpenAI SDK 2.54.0.
  Launcher: `~/.local/bin/hermes`. Isolated `HERMES_HOME` =
  `hidden_files/hermes-home` (the real `~/.hermes` was never touched).
- `hermes --version` prints the version. **`hermes version` is NOT a
  command** (`hermes: 'version' is not a hermes command` — the docs'
  version subcommand does not exist in v0.23.0).
- Two non-fatal warnings during install: `mv: failed to preserve
  ownership` for uv/uvx (operation not permitted in this sandbox).
  Install exit code 0.
- Install lives in the goal workspace (`.hermes-src/`,
  `hidden_files/hermes-home/`), git-ignored — there is no separate
  `.venv-hermes`; the installer manages its own venv/tools.

## Hackathon — verified

- Post: @NousResearch, Nov 4, 2026, 1:33 PM. URL above.
- "The Hermes Agent Plugin Hackathon starts now! It runs for 7 days,
  with $20,000 in cash prizes and more."
- Prizes: 1st $10,000 + neon sign + merch + $1,000 creds; 2nd $5,000;
  3rd $2,500; 4th $1,500; 5th $1,000; runners-up (x5) merch + $250 creds.
- Submissions due **5 PM EST Nov 11, 2026** (2 PM PST).
- Entry: (1) PR adding the plugin to the Hermes plugin catalog at
  `hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission`;
  (2) demo video on X tagging @NousResearch (under 90 seconds, show the
  plugin working); (3) both links via `form.typeform.com/to/FwJLvOln`.
- Judges score usefulness, reliability, polish, creativity; they favour
  plugins that do more than a prompt or a skill could.

## Native plugin format — verified

- A native plugin is a directory with **`plugin.yaml` + `__init__.py`**
  containing a **`register(ctx)`** function. Layout (docs):
  `~/.hermes/plugins/<name>/plugin.yaml`, `__init__.py`, `schemas.py`,
  `tools.py`. Portable Agent Plugins v1 (`plugin.json` + `skills/` +
  `mcp.json`) is a separate, compatibility format — Foundry uses the
  **native** format, not the portable one.
- Manifest v1 example (docs, "Step 2: Write the manifest"):
  `name`, `version`, `description`, `provides_tools: [...]`,
  `provides_hooks: [...]`. `provides_tools` must match what
  `register()` actually registers — `hermes plugins validate` fails
  otherwise, and that blocks catalog admission.
- Manifest v2 (additive, docs): `manifest_version: 2`, `api_version: 1`,
  `license`, `homepage`, `tags`, `requires_plugins`, `python_dependencies`
  (with bounds, e.g. `"somepkg>=1.0,<2"`), `config_schema`. A manifest
  without `manifest_version` is v1 and "stays fully supported forever".
  Unknown fields are ignored with a warning.
- Tool handlers: signature `def handler(args: dict, **kwargs) -> str`;
  **always return a JSON string**, success and errors alike; never raise.
  `**kwargs` receives Hermes-injected context (`task_id`, `session_id`, …).
- Skills: register with `ctx.register_skill(name, skill_md_path)`;
  namespaced as `<plugin>:<skill>`; read-only; loaded via
  `skill_view("foundry:foundry-creator")`.
- Durable state — **verified, exact import from the docs**:
  ```python
  from plugins.plugin_storage import plugin_data_dir, plugin_db
  state_file = plugin_data_dir("my-plugin") / "state.json"
  conn = plugin_db("my-plugin")  # SQLite, WAL mode, thread-friendly
  ```
  Never write runtime state into the plugin directory — updates/removal
  delete it. The per-plugin data root survives both and follows the
  active profile.
- Dependencies: declare in `python_dependencies` in `plugin.yaml`, or
  preferably in a `pyproject.toml` next to it (`[project]`,
  `requires-python = ">=3.11"`). `pyproject.toml` wins when both exist.
  Upper bounds on every dependency are strongly recommended.
- Validation: `hermes plugins validate /path/to/your-plugin --install-deps`
  runs the same check catalog CI runs. `hermes plugins doctor
  [path-or-id]` runs discovery, manifest parsing, `register(ctx)` and
  registries with a temporary `HERMES_HOME`; `--ci` exits non-zero
  on error.
- Install flow (docs): `hermes plugins install owner/repository
  --no-enable`, `hermes plugins list`, `hermes plugins enable <name>`.

## Web-dashboard extension — verified

- A dashboard plugin is a directory with **`manifest.json` + a pre-built
  JS bundle (IIFE)** and optionally CSS and a Python FastAPI file,
  living as a **`dashboard/` subfolder inside the plugin directory**,
  so one plugin can extend CLI/gateway and dashboard from one install.
- `manifest.json` fields: `name`, `label`, `description`, `icon`
  (Lucide name, e.g. `Sparkles`; unknown falls back to `Puzzle`),
  `version`, `tab: {path, position ("end" | "after:<path>" |
  "before:<path>"), override, hidden}`, `slots`, `entry`
  (default `dist/index.js`), `css`, `api`.
- JS bundle: plain IIFE, no build step required; React comes from
  `window.__HERMES_PLUGIN_SDK__` (`SDK.React`, `SDK.hooks`,
  `SDK.components` — Card, Button, Tabs, etc.); register with
  `window.__HERMES_PLUGINS__.register("my-plugin", MyPage)`.
  Never bundle React. JSX needs a bundler with React as an external.
- Backend: a Python file exposing a FastAPI `router`; routes mounted
  under **`/api/plugins/<name>/`**; called from the UI with
  `SDK.fetchJSON("/api/plugins/my-plugin/data")`.
- The **native Desktop app** has its own, unrelated SDK
  (`@hermes/plugin-sdk`) — Foundry's dashboard is the **web** dashboard
  only in the MVP. Desktop is backlog.

## Catalog submission — verified

From the catalog-submission page (18 rules; canonical copy is
`plugin-catalog/README.md` in `NousResearch/hermes-agent`):

1. Human-merged gate — entries only via a PR to the `hermes-agent`
   repo, reviewed and merged by a maintainer. No self-serve registry.
2. **Exact 40-character SHA pins are mandatory.** Branches, tags and
   short SHAs are rejected.
3. No self-updating code in a listed plugin.
4. SHA bumps are new PRs, re-reviewed.
5. Owner-or-major-contributor submissions only (or maintainer sweep).
6. Declared `capabilities:` must match reality (validate fails otherwise).
7. `hermes plugins validate` security scan runs at admission;
   `dangerous` fails, `caution` is a warning.
8. Desktop plugins stay inside the SDK surface (no `eval`, no prototype
   patching, no reaching into app internals).
9. No runtime overrides of Hermes core.
10. Dependency security policy is the plugin's; bare floors get asked
    for bounds.
11. Credentials only through Hermes routes (secret scope / OAuth);
    never read `.env`, `auth.json`, or another tool's login directly.
12. Approvals and unattended runs respected — no auto-approving.
13. Risky behaviour disclosed in PR description + README.
14. `requires_hermes` is a SemVer floor (`">=0.21.5"`), never a date,
    never newer than the current release; `version` matches pinned code.
15. No skins/forks of bundled plugins. 16. One listing per lineage.
17. No unscannable executable payloads (no binaries, no `.pyc`).
18. Password-manager login backends only from the vendor, at
    `verified`/`official` tier. (Not applicable to Foundry.)

## Validation + live ctx surface — verified 2026-11-06

Full record: `docs/VALIDATION.md`.

- **`hermes plugins validate` on Foundry: PASS** (15/15 checks,
  exit 0). **`hermes plugins doctor`: PASS** (8 tools registered)
  after one fix — see below. Both re-run after every change.
- **`ctx.register_tool` — exact signature** (`hermes_cli/plugins.py:463`):
  `register_tool(name, toolset, schema, handler, check_fn=None, ...)`.
  **`toolset` is required** — a call without it raises `TypeError`.
  Foundry passes `toolset="foundry"` (bundled `google_meet` passes
  `toolset="google_meet"`). Keyword form works.
- **Validate ≠ doctor.** Validate probes `register()` with a lenient
  stub (`RecordingContext.register_tool` accepts anything), so it
  passed while 0 tools were actually registered. Doctor runs the real
  `PluginContext` and caught the missing-`toolset` bug. Run both;
  doctor is the one that proves registration works. Doctor also exits
  0 even on registration failure — read its output, not its exit code.
- **`ctx.llm` — exact shape** (`agent/plugin_llm.py`, class `PluginLlm`,
  exposed as `PluginContext.llm`):
  `complete(messages: list[dict], *, provider=None, model=None, temperature=None, max_tokens=None, timeout=None, agent_id=None, profile=None, purpose=None, task=None) -> PluginLlmCompleteResult` with `.text`, `.provider`, `.model`, `.usage`.
  `complete_structured(*, instructions, input, json_schema=None, json_mode=False, ...) -> PluginLlmStructuredResult` with `.parsed`.
  Plain calls with **no provider/model override pass the default trust
  gate** (missing `plugins.entries.<id>.llm` config → fully restrictive
  only on *overrides*). Scribe uses `complete()` with no overrides.
  **Wired, not live-tested:** `scribe_revise` takes an `llm_complete`
  callable; `tools.bind_ctx(ctx)` in `register()` lets handlers call
  `ctx.llm.complete(...)`; any failure falls back to the rule-based
  rewrite and the card records `"generation": "llm" | "rule-based"`.
  No real completion has run (no model configured in this workspace).
- **`ctx.register_skill` — exact signature**
  (`hermes_cli/plugins_content.py:32`):
  `register_skill(name, path, description="", frontmatter=None)`;
  name must NOT contain `:` (namespace is derived from the plugin
  name). Foundry's `register_skill("foundry-creator", skill_md)` is
  correct as written.
- **No `ctx` web-search surface in v0.23.0.** `plugins.py` has no
  search/fetch method on `PluginContext`; web search lives in
  `tools/web_tools.py` / `agent/web_search_provider.py` as host
  internals, not a plugin-facing API. Lookout therefore stays
  agent-supplied (host agent searches, passes sources in) — no
  plugin-internal fetch. A plugin could reach it via `ctx.call_mcp`
  to a configured search MCP server, but no such server is configured
  or verified here.
- **Dashboard extension NOT covered by validate/doctor** — neither
  mentions it. Module-level checks 2026-11-06: `dist/index.js`
  parses under Hermes's own Node 26.12.1; `plugin_api.py` imports
  under FastAPI, router has `GET /cards` + `GET /summary`, reads the
  9 seeded cards. Live load under `hermes dashboard` still UNVERIFIED.
- **Current release is v0.23.0** (verified via `hermes --version`).
  `requires_hermes: ">=0.21.5"` in `plugin.yaml` remains the docs'
  example floor — the minimum release that actually ships the APIs
  Foundry uses (`register_tool` with `toolset`, `ctx.llm`) has not
  been bisected, so the floor is still a placeholder, not a verified
  minimum.

## UNVERIFIED — do not present as fact

- **Live X / analytics / money APIs.** No live X, Buffer, Stripe or
  analytics integration exists in the scaffold. Scorekeeper/Bursar
  numbers in the seed are illustrative example data, not real metrics.
- **Catalog entry file format** (`plugin-catalog/*.yaml` fields for the
  entry PR itself) — not read in full. Required before the PR.
- **The plugin-catalog repo / entry PR mechanics** beyond the rules
  above — the PR is not drafted yet and needs Amit's go-ahead.
- **Live dashboard load** under `hermes dashboard` (see above) and
  **live `ctx.llm` completion** (see above) — wired and unit-tested,
  never run against a live model/gateway.
- **`plugin.yaml` has no `homepage`** — no repo URL exists yet; do not
  invent one. Needed before the catalog PR.
