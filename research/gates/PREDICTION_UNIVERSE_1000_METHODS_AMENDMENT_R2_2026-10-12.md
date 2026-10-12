# Prediction Universe Expansion — R2 Protocol Amendment
Date: 2026-10-12
Status: **RESUBMITTED — independent tester review required; empirical execution blocked**
Supersedes R1 for review purposes; no empirical results or definitions have been inspected to choose this protocol.
Developer branch: `phase-08-prediction-developer`
Tester branch: `phase-08-prediction-tester`

## 1. Scope and count requirements

The target is at least **1,000 distinct prediction-method definitions**. Count method definitions, parameter configurations, horizon/label evaluations, folds, and cost scenarios in separate columns. None can be substituted for another.

Current `research/METHOD_REGISTRY.md` has 112 named entries. Phase 8's 4,800 forecast-to-option configurations are downstream execution configurations and do not count toward the target.

The method registry must be frozen and hash-pinned before new comparative empirical results are examined. No strategy can be selected from Phase 8 outcomes while prediction coverage is incomplete.

## 2. Canonical method identity and duplicate rule (T1)

Each method record must contain:
- stable `method_id`;
- algorithm/rule family and full mathematical decision function, pseudocode, or model architecture;
- learning objective/loss and target transformation;
- input representation/feature-construction graph, with source timestamps and causal lags;
- inference rule, calibration rule, uncertainty/abstention operator;
- training/refit/update policy;
- target definition and evaluation stratum (intraday or positional);
- source-code path, unit-test path, and synthetic invariant tests.

Canonicalize the identity fields as UTF-8 JSON using sorted keys, normalized numeric literals, normalized whitespace for embedded formulas, and no run-specific fields (seed, fold, date range, batch, data file, or parameter value that is merely a scalar setting). Compute SHA-256 over the canonical identity JSON. Two records with the same fingerprint are one method. A seed, fold, ticker, time window, horizon-only change, scalar hyperparameter change, renaming, or train/test split change creates a configuration/evaluation variant, not a new method.

A new method requires a substantive change in at least one of: algorithmic decision function, architecture, learning objective, input representation/feature construction, information-combination mechanism, or inference/uncertainty operator. Every proposed new method must have a short contrast statement against its nearest registry neighbor. The tester must inspect exact-fingerprint duplicates and a documented near-duplicate sample; unresolved near-duplicates do not count toward the 1,000 minimum. Publish fingerprint collisions/duplicates and the resulting accepted unique count.

## 3. Configuration manifest and completeness contract (T2)

Every method links to an explicit finite list of configurations. Each configuration includes stable `config_id`, parent `method_id`, canonical config JSON, config SHA-256, label/horizon, feature-set version, lookback, refit cadence, allowed model parameters, missing-data policy, and declared data dependencies.

The top-level frozen manifest includes:
- unique method count and method-fingerprint list;
- unique configuration count and config-hash list;
- expected deterministic batch IDs and configuration membership per batch;
- exact code commit and dependency lock hash;
- immutable data snapshot IDs/hashes and PIT schema version;
- expected output schema and validator version;
- predeclared metrics, folds, sample minima and multiple-testing family.

Manifest validation must fail on duplicate IDs/hashes, missing parent methods, a configuration assigned to multiple batches, missing expected results, duplicate result rows, unrecognized statuses, or a final count mismatch. Every configuration must have one terminal status: `EXECUTED_AUDITED`, `BLOCKED_DATA`, `BLOCKED_GATE`, `FAILED_TECHNICAL`, or `REJECTED_EMPIRICAL`. A failed job is not silently retried under a new identity; retry lineage references the same config ID. Poor metrics never remove a record.

## 4. Statistical plan frozen before execution (T3)

Evaluate intraday and positional strata separately. Freeze a single primary probability metric per stratum before the registry run:
- Primary: out-of-sample log loss, with lower values better, evaluated against a frozen no-skill/class-prior baseline fitted only on the training window.
- Co-primary descriptive diagnostics: Brier score and calibration intercept/slope.
- Secondary discrimination: ROC AUC, PR AUC and balanced accuracy when defined by class balance; these are descriptive and do not override a failed primary test.
- Report class prevalence, sample count, missingness, effect size versus baseline, block-level uncertainty intervals and all fold-level metrics.

