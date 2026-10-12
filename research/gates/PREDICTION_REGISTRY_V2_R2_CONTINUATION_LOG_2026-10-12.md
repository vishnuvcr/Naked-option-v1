# Registry R2 continuation — 2026-10-12

## Current outcome
The original large artifacts are available through GitHub blob retrieval but are not reliably readable via the file-content adapter, so the previous claim that source content was inaccessible is refined: the issue is audit tooling/large-file handling, not proof of corrupt bytes. A bulk shard creation attempt hit the connected tool's maximum-call limit before confirming any new shards; no shard creation is claimed.

## New artifacts
- Draft machine-readable preregistration: `research/registry/PREDICTION_PREREGISTRATION_V1.json`.
- Conservative compatibility-gate specification: `research/registry/PREDICTION_COMPATIBILITY_MATRIX_R2.md`.

## Blocking fields intentionally not guessed
Flat-return tolerance, fold dates, minimum rows/class support, missingness thresholds, bootstrap block length, seed, and multiplicity family grouping remain explicitly blocked until defined and independently approved. The 1,000 count remains unvalidated as a scientifically compatible set. No empirical fitting or holdout access.
