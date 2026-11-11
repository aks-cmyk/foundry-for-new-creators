# Approval integrity checkpoint

Implementation commit: 4936a7a (isolated working copy only).

## Verified
- Direct approval tool, approval feedback tool and dashboard feedback function reject approval without database writes, including forged `author`, `by`, `approved` and caller `actor` values.
- Feedback may still create revisions, but authorship is `unverified`, never asserted human.
- Four regression test methods pass, including the three approval-route subtests. Original smoke suite also exits zero on Python 3.15.2.
- RED/GREEN logs are in ../baseline-evidence/approval-{red,green}.log and authorship-{red,green}.log.

## Explicit limitations
- This disables approval; it does NOT implement an authenticated human-review flow.
- Desktop has not been loaded. Its approve button currently receives a backend error. Static demo HTML still has simulated client-only approval wording; it is NOT proof and must not be used as a real approval demo.
- Existing seeded/historical approved records are not retroactively authenticated or migrated. No release/publishing decision may rely on their status alone.
- Code able to write SQLite directly remains outside the API trust boundary. No sandbox/security claim is made.
- Required next slice: trusted host review adapter, exact content/version digest binding and replay/stale-content rejection, followed by UI/error-state work and migration of approval provenance. Do not accept a boolean or actor string as authorization.
- Scoped-memory implementation and live Hermes integration remain outstanding. No unattended workers, installation, cloud sharing or external publication occurred.
