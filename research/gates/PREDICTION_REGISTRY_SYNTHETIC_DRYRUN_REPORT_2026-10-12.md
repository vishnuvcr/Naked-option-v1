# R2 Prediction Registry Synthetic Dry-Run Report — 2026-10-12

**Status: PASS — synthetic execution plumbing only. No prediction evidence or empirical authorization.**

## Pinned execution

- Developer branch commit used by successful full run: `9319856912efb945ce9ac5162d3ec0b173551af7`.
- GitHub Actions run: [38251707853](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38251707853).
- Workflow: `.github/workflows/prediction-registry-synthetic-dryrun.yml`.
- Source manifests and registry index were Git-blob-pinned by preregistration. The data manifest explicitly says `encrypted_only=true`; this job verifies metadata and never decrypts or opens the market dataset.
- Full run result artifact: `r2-prediction-synthetic-dryrun` (GitHub Actions artifact ID `11749150256`). It contains `results.jsonl`, `summary.json`, `checkpoint.json`, and empty `errors.jsonl`.

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

The two terminal counts sum to 64,000. The `SYNTHETIC_MOCK_ONLY` rows are deterministic toy-probability scores from synthetic samples—not fitted estimators, market outcomes, or accepted performance metrics. Compatibility-blocked tasks are retained as explicit outcomes rather than silently dropped.

## Artifact fingerprint

- Full synthetic `results.jsonl` SHA-256: `6a45f139077bfa058f240a3268023f061ee3ca3ca51d84e5f3307c527a765f6b`.
- File size: 36,955,576 bytes.
- Synthetic run seed: `2026101208`.
- Elapsed time: 45.65 seconds on the GitHub-hosted runner (not a production-runtime benchmark).
- Registry/index/configuration hashes, data-manifest pins and preregistration digest are recorded inside the hosted `summary.json`.

## Restart and failure-handling tests

The test suite passed in the successful synthetic workflow:

1. Deterministic interruption after task 17, checkpoint creation, safe resume, and byte-for-byte equality with a clean 80-task synthetic run.
2. Injected exception creates a JSONL error row with exception type/message/traceback hash and a resumable failure checkpoint.
3. Registry loader validates the full 8,000-config universe before the one-task smoke assertion.

The earlier synthetic test failure was caused by writing the Git blob NUL separator as the two literal characters `\\0` rather than a NUL byte. The helper was corrected and the run passed. Another regression assertion expected different holdout wording than the actual frozen preregistration; the assertion was corrected to match the specification. These mistakes and corrections are logged in `research/ERROR_LOG.md`.

## Planning-only resource estimate

These are explicit engineering assumptions, **not measured runtime for any real estimator or market dataset**.

| Estimate | Result |
|---|---:|
| Design-compatible configurations pending all gates | 3,408 |
| Hypothetical estimator fit calls (`3,408 × 8 × 4`) | 109,056 |
| Assumed serial CPU time for entire compatible sweep | 1,173.33 hours |
| Assumed feature matrix | 20,000 × 1,920 float64 |
| Assumed feature matrix memory | 293.0 MiB |
| Peak single-worker family memory estimate | 1,671.9 MiB |
| Four-worker peak-memory lower-bound estimate | 6,687.6 MiB |

The estimate assumes five CPU seconds for a baseline fit on 20,000 rows/1,920 features and family-specific multipliers. It requires calibration using isolated, representative benchmark fixtures after the scientific gates are approved and before any real fitting. It must not be used as a production promise.

## Current gate decision

- **Registry file/hash/count integrity:** hosted CI PASS (separate repair + clean-audit runs are linked in `research/STATUS.md`).
- **Synthetic orchestration, restart, failure logging and resource-estimate reporting:** PASS for test plumbing.
- **Scientific compatibility/preregistration gate:** still BLOCKED pending the independent tester's hash-pinned review.
- **Empirical model fitting and untouched-holdout access:** NOT AUTHORIZED.

Next developer step is to fix any findings from independent review, complete adapter-specific numerical tests, and improve the execution-budget estimate with small synthetic benchmark fixtures. Developer must not proceed to real-data prediction runs without a new tester PASS.
