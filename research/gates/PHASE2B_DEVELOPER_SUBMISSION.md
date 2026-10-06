# Phase 2B Developer Submission

## Objective

Move from data architecture to actual point-in-time source acquisition and independent cross-source reconciliation.

## Implemented

- Added explicit BSE SENSEX and BSE derivatives source rows.
- Added official NSE contract-information/lot-size source.
- Added global macro/cross-market source manifest.
- Added publication/availability alignment rules.
- Added official NSE legacy and UDiFF sample acquisition with cache-hit handling.
- Added official archive schema validator.
- Added immutable snapshot manifest generator with SHA-256 and row counts.
- Added HF_TOKEN-aware metadata probe.
- Added actual HF derived-reference acquisition with cache.
- Added official-vs-HF option reconciliation script.
- Added derived-data license restrictions.
- Added static AST/manifest/workflow validators.
- Expanded GitHub Actions workflow with Python dependency installation, raw cache, HF acquisition and reconciliation.

## Gate requirements

Phase 2B is not considered passed merely because scripts exist. The workflow artifact must demonstrate:
- official sample acquisition success;
- UDiFF/legacy schema pass;
- nonempty snapshot manifests and hashes;
- HF reference acquisition;
- nonzero matched option keys;
- acceptable price reconciliation statistics;
- no unexplained timezone/date shift;
- no duplicate active contract keys;
- reproducible cache behavior.

## Developer instruction to tester

Independently review the new scripts for syntax, logical correctness, numerical comparison rules, data-source precedence, cache integrity, license treatment, and leakage. Treat any unobserved workflow result as pending rather than green.
