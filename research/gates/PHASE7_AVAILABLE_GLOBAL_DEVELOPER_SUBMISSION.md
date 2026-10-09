# Developer Submission — Available-Data Prediction Extension

Date: 2026-10-10
Developer branch: `phase-07-developer`
Independent review branch: `phase-07-tester`
Scope: prediction only; no options strategy or Phase 8 work.

## User-directed research change

The user asked to continue experimenting with methods using available data rather than stopping each method solely because a data layer is unavailable. This submission implements a finite, point-in-time-safe extension focused first on peer/global daily prices and other public cross-asset series that may be retrieved free. Missing sources do not stop unrelated candidate tests; they remain explicitly marked `BLOCKED_DATA`.

This extension does not falsify missing data, relax point-in-time rules, overwrite frozen Phase 6/7 evidence, or open the final untouched holdout.

## Submitted files

- `research/phase7/AVAILABLE_DATA_PREDICTION_SPEC.md` — pre-registered question, candidate methods, horizon grid, PIT joins, metrics, bootstrap family gate and interpretation limits.
- `scripts/acquire_global_history.py` — free Yahoo Finance chart acquisition for SENSEX, Bank Nifty, S&P 500, Nasdaq, Nikkei, Hang Seng, Cboe VIX, USD/INR, gold, crude and India VIX; source-by-source status, cache, timezone conversion and SHA-256 manifest.
- `scripts/run_phase7_available_global.py` — strict earlier-session as-of features, expanding walk-forward logistic forecasts, H-session label purge, fixed retraining schedule and family-level moving-block Brier inference.
- `scripts/test_phase7_available_global.py` — strict-as-of, causal feature, future-label mutation, metric reconciliation, reproducible bootstrap and source-status fixtures.
- `.github/workflows/phase-07-available-global.yml` — automatic developer-branch workflow plus manual dispatch; regression is always first, while empirical execution is fail-closed behind a tester report/approval JSON and protected-file SHA-256 validation.
- `research/ERROR_LOG.md` — two initial fixture failures are logged with root cause, correction and non-evidence disposition.

## Regression history to date

