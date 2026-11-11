# Mac Studio live check — Foundry

Purpose: close the last two UNVERIFIED items from the VM validation —
a real `ctx.llm` Smith revision, and a live dashboard load — on Amit's
Mac Studio, where his real Hermes lives. Both are now done: live Smith
verified Nov 10, 2026 (draft-003, `generation: "llm"`); live dashboard
load verified Nov 10, 11:15 PM (tabs render). Remaining unverified:
the Desktop load and the draft-003
correction (Amit has not yet picked an option — option 1 advised).
The Brand tab renders live — Amit confirmed all four tabs Nov 11.

Status before this check (VM, 2026-11-06):
- Hermes v0.23.0 installed in the VM; `hermes plugins validate` PASS
  (16 checks, incl. the desktop-surface check); `hermes plugins doctor`
  PASS (7 tools).
- Smoke test 34/34 PASS. Ledger now lives at `plugin_db("foundry")`;
  dashboard buttons are wired to a real `POST /feedback`; a Desktop
  GUI half (`foundry/desktop/plugin.js`) is built — see step 5.
- Live Smith wired via verified `ctx.llm` shape, but never run
  against a real model. Prospector stays stubbed (no `ctx` web-search
  surface in v0.23.0).
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

Expected: validate PASS, doctor PASS with **8 tools registered** —
the eighth is `foundry_start`, which restored the count to 8 after the
2026-11-06 fix round dropped the broken `foundry_dashboard_render` tool.
If doctor shows 0 tools, or validate fails, stop and send Zuzu the
full output — do not work around it.

## 3. Live Smith test (real LLM, no posting)

In Hermes, ask for a Foundry draft revision using the seeded data, e.g.:

> Revise draft-002 with the feedback "sharper hook"

Expected: Smith returns a v3 draft, and the Revision Card records
`"generation": "llm"` (not `"rule-based"`). That is the proof the live
`ctx.llm` path works. Nothing is posted anywhere — this is a draft
revision only.

Report back: did v3 come back, and did it say `llm` or `rule-based`?

## 4. Live dashboard load

```bash
hermes dashboard
```

Open the Foundry tab. Expected: all four tabs render —
Proofing Table, Brand, Inspector, Paymaster — over the 9 seeded cards,
with the v2 hook "Your last 100 posts taught your tools nothing…".

Report back: which tabs rendered, and anything blank / broken.

## 5. Live Desktop load (new — the Desktop half)

In the Hermes Desktop app:
1. Open **Capabilities → Plugins**, find **Foundry**, flip it on.
   (It ships opt-in, so it will be listed but off until you enable it.)
2. Open the **Foundry** page from the sidebar. Expected: the same
   four tabs — Proofing Table, Brand, Inspector, Paymaster — over the 9
   seeded cards.
3. On the Proofing Table, try **Tweak** with the note "sharper hook".
   Expected: a v3 draft comes back on the board (no pop-up alert —
   the old stubs are gone).

Report back: did the Foundry page appear, which tabs rendered, and
did Tweak return v3?

## 6. Onboarding live check (foundry start + Brand tab)

This is the one part the VM cannot test — the interview needs a live
model, and yours has one. In a fresh Hermes session, just say:

foundry start

Expected: Hermes asks the interview questions one at a time (who you
help, audience, story, pillars, beliefs, what you will never say,
voice examples, words you never use, mission). Answer in your own
words — only the first one is required. When you are done, Hermes
writes your Identity Card (v2 — the seeded demo brand is v1).

Then check two things:
1. In chat, ask: *show me my brand* (or list the identity cards).
   Expected: your answers, as Identity Card v2.
2. In the dashboard, open the **Brand** tab. Expected: your brand
   shown (v2, "interview"), with an **Edit brand** button. Try
   changing one field (e.g. Mission) and saving — it should come
   back as v3, and v2 should still be in the ledger underneath.

Also try, once: ask Hermes to draft something *before* the interview
is done (or with the demo brand). Expected: it refuses and points
you at `foundry start` — it should never draft in the demo brand's
voice.

Report back: did the interview run, what did the Brand tab show,
and did the edit save as v3?

## 7. What to send Zuzu

- `hermes --version` output
- validate + doctor output (pass/fail, tool count)
- Smith v3 result: `llm` or `rule-based`?
- Web dashboard: which tabs rendered?
- Desktop: did the Foundry page appear, and did Tweak return v3?
- Onboarding: did the interview run, what did the Brand tab show, and did the edit save as v3?

With those six answers, the last UNVERIFIED items close, and the
next step — GitHub repo + catalog PR + demo video + Typeform, only
with Amit's go-ahead — can start. Deadline: Wed Nov 11, 2026,
5 PM EST / 2 PM PST.
