"""Real SQLite regression tests; no host/model/network required."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import json
from foundry import bots, ledger, tools, storage
from foundry.dashboard import plugin_api


class DraftIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = ledger.connect(Path(self.tmp.name) / 'ledger.db')
        ledger.load_seed(self.conn, ROOT / 'foundry/data/seed.json')

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_untrusted_approval_paths_fail_closed_without_writes(self):
        tools.set_db_path(Path(self.tmp.name) / 'ledger.db')
        try:
            for route in ('tool', 'feedback', 'dashboard'):
                with self.subTest(route=route):
                    before = self.conn.iterdump()
                    before = list(before)
                    args = {'draft_id': 'draft-002', 'feedback_type': 'approve',
                            'author': 'human', 'by': 'human', 'approved': True}
                    if route == 'tool':
                        result = json.loads(tools.foundry_draft_approve(args, actor='human'))
                    elif route == 'feedback':
                        result = json.loads(tools.foundry_draft_feedback(args, actor='human'))
                    else:
                        result = plugin_api.feedback(args)
                    self.assertFalse(result['ok'])
                    self.assertIn('trusted human', result['error'])
                    self.assertEqual(before, list(self.conn.iterdump()))
        finally:
            storage._OVERRIDE = None
            tools._DB_PATH = None

    def test_unverified_feedback_never_claims_human_authorship(self):
        tools.set_db_path(Path(self.tmp.name) / 'ledger.db')
        try:
            result = json.loads(tools.foundry_draft_feedback({
                'draft_id': 'draft-002', 'feedback_type': 'tweak',
                'note': 'sharper hook', 'author': 'human'}, actor='human'))
            self.assertTrue(result['ok'])
            revision = result['revision']
            self.assertEqual('unverified', revision['created_by'])
            self.assertEqual('unverified', revision['payload']['author'])
        finally:
            storage._OVERRIDE = None
            tools._DB_PATH = None

    def test_wrong_kind_identity_is_rejected_without_writes(self):
        before = ledger.list_cards(self.conn)
        with self.assertRaisesRegex(ValueError, 'Identity Card'):
            bots.scribe_draft(self.conn, evidence_id='evidence-001',
                              identity_id='evidence-001', hook='Hook', body=['Body'])
        self.assertEqual(before, ledger.list_cards(self.conn))

    def test_wrong_kind_evidence_is_rejected_without_writes(self):
        before = ledger.list_cards(self.conn)
        with self.assertRaisesRegex(ValueError, 'Evidence Card'):
            bots.scribe_draft(self.conn, evidence_id='identity-001',
                              identity_id='identity-001', hook='Hook', body=['Body'])
        self.assertEqual(before, ledger.list_cards(self.conn))


class SeedFixtureTests(unittest.TestCase):
    """The seeded demo fixture must never present fake human approval
    or authorship as real (fixed 2026-11-11: draft-002 was seeded
    'approved', revision-001 was seeded as human-authored)."""

    def test_seed_contains_no_approved_status(self):
        seed = json.loads((ROOT / 'foundry/data/seed.json').read_text())
        self.assertFalse(
            [c['id'] for c in seed['cards'] if c.get('status') == 'approved'],
            'seed must not contain an approved status')

    def test_seed_revision_authorship_is_unverified(self):
        seed = json.loads((ROOT / 'foundry/data/seed.json').read_text())
        rev = next(c for c in seed['cards'] if c['id'] == 'revision-001')
        self.assertEqual('unverified', rev['created_by'])
        self.assertEqual('unverified', rev['payload']['author'])

    def test_seed_all_cards_labeled_demo(self):
        # 2026-11-11: every seeded card is titled "Demo: …" and carries
        # origin "seed" so no agent or viewer can mistake sample data
        # for the user's own brand, drafts, or numbers.
        seed = json.loads((ROOT / 'foundry/data/seed.json').read_text())
        self.assertEqual(9, len(seed['cards']))
        for c in seed['cards']:
            self.assertTrue(c['title'].startswith('Demo: '), c['id'])
            self.assertEqual('seed', c['payload'].get('origin'), c['id'])

    def test_static_render_labels_fixture_as_seeded_demo(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'render_dashboard', ROOT / 'scripts' / 'render_dashboard.py')
        render_dashboard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(render_dashboard)
        with tempfile.TemporaryDirectory() as tmp:
            render_dashboard.DB = Path(tmp) / 'foundry.db'
            render_dashboard.OUT = Path(tmp) / 'index.html'
            out = render_dashboard.render()
            html = out.read_text()
        self.assertIn('Seeded demo data', html)
        self.assertIn('Approval unavailable', html)
        self.assertIn('(in_review)', html)
        self.assertNotIn('(approved)', html)
        self.assertNotIn('Approved — Revision Card recorded', html)


if __name__ == '__main__':
    unittest.main(verbosity=2)
