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

## UNVERIFIED — do not present as fact

- **`hermes plugins validate` / `hermes plugins doctor` on Foundry.**
  Hermes CLI is not installed in this workspace (`hermes: command not
  found`, 2026-11-06). The scaffold follows the documented format, but
  it has **not** passed the catalog check. Run both before any PR.
- **`requires_hermes` floor.** The docs' example floor is `">=0.21.5"`.
  Foundry's `plugin.yaml` uses that as a placeholder floor; the correct
  floor for the APIs Foundry actually uses (dashboard backend, `ctx.llm`
  if added) has not been verified against a live Hermes release.
  The docs also say a floor must never be newer than the current release
  — the current release version was not checked here.
- **`ctx.llm` call shape, `ctx.register_tool` exact kwargs, and the
  `ctx` object surface** beyond what is quoted above. The scaffold's
  `__init__.py` uses `ctx.register_tool(name=…, schema=…, handler=…)`
  and `ctx.register_skill(name, path)` as shown in the guide's examples;
  the exact kwarg names have not been executed against a live Hermes.
- **Live X / analytics / money APIs.** No live X, Buffer, Stripe or
  analytics integration exists in the scaffold. Scorekeeper/Bursar
  numbers in the seed are illustrative example data, not real metrics.
- **Catalog entry file format** (`plugin-catalog/*.yaml` fields for the
  entry PR itself) — not read in full. Required before the PR.
- **The plugin-catalog repo / entry PR mechanics** beyond the rules
  above — the PR is not drafted yet and needs Amit's go-ahead.