- Workflow run [#1 / 37983764374](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37983764374): failed because the strict-as-of fixture's expected first row was wrong. No empirical run.
- Workflow run [#3 / 37983879350](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37983879350): failed because a source-map dictionary was incorrectly constructed as a pandas DataFrame in the fixture. No empirical run.
- Workflow run [#4 / 37983973028](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37983973028): regression suite passed after those corrections. No tester approval was present and the empirical job remained skipped.
- A cache freshness refinement was then made so cached global data older than ten calendar days is refreshed. Workflow [#5 / 37984078118](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37984078118) was in progress at submission preparation; its final result must be checked before any empirical approval.

The failed runs are preserved as regression-only non-evidence. They contain no prediction metrics and cannot be cited as empirical findings.

## Tester requests

Independently verify:
1. Exact method/status grid against the pre-registration.
2. Every source timezone and the strict `source_date < NIFTY_date` merge behavior.
3. Return/volatility feature causality and source manifest SHA-256 validation.
4. Horizon label construction and the `start - H` purge boundary.
5. Training-only standardization, fixed refit blocks, no result-driven feature/model tuning.
6. Confusion counts, accuracy, AUC/Brier/log-loss bounds and common-row family bootstrap.
7. Source-specific failure isolation, composite membership freezing, and proper `BLOCKED_DATA` reporting.
8. Workflow fail-closed behavior: no empirical job without independent approval for the exact protected hashes.
9. All three test fixtures and any issues not captured by current regression coverage.

Do not approve based only on a green workflow. If any defect is found, issue REQUEST CHANGES and archive the exact failure in the tester branch; do not authorize empirical execution.

## Disposition

**Pending independent tester code/spec review. Empirical prediction execution is not yet authorized.**

**Developer → Tester:** Review the exact developer snapshot and independently determine whether it is safe to run one empirical prediction batch.

**Tester → Developer:** Return a report with the exact reviewed commit, independent checks, protected-file SHA-256 values, all discrepancies, and explicit authorization or rejection for the empirical run.


## Developer resubmission after independent tester REQUEST CHANGES — 2026-10-10

The initial exact-snapshot review was rejected and remains preserved on phase-07-tester. The developer corrected the reported items before any empirical run:

- G13 now follows the frozen specification: equal-weight means of raw causal 1-session and 5-session log returns from the pre-run frozen constituent set; a missing constituent makes that row unavailable rather than changing weights.
- adjust_horizon_pvalues now always adjusts against all five registered horizons, while reporting the number actually executed separately.
- Each executed candidate includes paired_baseline_comparison computed on the exact rows used for that candidate; the full _BASELINE metric cell remains an explicitly broader, feature-mask-independent diagnostic.
- Added scripts/validate_phase7_available_global_results.py and scripts/test_validate_phase7_available_global_results.py; wired both into regression, protected-snapshot hashes, exact approval allowlist, and the hosted output-validation step.
- Regression additions check raw-vs-zscore distinction/fixed G13 membership, five-horizon Bonferroni with fewer available tests, paired baseline rows, missing baseline cells, wrong family adjustment, blocked-data reasons, pair-sample mismatch, and family-inference counts.
- Spec numbering and baseline sample semantics were clarified without changing labels, horizons, candidate universe, source-date cut-off, walk-forward training/purge, bootstrap, or holdout boundary.

### Current reviewed blobs

- Spec: feecc38f36711575eb10e6150b18cea32f35ee27
- Acquisition: 401fdacd3aa562b4907d422eb296fec502aa8f3c (unchanged)
- Predictor: af03f554dc3952b17678544c951efff89ed6ce5d
- Predictor regression tests: 34dd77ce9f16e339a5785f3ee337bd8a29b1e7c5
- Complete result validator: 606b504552a2e437a170b5fbe0d95d3c37d5e467
- Validator regression tests: bcae89c03c4047dc60f3a3d0fb9037a33c8c5410
- Workflow: 4ebdeece0060b0dd51d602085afb558705dbaee1
- Requirements: requirements-phase7-available.txt (must be hashed by workflow gate as protected path)

**Important execution state:** a successful hosted regression run has not yet been verified in the current tool session. These changes are not an approval and no empirical run has been authorized. Do not prepare or mirror an execution-approving JSON. A fresh tester report must examine the exact updated blobs and the automatic hosted regression result before deciding whether one empirical run may proceed.

**Developer → Tester:** Re-review these exact blobs independently. Verify formulas, missingness masks, family p-value adjustment, paired row equality, schema validator and workflow protected path set; record the exact CI run if visible. Do not authorize empirical execution if the hosted regression has not passed or any mismatch remains.

**Tester → Developer:** Return PASS / PASS WITH SCOPED RESTRICTIONS or REQUEST CHANGES with verified hashes and explicit one-run authorization status. Keep the old rejection as historical record; no strategy work or result promotion is permitted by a code review alone.


## Auditability addendum — row-level forecast panel (2026-10-10)

A further review found the previous output stored only aggregates, limiting independent reproduction of candidate metrics and the moving-block family test. Before any empirical execution, the developer added a row-level panel and made the output validator recalculate results from it.

### Current exact blobs after this addendum

- Spec: 71d2d8a9cfef5c138a75715c88bd2f17be3a2afc
- Acquisition: 401fdacd3aa562b4907d422eb296fec502aa8f3c
- Predictor with panel export: 3d4f7255755b2d55fe3bbce00f8a95e8d0e5c9b6
- Predictor regression tests: 34dd77ce9f16e339a5785f3ee337bd8a29b1e7c5
- Complete metric/panel validator: 21c63426ec055eed85c158280d8e0b4123c82ab1
- Validator regression tests: 8651a96f5889a699659871f93bba25b133acef15
- Workflow with panel artifact retention: c6fbf25e62a9882064cc350d558fd560f3afce35
- Requirements: f54f873bbba4cfd010cabc32bb4432f581520e7f

The panel is written to data/reports/available_global_prediction_panels.csv. Each eligible date/horizon has a baseline row and each registered candidate that can be run has a candidate row, including the realized return/direction, prediction probability or explicit abstention, paired baseline probability, source/feature identifiers and cell status. The JSON output records the panel path and SHA-256. The artifact validator now checks the panel hash, label/return signs, key uniqueness, row alignment, exact recomputation of model and paired-baseline metrics, common-row family mean Brier improvements, and reproducibility of the 500-replicate, 20-row moving-block bootstrap p-value.

The panel is retained as a GitHub Actions artifact beside the summary JSON, source manifest and cached source files. If there is no forecast panel, the schema must still be present, and an empty panel passes only when the aggregate grid has no executable forecasts and all baseline cells are not applicable.

This improvement was made before any empirical run; it is not a result and does not authorize a run. The full correction cycle must be independently reviewed again.

**Developer → Tester:** Inspect the latest exact blobs above. Recompute a synthetic valid panel/metric/family case and make sure mutations to probabilities, labels, missingness, or the p-value make validation fail. Do not approve empirical execution until the hosted regression outcome is verified and every protected hash matches.

**Tester → Developer:** Return a new exact-snapshot decision with tested panel reconciliation findings, CI run evidence if available, and explicit empirical-authorization status. Keep the original request-changes report as historical record and do not create an approval manifest without a pass.


## Final exact-snapshot inventory for re-review — 2026-10-10

The panel validation was tightened once more after adding its first regression fixture: candidate baseline probabilities must agree with the baseline panel for every row, predicted-up mean return is recomputed, invalid row flags/methods are rejected, an empty panel cannot support a family result, and the CSV is written with 17 significant digits for round-trip float fidelity.

- Frozen spec: 71d2d8a9cfef5c138a75715c88bd2f17be3a2afc
- Acquisition: 401fdacd3aa562b4907d422eb296fec502aa8f3c
- Predictor: a3026472cea648198485513e77df74cee706a46a
- Predictor regressions: 34dd77ce9f16e339a5785f3ee337bd8a29b1e7c5
- Complete result/panel validator: ad2cc6b617224e4c6cddd85b1b8126bc5021cc06
- Validator regressions: 8c580f80f4bdfc8e8be38997113168f008ad88ae
- Workflow: c6fbf25e62a9882064cc350d558fd560f3afce35
- Acquisition requirements: f54f873bbba4cfd010cabc32bb4432f581520e7f

The hosted workflow is set to trigger for the protected predictor/spec/test/validator/workflow files, run both regression suites, print the protected file hashes, fail closed without tester approval, and upload the row-level forecast panel with summary/source artifacts. However, the available commit-status endpoint currently returns no checks for the latest commits and the connector exposes no general workflow-run listing/dispatch action. Treat the hosted test result as **unverified**, not green. The tester must not authorize an empirical run until the actual workflow regression result is visible and passes. No approval JSON has been created.


## Superseding exact blob references — final panel audit version

The authoritative current file blob identifiers are the following (these supersede any earlier list in this submission; the hosted sha256sum output is still required separately):

- Spec: 71d2d8a9cfef5c138a75715c88bd2f17be3a2afc
- Acquisition: 401fdacd3aa562b4907d422eb296fec502aa8f3c
- Predictor: eec628a0c4760e862c2107ecb4b3262c29da2150
- Predictor regressions: 34dd77ce9f16e339a5785f3ee337bd8a29b1e7c5
- Result/panel validator: 6654b8f083083b666be3ee796a53687e64ce4389
- Validator regressions: 04da3f067a80270a09369104937af4d2989be2ff
- Workflow: c6fbf25e62a9882064cc350d558fd560f3afce35
- Requirements: f54f873bbba4cfd010cabc32bb4432f581520e7f

No hosted test result is verified in this session. Do not convert this list of source blob IDs into an approval hash manifest; that manifest must be based on the workflow's actual SHA-256 output and a fresh independent tester decision.


## Additional protected-input audit — NIFTY acquisition script (2026-10-10)

A workflow audit found that the empirical job executes scripts/acquire_nifty_daily_history.py, but the script was absent from the protected SHA-256 set and the push path trigger. This meant the data-acquisition logic for the primary NIFTY input was not covered by the exact-snapshot approval hash gate.

Correction on the developer branch:
- Added scripts/acquire_nifty_daily_history.py to the workflow push-path triggers.
- Added it to the exact approval protected-path allowlist.
- Added it to the workflow's sha256sum output list.

This is a gate-integrity correction, not an empirical result. The workflow changed again, so the earlier static tester report does not cover this latest workflow blob. A new independent review and observable hosted regression pass remain mandatory; empirical execution remains unauthorized.
