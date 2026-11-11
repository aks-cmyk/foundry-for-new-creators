"""Onboarding regressions: foundry_start, the draft guard, Brand save."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from foundry import bots, ledger, tools
from foundry.dashboard import plugin_api

SEED = Path(__file__).resolve().parents[1] / "foundry" / "data" / "seed.json"

ANSWERS = {
    "who_you_help": "Indie hackers learning to price their work",
    "audience": "Solo builders shipping their first paid product",
    "story": "Shipped a tool, charged too little, learned to price by value.",
    "pillars": ["pricing", "building in public", "solo business"],
    "beliefs": ["Most pricing advice is written for companies, not people."],
    "against": "Hustle-culture pricing hacks",
    "voice_examples": ["I charged $5. It should have been $50."],
    "voice_donts": ["crush it", "10x"],
    "mission": "Help solo builders charge what the work is worth",
}


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.db"
        conn = ledger.connect(self.db)
        ledger.load_seed(conn, SEED)
        conn.close()
        tools.set_db_path(self.db)

    def tearDown(self):
        from foundry import storage
        storage._OVERRIDE = None
        self.tmp.cleanup()

    def _call(self, handler, args):
        return json.loads(handler(args))

    def test_start_begin_returns_questions_and_not_onboarded(self):
        out = self._call(tools.foundry_start, {"step": "begin"})
        self.assertTrue(out["ok"])
        self.assertFalse(out["onboarded"])
        self.assertEqual(len(out["questions"]), 9)
        self.assertEqual(out["questions"][0]["key"], "who_you_help")
        self.assertTrue(out["questions"][0]["required"])
        self.assertEqual(out["identity"]["id"], "identity-001")

    def test_start_begin_bare_call_defaults_to_begin(self):
        out = self._call(tools.foundry_start, {})
        self.assertTrue(out["ok"])
        self.assertIn("questions", out)

    def test_start_complete_writes_identity_v2(self):
        out = self._call(tools.foundry_start, {"step": "complete", "answers": ANSWERS})
        self.assertTrue(out["ok"], out)
        card = out["identity"]
        self.assertEqual(card["id"], "identity-002")
        self.assertEqual(card["version"], 2)
        self.assertEqual(card["payload"]["origin"], "interview")
        self.assertEqual(card["created_by"], "cartographer")
        self.assertEqual(card["supersedes_id"], "identity-001")
        self.assertEqual(card["payload"]["who_you_help"], ANSWERS["who_you_help"])
        self.assertTrue(out["onboarded"])

    def test_start_complete_requires_who_you_help(self):
        out = self._call(tools.foundry_start, {"step": "complete", "answers": {"audience": "x"}})
        self.assertFalse(out["ok"])
        self.assertIn("who_you_help", out["error"])

    def test_start_complete_accepts_comma_separated_lists(self):
        answers = dict(ANSWERS, pillars="pricing, solo business")
        out = self._call(tools.foundry_start, {"step": "complete", "answers": answers})
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["identity"]["payload"]["pillars"], ["pricing", "solo business"])

    def test_start_begin_after_onboarding_reports_onboarded(self):
        self._call(tools.foundry_start, {"step": "complete", "answers": ANSWERS})
        out = self._call(tools.foundry_start, {"step": "begin"})
        self.assertTrue(out["onboarded"])
        self.assertEqual(out["identity"]["id"], "identity-002")

    def test_draft_create_refuses_demo_brand(self):
        out = self._call(tools.foundry_draft_create, {
            "evidence_id": "evidence-001", "identity_id": "identity-001",
            "hook": "Hook", "body": ["Body"]})
        self.assertFalse(out["ok"])
        self.assertIn("foundry_start", out["error"])

    def test_draft_create_works_with_interview_brand(self):
        self._call(tools.foundry_start, {"step": "complete", "answers": ANSWERS})
        out = self._call(tools.foundry_draft_create, {
            "evidence_id": "evidence-001", "identity_id": "identity-002",
            "hook": "Hook", "body": ["Body"]})
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["card"]["payload"]["evidence_ids"], ["evidence-001"])

    def test_brand_save_writes_new_version(self):
        self._call(tools.foundry_start, {"step": "complete", "answers": ANSWERS})
        out = plugin_api.brand({"identity_id": "identity-002",
                                "payload": {"mission": "Charge what it is worth"}})
        self.assertTrue(out["ok"], out)
        card = out["identity"]
        self.assertEqual(card["id"], "identity-003")
        self.assertEqual(card["version"], 3)
        self.assertEqual(card["payload"]["origin"], "dashboard-edit")
        self.assertEqual(card["created_by"], "dashboard")
        self.assertEqual(card["payload"]["mission"], "Charge what it is worth")
        self.assertEqual(card["payload"]["who_you_help"], ANSWERS["who_you_help"])
        # old version untouched
        conn = ledger.connect(self.db)
        try:
            old = ledger.get_card(conn, "identity-002")
        finally:
            conn.close()
        self.assertEqual(old["payload"]["mission"], ANSWERS["mission"])

    def test_brand_save_rejects_empty_who_you_help(self):
        out = plugin_api.brand({"payload": {"who_you_help": "  "}})
        self.assertFalse(out["ok"])
        self.assertIn("who_you_help", out["error"])

    def test_brand_save_rejects_unknown_fields(self):
        out = plugin_api.brand({"payload": {"nickname": "Zuzu"}})
        self.assertFalse(out["ok"])
        self.assertIn("nickname", out["error"])

    def test_brand_save_rejects_wrong_kind(self):
        out = plugin_api.brand({"identity_id": "draft-001", "payload": {"mission": "x"}})
        self.assertFalse(out["ok"])

    def test_seed_identity_is_marked_demo(self):
        conn = ledger.connect(self.db)
        try:
            ident = bots.latest_identity(conn)
            self.assertEqual(ident["id"], "identity-001")
            self.assertEqual(ident["payload"]["origin"], "seed")
            self.assertFalse(bots.is_onboarded(conn))
        finally:
            conn.close()

    def test_pre_origin_identity_counts_as_demo(self):
        # Installs seeded before the origin field existed (e.g. a live
        # Mac Studio DB from Nov 10) carry no origin — they are demo
        # brands too, so the guard and the onboarded check must treat
        # a missing origin the same as "seed".
        conn = ledger.connect(self.db)
        try:
            ledger.create_card(conn, id="identity-000", kind="identity", version=1,
                               lineage="identity-000", title="Identity Card",
                               status="active",
                               payload={"who_you_help": "Old demo brand"},
                               created_by="cartographer")
            self.assertFalse(bots.is_onboarded(conn))
        finally:
            conn.close()
        out = self._call(tools.foundry_draft_create, {
            "evidence_id": "evidence-001", "identity_id": "identity-000",
            "hook": "Hook", "body": ["Body"]})
        self.assertFalse(out["ok"])
        self.assertIn("foundry_start", out["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
