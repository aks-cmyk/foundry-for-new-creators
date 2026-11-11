# Approval integrity checkpoint

Implementation: Mac Studio candidate bde3c03, adopted as d257c2b;
fixture fixes in this commit. Re-verified in this repo after adoption:
see hidden_files/adoption-2026-11-10/ (memory / integrity / smoke /
validate / doctor logs).

## Verified
- Direct approval tool, approval feedback tool and dashboard feedback function reject approval without database writes, including forged `author`, `by`, `approved` and caller `actor` values.
- Feedback may still create revisions, but authorship is `unverified`, never asserted human.
- Four regression test methods pass, including the three approval-route subtests. Original smoke suite also exits zero on Python 3.15.2.

## Explicit limitations
- This disables approval; it does NOT implement an authenticated human-review flow.
- Desktop has not been loaded in a live `hermes desktop`. Its Approve button is disabled with an honest label (2026-11-11) until a trusted human channel exists.
- Existing seeded/historical approved records are not retroactively authenticated or migrated. No release/publishing decision may rely on their status alone. (2026-11-11: the seed fixture itself was fixed — draft-002 is now `in_review`, revision-001 authorship `unverified` — but no historical approval was ever authenticated.)
- Code able to write SQLite directly remains outside the API trust boundary. No sandbox/security claim is made.
- Required next slice: trusted host review adapter, exact content/version digest binding and replay/stale-content rejection, followed by UI/error-state work and migration of approval provenance. Do not accept a boolean or actor string as authorization.
- Scoped-memory implementation and live Hermes integration remain outstanding. No unattended workers, installation, cloud sharing or external publication occurred.
