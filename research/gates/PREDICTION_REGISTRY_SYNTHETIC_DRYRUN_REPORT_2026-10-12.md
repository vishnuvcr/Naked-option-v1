# R2 Prediction Registry Synthetic Dry-Run Report — 2026-10-12

**Status: PASS — synthetic execution plumbing only. No prediction evidence or empirical authorization.**

## Pinned execution

- Developer branch commit used by the successful, commit-pinned full run: `6d4787348d7b0b794e210026ceddcea19192eccc`.
- GitHub Actions run: [38254175308](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38254175308).
- Workflow: `.github/workflows/prediction-registry-synthetic-dryrun.yml`.
- The committed dataset manifest explicitly says `encrypted_only=true`. The workflow verifies metadata and hashes but does not decrypt or open market data.
- Full result artifact: GitHub Actions artifact `r2-prediction-synthetic-dryrun`, ID `11749635242`, including `results.jsonl`, `summary.json`, `checkpoint.json`, and empty `errors.jsonl`.

## Execution counts

| Measure | Result |
|---|---:|
| Configurations × outer-fold tasks | 8,000 × 8 = 64,000 |
| Result rows | 64,000 |
| `SYNTHETIC_MOCK_ONLY` | 27,264 |
| `BLOCKED_COMPATIBILITY` | 36,736 |
| Runtime exceptions recorded | 0 |
| Error JSONL rows | 0 |
| Market data opened | No |
| Model fitting performed | No |
| Untouched holdout accessed | No |
| Scientific evidence | No |

The terminal-status counts sum to 64,000. The `SYNTHETIC_MOCK_ONLY` rows are deterministic toy-probability scores from synthetic samples—not fitted estimators, market outcomes, or accepted performance metrics. Compatibility-blocked tasks remain explicit rather than silently disappearing.

## Artifact fingerprint

- Full synthetic `results.jsonl` SHA-256: `6a45f139077bfa058f240a3268023f061ee3ca3ca51d84e5f3307c527a765f6b`.
- File size: 36,955,576 bytes.
- Synthetic seed: `2026101208`.
- Hosted wall time: 46.96 seconds (not a production-runtime benchmark).
- The hosted `summary.json` records source Git blob SHA-1 pins (distinct from content SHA-256) and registry/preregistration digests. The workflow asserts the checkout commit equals the triggering `GITHUB_SHA`.

## Restart and failure-handling tests

The latest hardened, commit-pinned full synthetic workflow [38254175308](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38254175308) passed all 10 statistical utility tests plus the restart and failure-handling tests for: deterministic interruption after task 17, checkpoint creation, safe resume, and byte-for-byte equality with a clean 80-task run; injected exception logging to JSONL with exception type/message and traceback hash; and loading/validating the full 8,000-config registry before a one-task smoke assertion.

Two defects were caught and corrected: the Git-blob verifier originally used the two literal characters `\\0` instead of the NUL byte; a test also expected holdout wording different from the frozen preregistration. Both corrections are recorded in `research/ERROR_LOG.md`.

## Planning-only resource estimate

**These are assumption-based planning values, not measured runtime for actual estimators or market data.**

| Estimate | Result |
|---|---:|
| Design-compatible configurations pending remaining gates | 3,408 |
| Hypothetical fit calls (`3,408 × 8 × 4`) | 109,056 |
| Assumption-based serial CPU estimate | 1,173.33 hours |
| Assumed feature matrix | 20,000 × 1,920 float64 |
| Assumed feature matrix memory | 293.0 MiB |
| Peak single-worker family memory estimate | 1,671.9 MiB |
| Four-worker peak-memory lower-bound estimate | 6,687.6 MiB |

The estimate assumes five CPU seconds per baseline fit on 20,000 rows/1,920 features plus family multipliers. It requires calibration on representative synthetic estimator benchmarks before actual fitting and must not be interpreted as a production runtime promise.

## Gate decision

- **Registry file/hash/count integrity:** hosted CI PASS.
- **Synthetic orchestration, checkpoint/restart, failure logging, statistical utility tests:** PASS. The same commit-pinned workflow included the log-loss/Brier/balanced-accuracy/calibration, block-bootstrap and BY-FDR regression suite.
- **Actual per-family estimator performance:** NOT BENCHMARKED; assumptions only.
- **Scientific compatibility/preregistration gate:** BLOCKED pending independent tester review.
- **Empirical fitting and untouched-holdout access:** NOT AUTHORIZED.

The next developer step is to resolve tester findings, complete adapter-specific numerical tests, and calibrate resource assumptions with representative synthetic estimator benchmarks. No real-data model runs until a new hash-pinned tester PASS.


The same hosted job reports `Ran 10 tests` for `scripts/test_prediction_statistics.py`; all passed, including strict label/parameter type checks and the both-classes requirement for calibration.
