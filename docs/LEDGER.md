# Shared Ledger — data model

The ledger is the product. Everything else is a view over it.

## Storage

SQLite, three tables. In Hermes: `plugin_db("foundry")`. In the
scaffold: `data/foundry.db` (regenerated from `foundry/data/seed.json`).

```sql
CREATE TABLE cards (
  id TEXT PRIMARY KEY,          -- e.g. "identity-001", "draft-002"
  kind TEXT NOT NULL,           -- identity | evidence | draft |
                                -- revision | performance | money
  version INTEGER NOT NULL,     -- 1, 2, 3… per logical card lineage
  lineage TEXT NOT NULL,        -- stable id for the lineage (draft-001)
  title TEXT NOT NULL,
  status TEXT NOT NULL,         -- see per-kind statuses below
  payload TEXT NOT NULL,        -- JSON object, fields per kind (below)
  created_by TEXT NOT NULL,     -- cartographer | lookout | scribe |
                                -- scorekeeper | bursar | human
  created_at TEXT NOT NULL,     -- ISO 8601 UTC
  supersedes_id TEXT            -- id of the previous version, or NULL
);

CREATE TABLE links (
  from_id TEXT NOT NULL,        -- card id
  to_id TEXT NOT NULL,          -- card id
  relation TEXT NOT NULL,       -- cites | revises | measures | prices |
                                -- supersedes | derived_from
  PRIMARY KEY (from_id, to_id, relation)
);

CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id TEXT NOT NULL,
  event TEXT NOT NULL,          -- created | feedback | approved | revised
  detail TEXT,                  -- JSON
  created_at TEXT NOT NULL
);
```

Invariants: cards are never mutated in place — a new version is a
new row with `supersedes_id` set. Money is integer cents in
`payload`. Every card has `created_by` and `created_at` (provenance).

## Common fields (every card)

| Field | Type | Notes |
|---|---|---|
| `id` | string | Unique. `<kind>-<nnn>`, e.g. `draft-001` |
| `kind` | string | One of the six kinds |
| `version` | integer | Starts at 1, increments per lineage |
| `lineage` | string | Stable across versions, e.g. `draft-001` |
| `title` | string | Human-readable, e.g. "X thread: why creator tools forget" |
| `status` | string | Per-kind (below) |
| `payload` | JSON | Per-kind fields (below) |
| `created_by` | string | Bot name or `human` |
| `created_at` | string | ISO 8601 UTC |
| `supersedes_id` | string \| null | Previous version's `id` |

## Identity Card (`kind = identity`)

The Patternmaker's output. Versioned: a re-interview writes v2,
it never overwrites v1.

| Field | Type | Required | Notes |
|---|---|---|---|
| `who_you_help` | string | yes | One real person, in their words |
| `audience` | string | yes | Who they are, what they want |
| `story` | string | yes | What you lived through that they are living through |
| `pillars` | string[2–3] | yes | Topics you can talk about for hours |
| `beliefs` | string[] | yes | What you believe that most in your space don't |
| `against` | string | no | What you are against (a habit/idea, not a person) |
| `voice_examples` | string[] | yes | 3–5 example posts in your voice |
| `voice_donts` | string[] | yes | Words / moves you never use |
| `mission` | string | yes | One sentence: what you help people do |

Status: `active` | `superseded`.

## Evidence Card (`kind = evidence`)

The Prospector's output. A draft may cite it only if it has ≥2 sources.

| Field | Type | Required | Notes |
|---|---|---|---|
| `topic` | string | yes | What this evidence is about |
| `sources` | object[] | yes, ≥2 | Each: `{title, url, retrieved_at, note}` |
| `confirmed` | string[] | yes | Claims confirmed by a source |
| `unconfirmed` | string[] | no | Claims that could not be confirmed — Smith must not use them |
| `niche` | string | yes | Which pillar this serves |

Status: `active` | `stale` (older than 30 days, or superseded by newer evidence).

## Draft Card (`kind = draft`)

The Smith's output. One lineage per post; v1, v2… are separate rows.

| Field | Type | Required | Notes |
|---|---|---|---|
| `platform` | string | yes | MVP: `x` |
| `format` | string | yes | MVP: `thread` |
| `text` | string | yes | Full draft text, numbered for threads |
| `evidence_ids` | string[] | yes, ≥1 | Must link via `cites` to Evidence Cards |
| `hook` | string | yes | First line, separately editable |
| `word_count` | integer | no | Computed |
| `cost_cents` | integer | no | Model/tool cost to produce this version |

