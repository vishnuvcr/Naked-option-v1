# Offline preflight correction checkpoint — 2026-10-11

## Scope
Developer-only correction to the structural dataset preflight. No real dataset was opened or changed, no network data source was queried, and no model, holdout, or strategy test was run.

## Changes
- Reworked `scripts/offline_dataset_preflight.py` so its disk-backed SQLite duplicate index is closed and removed in a `finally` block on both success and failure.
- Replaced lexical timestamp extrema with numeric/ISO timestamp normalization and explicit parse-error counts.
- Incomplete composite keys are excluded from duplicate claims; missing recognized key schemas report `NOT_ESTIMABLE`.
- Expanded synthetic regression tests for corrupt/truncated gzip, malformed row width, duplicate composite keys, absent key fields, incomplete keys, timestamp parsing, nested report paths, and temporary-index cleanup.
- Developer commits: preflight implementation `d7095ea89f697b4d0ba6df8b771cc38781295d09`; expanded tests `ca500c3b931c8e8204ec59f5b2baa57bb19170d7`.

## Verification state
- GitHub Actions should run the synthetic-only workflow on these developer-branch changes; no verified run receipt is available in this checkpoint.
- The 4.75 GB CSV is not mounted in this tool execution environment. The new code has not been run against the real dataset.
- The workflow still needs its action-pinning policy confirmed. The attempted workflow edit was blocked and was not committed.

## Gate state
- Synthetic tests: awaiting verified CI receipt.
- Real-file preflight: NOT AUTHORIZED.
- Modelling readiness / fitting / scoring: CLOSED.
- Holdout: CLOSED.
- New data requests: CLOSED.
- Strategy/P&L: CLOSED.

Developer → Tester: Review exact commits `d7095ea89f697b4d0ba6df8b771cc38781295d09` and `ca500c3b931c8e8204ec59f5b2baa57bb19170d7`; require a verified synthetic CI pass and check cleanup and timestamp edge cases.
Tester → Developer: Do not execute the real-file preflight or progress to fitting unless the exact-snapshot gate passes.
