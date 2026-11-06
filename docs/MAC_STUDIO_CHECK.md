# Mac Studio live check — Foundry

Purpose: close the last two UNVERIFIED items from the VM validation —
a real `ctx.llm` Scribe revision, and a live dashboard load — on Amit's
Mac Studio, where his real Hermes lives.

Status before this check (VM, 2026-11-06):
- Hermes v0.23.0 installed in the VM; `hermes plugins validate` 15/15 PASS;
  `hermes plugins doctor` PASS after fixing `register_tool(toolset="foundry")`.
- Smoke test 23/23 PASS. Live Scribe wired via verified `ctx.llm` shape,
  but never run against a real model. Lookout stays stubbed (no `ctx`
  web-search surface in v0.23.0).
- Full record: `docs/VALIDATION.md`.

## 0. What you need

- Your Mac Studio, with your Hermes already installed.
- The Foundry repo (this folder). If you don't have it on the Mac yet,
  copy the whole `foundry-creator-plugin-hermes-plugin-hackathon-entry`
  folder over first — no GitHub repo exists yet, so copy it by AirDrop /
  USB / file share, whichever you normally use.
- About 15 minutes. Nothing here submits, posts, or spends money.

## 1. Check your Hermes version

```bash
hermes --version
```

Note the version down. The VM validated against **v0.23.0**. If yours is
older, tell Zuzu before going further — the plugin floor in
`foundry/plugin.yaml` is `>=0.21.5` (the docs' example floor, not a
bisected minimum), so an older version may still work, but it is
unverified.

## 2. Install Foundry into your Hermes

```bash
cp -r foundry ~/.hermes/plugins/foundry
hermes plugins validate ~/.hermes/plugins/foundry --install-deps
hermes plugins doctor foundry --ci
hermes plugins enable foundry
```

Expected: validate PASS, doctor PASS with **7 tools registered**.
(The count was 8 before the 2026-11-06 fix round dropped the
`foundry_dashboard_render` tool, which failed in a live install.)
If doctor shows 0 tools, or validate fails, stop and send Zuzu the
full output — do not work around it.

## 3. Live Scribe test (real LLM, no posting)

In Hermes, ask for a Foundry draft revision using the seeded data, e.g.:

> Revise draft-002 with the feedback "sharper hook"

Expected: Scribe returns a v3 draft, and the Revision Card records
`"generation": "llm"` (not `"rule-based"`). That is the proof the live
`ctx.llm` path works. Nothing is posted anywhere — this is a draft
revision only.

Report back: did v3 come back, and did it say `llm` or `rule-based`?

## 4. Live dashboard load

```bash
hermes dashboard
```

Open the Foundry tab. Expected: all three tabs render —
Proofing Table, Scorekeeper, Bursar — over the 9 seeded cards,
with the v2 hook "Your last 100 posts taught your tools nothing…".

Report back: which tabs rendered, and anything blank / broken.

## 5. What to send Zuzu

- `hermes --version` output
- validate + doctor output (pass/fail, tool count)
- Scribe v3 result: `llm` or `rule-based`?
- Dashboard: which tabs rendered?

With those four answers, the last UNVERIFIED items close, and the
next step — GitHub repo + catalog PR + demo video + Typeform, only
with Amit's go-ahead — can start. Deadline: Wed Nov 11, 2026,
5 PM EST / 2 PM PST.