Status: `draft` | `in_review` | `approved` | `rejected` | `posted`.
A draft with status `posted` is immutable (new versions start a new lineage).

## Revision Card (`kind = revision`)

Human feedback, or a bot flag. This is how the loop learns.

| Field | Type | Required | Notes |
|---|---|---|---|
| `draft_id` | string | yes | Link (`revises`) to the Draft Card |
| `feedback_type` | string | yes | `approve` \| `tweak` \| `reject` |
| `note` | string | yes for tweak/reject | One-line note, e.g. "sharper hook" |
| `author` | string | yes | `human` (MVP) |
| `applied_in` | string \| null | no | Draft version that applied it, e.g. `draft-002` |

Status: `open` | `applied` | `dismissed`.

## Performance Card (`kind = performance`)

The Inspector's output, linked to a Draft Card (`measures`).

| Field | Type | Required | Notes |
|---|---|---|---|
| `draft_id` | string | yes | |
| `platform` | string | yes | |
| `views` | integer | no | Null until posted / measured |
| `likes` | integer | no | |
| `reposts` | integer | no | |
| `replies` | integer | no | |
| `saves` | integer | no | |
| `verdict` | string | yes | `repeat` \| `drop` \| `retry_differently` |
| `verdict_reason` | string | yes | One line, e.g. "hook format outperformed the last 3 threads" |
| `measured_at` | string | no | ISO 8601 UTC |

Status: `measured` | `estimated` (seed/demo data is `estimated` and
labelled as such on the dashboard — never presented as real metrics).

## Money Card (`kind = money`)

The Paymaster's output, linked to a Draft Card (`prices`) and optionally
to a Partnership record.

| Field | Type | Required | Notes |
|---|---|---|---|
| `draft_id` | string \| null | no | Null for period-level cards |
| `client` | string | no | MVP: `self` |
| `period` | string | no | e.g. `2026-11` |
| `cost_cents` | integer | yes | Model + tools + time (time at the creator's stated hourly rate, stored in cents) |
| `revenue_cents` | integer | yes | 0 until a deal / payout is recorded |
| `profit_cents` | integer | yes | `revenue_cents - cost_cents` (computed, stored) |
| `currency` | string | yes | `USD` (MVP) |
| `cost_breakdown` | object | no | `{model_cents, tools_cents, time_cents}` |
| `partnership_id` | string \| null | no | Link to a Partnership record |

Status: `draft` | `final`.

### Partnership record (stored as a Money-kind card with `record_type`)

| Field | Type | Notes |
|---|---|---|
| `record_type` | `partnership` | |
| `brand` | string | |
| `deal_status` | `pitched` \| `terms` \| `delivered` \| `paid` | |
| `amount_cents` | integer \| null | Agreed amount, if any |
| `deliverables` | string[] | |
| `disclosure` | boolean | Paid-partnership disclosure required — always true for sponsored items |
| `due_date` | string \| null | ISO date |

### Tax record (stored as a Money-kind card with `record_type`)

| Field | Type | Notes |
|---|---|---|
| `record_type` | `tax` | |
| `period` | string | e.g. `2026-Q4` |
| `income_cents` | integer | |
| `expense_cents` | integer | |
| `estimated_tax_cents` | integer | **Estimate only**, labelled as such |
| `export_format` | `csv` | |

**Tax is tracking/export only. No advice, no filing, no definitive
"you owe" claim.**

## Worked example (seed data)

- `identity-001` v1 — Patternmaker, "Creator who helps builders…"
- `evidence-001` v1 — Prospector, 2 sources, topic "creator tools forget"
- `draft-001` v1 — Smith, cites `evidence-001`, status `in_review`
- `revision-001` — unverified author (seeded demo data, not a real human review), `tweak`, "sharper hook", applied in `draft-002`
- `draft-002` v2 — Smith, supersedes `draft-001`, status `in_review` (seeded demo data; approval is disabled — no trusted human review channel yet)
- `performance-001` — Inspector, measures `draft-002`, verdict `repeat`
- `money-001` — Paymaster, prices `draft-002`, profit computed from seed costs
- `money-002` — Paymaster, partnership record, one seeded deal, status `terms`
