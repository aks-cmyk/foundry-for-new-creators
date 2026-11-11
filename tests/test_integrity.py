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


if __name__ == '__main__':
    unittest.main(verbosity=2)
