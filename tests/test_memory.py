"""Real SQLite scoped-memory regressions; no live runtime storage."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundry import ledger

class MemoryTests(unittest.TestCase):
    def test_candidate_survives_restart_but_is_not_authoritative(self):
        from foundry.memory import RoleMemory
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ledger.db'
            conn = ledger.connect(path)
            ledger.create_card(conn, id='source', kind='evidence', version=1,
                lineage='source', title='Observed source', status='new',
                payload={'fact': 'example'}, created_by='lookout')
            memory = RoleMemory(conn, role='lookout')
            candidate = memory.propose(category='observation', content={'fact': 'example'},
                                       source_id='source', source_version=1)
            self.assertEqual(memory.retrieve(), [])
            conn.close()
            conn = ledger.connect(path)
            restored = RoleMemory(conn, role='lookout').candidate(candidate['id'])
            self.assertEqual(restored['content'], {'fact': 'example'})
            self.assertEqual(restored['state'], 'candidate')
            self.assertEqual(restored['source_version'], 1)
            conn.close()

    def test_cross_role_candidate_read_is_denied(self):
        from foundry.memory import RoleMemory
        with tempfile.TemporaryDirectory() as tmp:
            conn = ledger.connect(Path(tmp) / 'ledger.db')
            ledger.create_card(conn, id='source', kind='evidence', version=1,
                lineage='source', title='Observed source', status='new',
                payload={'fact': 'example'}, created_by='lookout')
            owner = RoleMemory(conn, role='lookout')
            item = owner.propose(category='observation', content={'fact': 'private'},
                                 source_id='source', source_version=1)
            before = list(conn.iterdump())
            with self.assertRaises(PermissionError):
                RoleMemory(conn, role='scribe').candidate(item['id'])
            self.assertEqual(before, list(conn.iterdump()))
            conn.close()

    def test_invalid_provenance_rejected_without_writes(self):
        from foundry.memory import RoleMemory
        with tempfile.TemporaryDirectory() as tmp:
            conn = ledger.connect(Path(tmp) / 'ledger.db')
            memory = RoleMemory(conn, role='lookout')
            before = list(conn.iterdump())
            with self.assertRaises(ValueError):
                memory.propose(category='observation', content={'fact': 'unverified'},
                               source_id='missing', source_version=1)
            self.assertEqual(before, list(conn.iterdump()))
            conn.close()

    def test_invalid_candidate_fields_do_not_mutate_store(self):
        from foundry.memory import RoleMemory
        with tempfile.TemporaryDirectory() as tmp:
            conn = ledger.connect(Path(tmp) / 'ledger.db')
            ledger.create_card(conn, id='source', kind='evidence', version=1,
                lineage='source', title='Source', status='new', payload={}, created_by='lookout')
            memory = RoleMemory(conn, role='lookout')
            base = dict(category='observation', content={'fact': 'example'}, source_id='source', source_version=1)
            invalid = [dict(category='invented'), dict(content=[]), dict(content={}),
                       dict(source_version=True), dict(source_version=1.0), dict(source_version=2)]
            for override in invalid:
                with self.subTest(override=override):
                    before = list(conn.iterdump())
                    with self.assertRaises(ValueError):
                        memory.propose(**(base | override))
                    self.assertEqual(before, list(conn.iterdump()))
            conn.close()

    def test_export_is_owner_scoped_and_explicitly_non_authoritative(self):
        import json
        from foundry.memory import RoleMemory
        with tempfile.TemporaryDirectory() as tmp:
            conn = ledger.connect(Path(tmp) / 'ledger.db')
            ledger.create_card(conn, id='source', kind='evidence', version=1,
                lineage='source', title='Source', status='new', payload={}, created_by='lookout')
            owner = RoleMemory(conn, role='lookout')
            other = RoleMemory(conn, role='scribe')
            item = owner.propose(category='observation', content={'fact': 'owner-only'},
                source_id='source', source_version=1)
            other.propose(category='hypothesis', content={'fact': 'other-private'},
                source_id='source', source_version=1)
            before = list(conn.iterdump())
            exported = json.loads(owner.export_json())
            self.assertEqual(exported['schema_version'], 'foundry-memory-candidates-v1')
            self.assertEqual(exported['owner_role'], 'lookout')
            self.assertIs(exported['authoritative'], False)
            self.assertEqual([c['id'] for c in exported['candidates']], [item['id']])
            self.assertNotIn('other-private', json.dumps(exported))
            self.assertEqual(before, list(conn.iterdump()))
            conn.close()

if __name__ == '__main__':
    unittest.main()
