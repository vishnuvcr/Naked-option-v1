# Prediction registry R2 continuation — shard tooling checkpoint

Date: 2026-10-12
Branch: `phase-08-prediction-developer`
Status: **IMPLEMENTED, NOT YET EXECUTED OR TESTER-APPROVED**.

## Work completed in this checkpoint

- Added `scripts/shard_prediction_registry.py`, a deterministic utility to split a JSON record collection into small JSONL shards, emit a per-shard index (record count, byte length, first/last ID, SHA-256), and verify the written files.
- The shard format is explicitly defined as UTF-8 JSONL, sorted JSON keys, compact separators, and one LF after each record. Hashes cover the exact emitted bytes.
- Added `scripts/test_shard_prediction_registry.py` with tests for the standard SHA-256 `abc` known vector, shard round-trip/integrity detection, duplicate-ID rejection, and ambiguous input rejection.
- Commits: utility `a0ce5b04346c50c81dd8fed9fdac9b3a5f3f4cce`; tests `57760230594c8829e8d816a156696b595084e8f6`.

## Important limits

- These files have been committed but **have not been run in a local or hosted test environment in this checkpoint**. The tests are not reported as passing.
- The sharding utility only establishes file-level integrity and auditability. It does not determine whether a method is scientifically distinct or compatible with an inference operator.
- No method/config shards have been generated from the current registry yet. Do not claim that shard outputs exist.
- The method registry, configuration manifest, labels, and statistical preregistration remain drafts. All empirical fitting and untouched-holdout access remain prohibited.
- The known-vector check is included in both utility startup and the test suite; independent execution is still required.

## Next required steps

1. Independent tester reviews the utility and test file at exact commit `57760230594c8829e8d816a156696b595084e8f6`, and returns PASS/REQUEST CHANGES on `phase-08-prediction-tester`.
2. If approved, run the unit tests in the gated workflow.
3. Run the splitter against the actual method registry and configuration inputs, with explicit record-list keys, then verify every emitted shard and index.
4. Add compatibility filtering and a separate semantic-distinctness audit; do not count blocked combinations toward 1,000.
5. Freeze the remaining label/sample/fold/multiplicity/bootstrap fields and implement synthetic restart/resource/failure-log tests.
6. Submit all exact artifact hashes for a fresh tester decision. Empirical execution stays blocked until both registry and synthetic-runner gates pass.

## Role handoff

**Developer → Tester:** review the implementation and tests at the exact commit above. Check path resolution, canonical byte definitions, duplicate IDs, malformed records, hash/count/range verification, and failure behavior. Do not approve scientific validity or empirical execution from this utility alone.

**Tester → Developer:** report a hash-pinned PASS/REQUEST CHANGES. If code-level concerns exist, name exact file/line and required regression. No empirical fitting or holdout access until all registry and runner gates pass.
