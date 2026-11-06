# Foundry — a creator plugin for Hermes Agent

Foundry is an end-to-end creator plugin for Hermes Agent: a crew of five bots
sharing **one structured memory ledger**, with a three-tab dashboard
(Proofing Table / Scorekeeper / Bursar).

It is the entry for the **Hermes Agent Plugin Hackathon** (announced Nov 4, 2026;
submissions due **5 PM EST Wed Nov 11, 2026 — 2 PM PST**).

> **Status: MVP scaffold, not a submission.** Nothing here has been submitted
> anywhere. No catalog PR, no demo video, no Typeform — those need Amit's
> go-ahead. See `docs/SPEC.md` and `docs/CHANGELOG.md`.

## The idea in one paragraph

Most creator tools are a prompt chain: research, draft, post, forget.
Foundry is a workshop. Five bots — **Cartographer** (interview),
**Lookout** (sourced research), **Scribe** (writer), **Scorekeeper**
(analytics), **Bursar** (costs, profit, partnerships, tax tracking) —
read and write the same versioned ledger cards. A draft cannot exist
without citing an Evidence Card. Feedback becomes a Revision Card.
Performance and money write back, so the next cycle is smarter.
A human approves anything public. Nothing auto-posts.

Foundry is **not** Eden / Dan Koe. Different names, different design
(workshop + ledger, not garden / brand board), different job: Foundry
owns the money side and the memory between bots, which Eden-style
content tools do not.

## Quick start (no coding needed)

```bash
make test        # smoke test: ledger + bots + dashboard render
make demo        # rebuild the seeded dashboard and print where it is
make seed        # (re)seed the demo ledger from foundry/data/seed.json
```

Then open the dashboard it prints, e.g. `dashboard/index.html`, in a browser.
It is a static, self-contained demo: no API keys, no Hermes install,
no network calls.

## Layout

```
foundry/                  # the installable Hermes plugin directory
  plugin.yaml             # native manifest (v2) — name, version, tools
  __init__.py             # register(ctx) — wires schemas to handlers
  schemas.py              # tool schemas (what the model sees)
  tools.py                # tool handlers (always return JSON strings)
  ledger.py               # shared ledger: SQLite cards + links + events
  bots.py                 # Cartographer / Lookout / Scribe / Scorekeeper / Bursar
  dashboard/
    manifest.json         # web-dashboard tab (name, label, tab path, entry)
    dist/index.js         # dashboard UI bundle (IIFE, SDK React)
    dist/style.css
    plugin_api.py         # FastAPI routes, mounted at /api/plugins/foundry/
  skills/foundry-creator/SKILL.md
  data/seed.json          # seeded demo cards
docs/
  SPEC.md                 # full build spec (product, bots, demo, day-by-day plan)
  ARCHITECTURE.md         # how the pieces fit, verified vs unverified
  LEDGER.md               # shared-ledger data model, field by field
  DEMO.md                 # 90-second demo script
  RESEARCH.md             # what was verified from primary sources
  CHANGELOG.md            # version history
tests/test_smoke.py       # smoke test (no Hermes, no network)
scripts/                  # seed.py, render_dashboard.py, demo.py
```

## Install into Hermes

Validated in the VM against Hermes **v0.23.0** (2026-11-06):
`hermes plugins validate` 15/15 PASS, `hermes plugins doctor` PASS
(8 tools). Full record: `docs/VALIDATION.md`. Live Scribe and live
dashboard load are still UNVERIFIED — they need Amit's Mac Studio,
where his real Hermes lives. See `docs/MAC_STUDIO_CHECK.md` for the
exact steps.

```bash
# copy the plugin into Hermes' plugin directory, then validate + doctor it
cp -r foundry ~/.hermes/plugins/foundry
hermes plugins validate ~/.hermes/plugins/foundry --install-deps
hermes plugins doctor foundry --ci
hermes plugins enable foundry
```

Catalog submission is a PR to `NousResearch/hermes-agent` pinning a full
40-character commit SHA — see `docs/RESEARCH.md` and `docs/SPEC.md §9`.
Do not submit without Amit's go-ahead.

## Rules baked in

- **Human approval on anything public.** No auto-post, no auto-send.
- **Tax tracking only.** Bursar categorises, estimates and exports.
  It gives no tax advice and files nothing.
- **No invented facts.** Scribe drafts only from cited Evidence Cards;
  a claim with no source is cut.
- **No secrets in the repo.** No API keys, no `.env`, no credentials.
  See `.gitignore`.
