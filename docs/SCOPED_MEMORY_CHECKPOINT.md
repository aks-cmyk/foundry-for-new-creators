# Scoped memory checkpoint

Implemented in isolated source only; not installed or connected to bot tools.

- Host-created RoleMemory binds one of the five existing role IDs. Do not expose its constructor through model arguments.
- Additive SQLite candidate table leaves cards/links/events intact. Candidates survive connection restart.
- Candidate reads reject another bound role. This is application compartmentalisation, not OS or hostile-host isolation.
- Proposals require an existing source card at its exact version. Provenance existence is not evidence quality or source approval.
- Candidates never enter authoritative retrieval. There is intentionally no promotion or approval implementation; retrieve returns an empty list.
- UUID identifiers and a transactional candidate insert are used.

Unfinished: host capability integration, category/content validation and source-kind policies, concurrent migration coverage, human-reviewed promotion, active retrieval, grants, corrections/invalidation, expiry, exports and live Desktop journey. Public source IDs and raw database access are not security capabilities. Do not claim scoped memory is complete or deploy it as such.

Verification: three new real-SQLite tests (restart/non-authoritative candidate, denied cross-role read without writes, missing provenance rejection without writes); existing four-method integrity suite also passes. RED/GREEN logs are in ../baseline-evidence/memory-*.log. Source-version mismatch, migration concurrency and actual host role binding require additional coverage.
