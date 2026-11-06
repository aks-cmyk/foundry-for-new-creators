"""Foundry smoke test — stdlib only, no Hermes, no network.

Covers: ledger round-trip + invariants, the full bot loop
(identity -> evidence -> draft v1 -> feedback -> draft v2 -> score -> money),
tool handlers (JSON strings, never raise), plugin.yaml tools matching
schemas, register() with a fake ctx, and dashboard render.
Run: python3 tests/test_smoke.py  (or: make test)
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry import bots, ledger, schemas, storage, tools  # noqa: E402
import foundry as foundry_plugin  # noqa: E402  (package __init__ defines register())


def check(name, cond):
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise AssertionError(name)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        conn = ledger.connect(db)
        result = ledger.load_seed(conn, ROOT / "foundry" / "data" / "seed.json")
        check("seed loads 9 cards", result["cards_loaded"] == 9)
        check("seed loads 8 links", result["links_loaded"] == 8)
        counts = ledger.counts(conn)
        check("counts: 1 identity, 1 evidence, 2 drafts, 1 revision, 1 performance, 3 money",
              counts == {"identity": 1, "evidence": 1, "draft": 2,
                         "revision": 1, "performance": 1, "money": 3})

        # Invariant: draft cites evidence
        d2 = ledger.get_card(conn, "draft-002")
        check("draft-002 supersedes draft-001", d2["supersedes_id"] == "draft-001")
        check("draft-002 cites evidence-001",
              any(l["to_id"] == "evidence-001" and l["relation"] == "cites" for l in d2["links"]))

        # Scribe refuses without evidence
        try:
            bots.scribe_draft(conn, evidence_id="evidence-999", identity_id="identity-001",
                              hook="x", body=["y"])
            check("scribe refuses missing evidence", False)
        except ValueError:
            check("scribe refuses missing evidence", True)

        # Full loop on a fresh draft
        ev = bots.lookout_evidence(
            conn, topic="test topic",
            sources=[{"title": "s1", "url": "https://example.com/1", "retrieved_at": "2026-11-06", "note": ""},
                     {"title": "s2", "url": "https://example.com/2", "retrieved_at": "2026-11-06", "note": ""}],
            confirmed=["test claim"], niche="creator business")
        check("lookout needs >=2 sources (created)", ev["kind"] == "evidence")
        draft = bots.scribe_draft(conn, evidence_id=ev["id"], identity_id="identity-001",
                                  hook="A test hook.", body=["Body post."])
        check("scribe draft v1 created", draft["version"] == 1 and draft["status"] == "in_review")
        revised = bots.scribe_revise(conn, draft_id=draft["id"], note="sharper hook")
        check("scribe revise creates v2, original untouched",
              revised["version"] == 2 and revised["supersedes_id"] == draft["id"]
              and ledger.get_card(conn, draft["id"])["payload"]["hook"] == "A test hook.")
        check("rule-based revise marks generation", revised["payload"].get("generation") == "rule-based")

        # Live Scribe path (fake llm): JSON reply replaces the draft
        def fake_llm(messages):
            assert messages[0]["role"] == "system" and "Scribe" in messages[0]["content"]
            return json.dumps({"hook": "LLM hook.", "body": ["LLM post one.", "LLM post two."]})
        llm_revised = bots.scribe_revise(conn, draft_id=revised["id"], note="sharper hook",
                                         llm_complete=fake_llm)
        check("llm revise uses model text + marks generation=llm",
              llm_revised["payload"]["hook"] == "LLM hook."
              and llm_revised["payload"]["text"].startswith("LLM hook.\n\nLLM post one.")
              and llm_revised["payload"].get("generation") == "llm")
        # Failing llm falls back to the rule-based rewrite, never raises
        def bad_llm(messages):
            raise RuntimeError("model down")
        fb = bots.scribe_revise(conn, draft_id=llm_revised["id"], note="sharper hook",
                                llm_complete=bad_llm)
        check("llm failure falls back to rule-based",
              fb["payload"].get("generation") == "rule-based" and fb["version"] == 4)
        perf = bots.scorekeeper_verdict(conn, draft_id=revised["id"],
                                        metrics={"views": 100, "likes": 10, "reposts": 40, "replies": 20, "saves": 5})
        check("scorekeeper verdict repeat on engagement>=50", perf["payload"]["verdict"] == "repeat")
        money = bots.bursar_money(conn, draft_id=revised["id"], cost_cents=1000, revenue_cents=2500)
        check("bursar profit computed (2500-1000=1500)", money["payload"]["profit_cents"] == 1500)

        # Durable store (fix 2026-11-06): outside Hermes, storage falls
        # back to the local demo DB; inside Hermes it resolves to
        # <home>/plugin-data/foundry/data.db (plugin_db's file). Checked
        # BEFORE set_db_path, which overrides the resolution (tests).
        check("storage.db_path() falls back to local demo DB outside Hermes",
              storage.db_path() == ROOT / "foundry" / "data" / "foundry.db")

        # Tools: JSON strings, never raise
        tools.set_db_path(db)
        check("set_db_path() overrides the resolution for tools AND the API",
              storage.db_path() == db)
        out = json.loads(tools.foundry_ledger_list({"kind": "draft"}))
        check("tool ledger_list returns JSON ok", out["ok"] and len(out["cards"]) >= 2)
        bad = json.loads(tools.foundry_ledger_get({"card_id": "nope"}))
        check("tool ledger_get error is JSON, not a raise", bad["ok"] is False)

        # Dashboard backend POST /feedback (fix 2026-11-06): writes a real
        # Revision Card + a revised draft, sharing the tools' database
        # (tools._DB_PATH is the temp DB here, so the API sees it too).
        from foundry.dashboard import plugin_api
        # Router registration is only checkable when FastAPI is installed
        # (it is a Hermes dependency; system Python here has none).
        if plugin_api.router is not None:
            check("plugin_api router has GET /cards, /summary and POST /feedback",
                  {r.path for r in plugin_api.router.routes} >= {"/cards", "/summary", "/feedback"})
        else:
            check("plugin_api endpoints exist without FastAPI (router is None here)",
                  callable(plugin_api.feedback) and callable(plugin_api.list_cards))
        fb = plugin_api.feedback({"draft_id": "draft-002",
                                  "feedback_type": "tweak",
                                  "note": "sharper hook"})
        check("POST /feedback tweak writes Revision Card + revised draft",
              fb["ok"] and fb["revision"]["kind"] == "revision"
              and fb["revised_draft"]["version"] == 3
              and fb["revised_draft"]["payload"].get("generation") == "rule-based")
        fb_bad = plugin_api.feedback({"draft_id": "draft-002",
                                      "feedback_type": "tweak", "note": ""})
        check("POST /feedback tweak without a note is an error, not a raise",
              fb_bad["ok"] is False)
        cards = plugin_api._read_cards()
        check("plugin_api reads the same ledger the tools write",
              len(cards) >= 10 and any(c["kind"] == "revision" for c in cards))

        # plugin.yaml tools == schemas == handlers
    # PyYAML is not a dependency — parse plugin.yaml minimally.
    text = (ROOT / "foundry" / "plugin.yaml").read_text()
    declared = [line.strip()[2:] for line in text.splitlines()
                if line.strip().startswith("- foundry_")]
    schema_names = [s["name"] for s in schemas.ALL_SCHEMAS]
    check("plugin.yaml provides_tools == schemas == handlers",
          declared == schema_names == sorted(tools.HANDLERS.keys()) or
          set(declared) == set(schema_names) == set(tools.HANDLERS.keys()))

    # register() with a fake ctx — records the toolset kwarg, because
    # doctor (2026-11-06) caught the real bug: register_tool() requires
    # toolset, and validate's stub accepts anything.
    class FakeCtx:
        def __init__(self):
            self.tools = {}
            self.toolsets = {}
            self.skills = {}
        def register_tool(self, name=None, schema=None, handler=None, toolset=None, **kw):
            if toolset is None:
                raise TypeError("register_tool() missing required argument: 'toolset'")
            self.tools[name or schema["name"]] = handler
            self.toolsets[name or schema["name"]] = toolset
        def register_skill(self, name, path):
            self.skills[name] = path
    ctx = FakeCtx()
    foundry_plugin.register(ctx)
    check("register() registers 7 tools (dashboard_render dropped 2026-11-06)",
          len(ctx.tools) == 7)
    check("register() passes toolset='foundry' for all tools",
          set(ctx.toolsets.values()) == {"foundry"})
    check("register() registers foundry-creator skill", "foundry-creator" in ctx.skills)

    # Desktop half (fix 2026-11-06): single ESM file, allowed imports
    # only, route + sidebar nav, same backend via ctx.rest.
    desktop = (ROOT / "foundry" / "desktop" / "plugin.js").read_text()
    check("desktop/plugin.js exists and default-exports id 'foundry'",
          "id: 'foundry'" in desktop and "export default" in desktop)
    check("desktop/plugin.js imports only @hermes/plugin-sdk, react, react/jsx-runtime",
          "from '@hermes/plugin-sdk'" in desktop
          and "from 'react'" in desktop
          and "from 'react/jsx-runtime'" in desktop
          and "from '" not in desktop.replace("from '@hermes/plugin-sdk'", "")
          .replace("from 'react'", "").replace("from 'react/jsx-runtime'", ""))
    check("desktop/plugin.js registers a /foundry route + sidebar nav",
          "ROUTES_AREA" in desktop and "SIDEBAR_NAV_AREA" in desktop
          and "path: '/foundry'" in desktop)
    check("desktop/plugin.js reaches the shared backend via ctx.rest",
          "rest('/cards')" in desktop and "rest('/feedback'" in desktop
          and "method: 'POST'" in desktop)
    check("desktop/plugin.js has no alert()/eval/document reach",
          "alert(" not in desktop and "eval(" not in desktop
          and "document." not in desktop)

    # Dashboard render
    from scripts.render_dashboard import render
    out_path = render()
    html_text = out_path.read_text()
    check("dashboard renders with all three tabs",
          all(t in html_text for t in ("Proofing Table", "Scorekeeper", "Bursar")))
    check("dashboard shows seeded v2 hook", "Your last 100 posts taught your tools nothing" in html_text)
    check("dashboard labels seed as estimated", "estimated" in html_text)

    print("\nSMOKE TEST: all checks passed.")


if __name__ == "__main__":
    main()
