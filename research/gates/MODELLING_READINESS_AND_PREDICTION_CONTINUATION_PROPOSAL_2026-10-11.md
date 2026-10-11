# Modelling-readiness and prediction continuation gate

Date: 2026-10-11
Role: Developer submission
Scope: prediction only; no options P&L or strategy selection.

## Decision requested
Authorize a bounded, reproducible, prediction-only modelling-readiness preflight against the exact offline export. This proposal does not itself authorize fitting, tuning, scoring on a holdout, new market-data requests, or strategy tests.

## Source snapshot and known facts
- Offline CSV: `nifty_repaired_composite_2021-10_to_2026-10.csv.gz`
- SHA-256: `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5`
- 8,999,865 rows; 47 columns; options 8,490,723; spot 509,142.
- 8,471,702 option rows have exact spot timestamp matches; 19,021 rows across 421 timestamps remain unmatched.
- 24,847 rows carry weekend-session review flags.
- Invalid OHLC/volume values were masked, not fabricated. No approximate timestamp joins were used.
- Export verification is not modelling-readiness approval. CSV is local to the conversation workspace; it must not be committed or uploaded as plaintext.

## Research questions
1. Which of the paper-specified methods adds out-of-sample predictive value over naive and simple time-series baselines for NIFTY direction?
2. Are gains stable across walk-forward origins, volatility/regime slices, and forecast horizons?
3. Do results survive multiple-testing correction and comparison against a null that respects serial dependence?
4. Which feature families are estimable from the verified dataset without leakage or unsupported historical inputs?

## Aims and objectives
- Audit schema, timestamp ordering, duplicate keys, row types, missingness, target construction and leakage risks.
- Freeze an explicit decision-origin and label-horizon contract before any fit.
- Test methods described in the repository's paper crosswalk one-by-one, only where input and target requirements are met.
- Report discrimination and calibration metrics, confidence intervals, familywise inference, and baseline-relative effects.
- Keep prediction claims separate from economic profitability claims.

## Phase A — immutable local data preflight (proposed next)
1. Require the user-workspace CSV/GZ path; verify gzip integrity, SHA-256, 47-column schema, and expected record count.
2. Stream the file in bounded chunks; report dtypes, null counts, key uniqueness, timestamp/session coverage, class balance and row-type coverage.
3. Independently recompute exact spot joins and quality flags without editing source rows.
4. Verify that no future-derived or post-decision fields enter the predictor set.
5. Emit sanitized JSON/CSV summaries only; no market prices or plaintext dataset in GitHub.
6. Tester gate: exact commit + report hashes, test fixtures for malformed schema, duplicates, timezone/session boundaries, missing labels, and leak sentinels.

## Phase B — target and split contract
- Define targets as future spot return/sign at explicitly stated horizons, computed only from decision-origin spot values.
- Separate feature time from label time; no feature may be timestamped after the decision origin.
- Use chronological walk-forward validation, with purging/embargo at least as long as the maximum target horizon.
- Development period only for method selection. Reserve the repository's prospective untouched 252-session holdout plus 10-session label-maturity tail for one final evaluation after configuration freeze. Do not retroactively call historical data an untouched holdout.
- Freeze class order, tie/flat rules, missing-label policy, baselines, metrics, random seeds, and global fit budget before fitting.

## Phase C — bounded prediction experiments
- Baselines: no-change/majority class, historical class rate, logistic regression, regularized linear model, and simple autoregressive/technical benchmark.
- Paper replications: only methods explicitly described in the crosswalk and supported by available features; report deviations from the paper.
- Models: linear/tabular classifiers, tree ensembles, and sequence models only when their method-specific input data and computational budget are available.
- No blind hyperparameter search. Fixed search budget, nested chronological validation where tuning is required, deterministic seeds, and cached derived features.
- Feature families such as news sentiment, FII/DII, FX/VIX, global indices, option Greeks/PCR and corporate actions are marked NOT_ESTIMABLE unless point-in-time histories and lineage are available. Do not proxy unavailable variables silently.

## Phase D — statistical analysis
- Primary: balanced accuracy and macro-F1 for directional classes; log loss/Brier score and calibration for probabilistic outputs.
- Secondary: ROC-AUC only for binary tasks with a declared positive class; confusion matrix, per-class precision/recall, calibration curve, and horizon-specific results.
- Compare each method with the strongest eligible baseline using paired walk-forward-origin differences.
- Use a predeclared moving-block bootstrap / dependence-aware null and familywise correction (e.g., Holm) across all tested method × horizon × target comparisons.
- Publish effect sizes and confidence intervals, not p-values alone. Report all attempted configurations, including failures and negative outcomes.
- No winner is declared on in-sample performance or uncorrected comparisons.

## Phase E — robustness and reproducibility
- Evaluate regimes using only contemporaneously available regime labels; show sample sizes and uncertainty.
- Sensitivity checks: masked-data exclusion, exact-match-only subset, session/calendar handling, horizon embargo, class thresholds, and baseline definition.
- Persist source hashes, configuration, environment lock, seeds, fold boundaries, per-origin predictions, metrics and sanitized logs as immutable artifacts.
- Regression and tester gates run before each empirical submission. Tester must issue an explicit exact-snapshot decision before the next phase.

## Phase F — conclusion and manuscript
- Classify each method: supported, not supported, inconclusive, or not estimable.
- A predictive result is not a profitable option strategy. Any later economic evaluation is a separate gate and must model Paytm Money brokerage, statutory/exchange charges, bid-ask spread, slippage, latency, lot-size changes, premium decay, liquidity and realistic execution.
- Produce a manuscript with abstract, questions, literature synthesis, data/methods, results, statistical inference, discussion, limitations, conclusion, future work, tables, plots, appendices and artifact links.

## Stop rule
This is a finite plan, not indefinite parameter mining. Stop after the pre-registered methods, horizons, robustness checks and final holdout are complete, or report that evidence is insufficient. Do not fabricate a positive conclusion. Missing one feature family does not stop unrelated estimable experiments.

## Current permissions
- Export/integrity: PASS with scoped restrictions.
- Dataset modelling-readiness: NOT YET APPROVED.
- Fitting/scoring: CLOSED pending tester gate and preflight.
- Untouched holdout: CLOSED.
- Option strategy/P&L: CLOSED.
- New source requests: CLOSED unless separately authorized by exact-snapshot gate.

## Tester checklist
1. Verify the CSV digest and counts are treated as claimed metadata, not as a substitute for local file availability.
2. Check leakage controls, target timing, split chronology, embargo and holdout separation.
3. Check statistical family definition, multiplicity correction, baseline fairness, metrics and missing-data policies.
4. Check every proposed method is tied to source evidence in the paper crosswalk.
5. Return PASS / PASS_WITH_SCOPED_RESTRICTIONS / REQUEST_CHANGES with exact scope; do not authorize fitting or holdout access implicitly.
