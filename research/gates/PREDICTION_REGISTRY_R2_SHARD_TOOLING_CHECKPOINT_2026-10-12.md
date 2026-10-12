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


## CI result update — 2026-10-12

- Hosted GitHub Actions run [38240927039](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38240927039) completed successfully on workflow commit `8fd619332155ba8cd68614c5a96a9ab81de37433`.
- Four unit tests passed (0.072 seconds): SHA-256 known vector, shard round-trip/tamper detection, duplicate-ID rejection, and ambiguous-input rejection. The workflow's independent SHA-256 known-vector step also passed.
- This is developer CI evidence only; independent tester review is still requested. No method/config shards have been generated. Scientific compatibility, label/statistical freeze and synthetic restart/resource gates remain unresolved; empirical fitting and holdout access remain prohibited.

## Validator hardening follow-up — 2026-10-12

- After inspecting the first utility version, hardened stable-ID handling (exactly one recognized non-empty ID field), explicit empty-list handling, missing-key errors, deterministic source basename recording, supported-kind checks, and fail-closed index validation.
- Verification now rejects unsafe/duplicate shard paths, malformed index structures, missing final LF, CR bytes, non-canonical JSON record encoding, duplicate IDs, and count/hash/byte/range mismatches.
- Expanded adversarial tests for empty lists, missing keys, ambiguous IDs, canonical JSONL, malformed indexes, and path traversal.
- Commits: validator 9c6db727656d351742e3f2a93a7d8c6e3508aa8b; expanded tests 49c60997b12aeb71a93a891b3c895cd6a34445b9.
- Workflow run 38241541882 passed on the validator commit, but its log ran the earlier four-test version because the expanded test update followed immediately afterward. The expanded eight-test suite is running as [run 38241558360](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38241558360); its result must be checked before reporting the new test set as passed.
- This remains utility-only. No registry shards have been generated; no scientific/empirical gate is cleared.

**Developer → Tester:** independently inspect the updated validator and adversarial tests at 49c60997b12aeb71a93a891b3c895cd6a34445b9, and inspect the exact hosted test logs.
**Tester → Developer:** issue a hash-pinned scoped decision and name any residual defects; do not authorize fitting from shard integrity alone.

## Adversarial regression correction — 2026-10-12

- Expanded suite run [38241558360](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38241558360) executed 8 tests; 7 passed and 1 failed because the malformed-index fixture incorrectly expected a shard-count mismatch while declaring one shard and a count of one. The failure was in the test expectation, not a demonstrated validator defect.
- Corrected the fixture to declare shard_count=2 while providing one entry in commit `1fe2a290cf933d349ece0691929ee65f669d2b9c`. A fresh run must pass before the expanded suite is reported green.
- Failure is preserved as non-passing evidence. Scientific gate remains blocked; no shards or empirical fitting.
