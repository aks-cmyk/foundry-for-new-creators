# Scoped memory checkpoint

Implemented in isolated source only; not installed or connected to bot tools.

- Host-created RoleMemory binds one of the five existing role IDs. Do not expose its constructor through model arguments.
- Additive SQLite candidate table leaves cards/links/events intact. Candidates survive connection restart.
- Candidate reads reject another bound role. This is application compartmentalisation, not OS or hostile-host isolation.
- Proposals require an existing source card at its exact version. Provenance existence is not evidence quality or source approval.
- Candidates never enter authoritative retrieval. There is intentionally no promotion or approval implementation; retrieve returns an empty list.
- UUID identifiers and a transactional candidate insert are used.

Unfinished: host capability integration, source-kind policies, concurrent migration coverage, human-reviewed promotion, active retrieval, grants, corrections/invalidation, expiry, exports and live Desktop journey. Public source IDs and raw database access are not security capabilities. Do not claim scoped memory is complete or deploy it as such.

Verification: five real-SQLite test methods (restart/non-authoritative candidate, denied cross-role read without writes, missing provenance rejection without writes, invalid-field rejection without writes, owner-scoped non-authoritative export); the four-method integrity suite also passes. Re-verified in this repo after adoption: see hidden_files/adoption-2026-11-10/. Migration concurrency and actual host role binding require additional coverage.
