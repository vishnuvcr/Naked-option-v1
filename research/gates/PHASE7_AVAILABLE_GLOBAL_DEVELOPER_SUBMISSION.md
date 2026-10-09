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
