"""Host-bound role memory, application-level isolation only.

Instantiate in trusted host code, never from model-supplied role arguments.
No promotion or human approval API exists yet. Raw DB access bypasses this API.
"""
import json
from uuid import uuid4
from . import ledger

ROLES = frozenset({'cartographer', 'lookout', 'scribe', 'scorekeeper', 'bursar'})
SCHEMA = '''
CREATE TABLE IF NOT EXISTS foundry_memory_candidates_v1 (
 id TEXT PRIMARY KEY,
 owner_role TEXT NOT NULL,
 category TEXT NOT NULL,
 content_json TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state = 'candidate'),
 source_id TEXT NOT NULL,
 source_version INTEGER NOT NULL,
 created_at TEXT NOT NULL
);
'''

class RoleMemory:
    def __init__(self, conn, *, role):
        if role not in ROLES:
            raise ValueError('Unknown host-bound role')
        self._conn = conn
        self._role = role
        conn.executescript(SCHEMA)

    def propose(self, *, category, content, source_id, source_version):
        if category not in ('observation', 'preference', 'hypothesis', 'decision'):
            raise ValueError('Unknown epistemic category')
        if not isinstance(content, dict) or not content:
            raise ValueError('Memory content must be a nonempty object')
        if type(source_version) is not int or source_version < 1:
            raise ValueError('Source version must be a positive integer')
        source = ledger.get_card(self._conn, source_id)
        if source is None or source['version'] != source_version:
            raise ValueError('Source card and exact version are required')
        item_id = str(uuid4())
        with self._conn:
            self._conn.execute(
                'INSERT INTO foundry_memory_candidates_v1 VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (item_id, self._role, category, json.dumps(content, allow_nan=False),
                 'candidate', source_id, source_version, ledger.utcnow()))
        return self.candidate(item_id)

    def candidate(self, item_id):
        row = self._conn.execute(
            'SELECT * FROM foundry_memory_candidates_v1 WHERE id = ?', (item_id,)).fetchone()
        if row is None:
            return None
        if row['owner_role'] != self._role:
            raise PermissionError('Memory belongs to another role')
        item = dict(row)
        item['content'] = json.loads(item.pop('content_json'))
        return item

    def export_json(self):
        """Return only this host-bound role's candidates; never promotion evidence."""
        rows = self._conn.execute(
            'SELECT id FROM foundry_memory_candidates_v1 WHERE owner_role = ? '
            'ORDER BY created_at, id', (self._role,)).fetchall()
        return json.dumps({
            'schema_version': 'foundry-memory-candidates-v1',
            'owner_role': self._role,
            'authoritative': False,
            'candidates': [self.candidate(row['id']) for row in rows],
        }, allow_nan=False, sort_keys=True)

    def retrieve(self):
        # Candidates cannot be authoritative; promotion is deliberately unavailable.
        return []