For each method and stratum, compare the out-of-sample log-loss difference to the frozen baseline using paired chronological block bootstrap on the untouched out-of-sample prediction sequence, with block length chosen from training-only autocorrelation diagnostics and frozen before scoring the evaluation segment. Use 10,000 bootstrap replicates with deterministic, recorded seeds; if sample length makes this invalid, record a predeclared BLOCKED/NOT_ESTIMABLE reason rather than changing the test after seeing results.

Multiplicity family: all method hypotheses within each separately declared target/horizon stratum. Apply Benjamini–Yekutieli FDR control at q=0.05 to the one-sided baseline-improvement hypotheses, because method outcomes are dependent. Publish raw p-values and adjusted q-values for every estimable method. No post-hoc choice of a different correction based on the leaderboard. A method is only a statistical candidate if its out-of-sample log loss improves on baseline and BY-adjusted q≤0.05; this is not sufficient for promotion and does not authorize trading. Include confidence intervals and the full distribution, not only significant methods.

No untouched forward holdout is opened for method screening. Use chronological training/validation/out-of-sample development blocks with purge/embargo when labels overlap. Phase 10 forward testing remains a later locked gate.

## 5. Data leakage, provenance and failure rules

- All transforms, imputation, scaling, feature selection, calibration and model selection are fitted on training data only.
- Features are joined by availability/publication timestamp, not merely event date. Future corrections/revisions cannot be used if not available at the decision time.
- Intraday and positional labels/metrics never mix.
- Minimum sample, maximum missingness, class support and valid-fold rules must be declared per target before running.
- Every result includes method/config hashes, code/data hashes, per-fold predictions or a protected reproducible reference, metrics, logs, status and tester disposition.
- Null results, failed tests, data blockers and non-significant methods remain in the manifest.
- Phase 8 proxy outcomes can be audited for accounting integrity but must not inform prediction method construction, ranking, tuning or selection.

## 6. Resource, batching and restart contract (T4)

Before scheduling, publish a dry-run resource report from synthetic or training-only pilot data. Use deterministic shards sorted by `config_id`; each batch has a declared maximum of 4 hours wall time and a memory budget set by the hosted runner. A batch exceeding its budget is checkpointed only at completed configuration boundaries. Restart resumes unfinished config IDs with the same hashes; completed outputs are immutable and are not recomputed unless a reproducible validator failure is logged.

Cache only immutable, hash-verified source snapshots and training-fold feature matrices. Do not cache outputs across data/code hashes. Batch completion is accepted only after reconciliation of expected/observed IDs and terminal statuses. Resource-limited methods receive `BLOCKED_GATE` or `FAILED_TECHNICAL` with logs; they are not silently omitted. Publish expected configuration count and estimated number of batches before execution. If the finite universe cannot fit the declared budget, reduce it only by a protocol amendment approved before empirical comparison, not by dropping slow/poor methods.

## 7. Historical result reconciliation (T5)

Historical Phases 3–7 count toward the 1,000 only if an independent tester can map an immutable pre-existing method specification, exact code/input hashes, explicit configuration coverage, fold-level results and result artifact to one canonical V2 method fingerprint without changing its identity after seeing performance. Otherwise mark `HISTORICAL_NOT_COUNTED`. Narrative claims, names, parameter variants and missing hashes earn no count credit. The tester must publish a reconciliation table with counted/not-counted reason for every proposed historical item.

## 8. Independent gates and stopping rule

1. Tester passes this R2 protocol, hash-pinned.
2. Developer creates registry V2 and full finite configuration manifest without empirical comparison.
3. Tester audits unique fingerprints, near-duplicates, counts, schema, config coverage, hashes, resource estimate and statistical plan.
4. Developer runs deterministic batches only after gate 2 passes; tester independently audits each immutable batch artifact before the next batch is authorized.
5. After all methods/configurations reach terminal statuses, perform the preregistered multiplicity analysis and independent result reconciliation.
6. Only survivors proceed to the separately gated robustness/fresh-forward work. Prediction accuracy is not itself a profitable-trading claim.
7. Stop after every manifest entry is audited and all downstream pre-registered gates are complete. Do not endlessly expand the registry after seeing results.

No new empirical prediction runs, data download/decryption for fitting, or holdout access is authorized by this amendment alone.

**Developer → Tester:** review R2 exactly as committed; verify T1–T5 are concretely addressed and identify any remaining blocking issue. Do not fit models or access the holdout.

**Tester → Developer:** issue a hash-pinned PASS or REQUEST CHANGES. Registry V2 and empirical prediction batches remain blocked until the protocol passes.
