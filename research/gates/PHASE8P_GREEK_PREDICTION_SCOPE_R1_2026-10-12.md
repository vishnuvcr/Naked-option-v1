# Phase 8P — Greek Feature Incremental Prediction Study, Scope R1
Date: 2026-10-12
Role branch: phase-08-developer
Status: **SCOPE SUBMITTED FOR INDEPENDENT TESTER REVIEW — NO EMPIRICAL RUN AUTHORIZED**

## 1. Purpose and boundary
This is a prediction-only sub-study. It tests whether option-derived features from the independently accepted R3 Greek-enriched research artifact add out-of-sample information for future NIFTY spot direction on identical timestamps, labels and chronological test rows. It does not convert forecasts into options, evaluate P&L, tune entries/exits, open the final holdout, promote a method, or authorize source/API requests.

This scope refines the existing plan's questions about incremental derivatives/options information; it does not replace the existing finite Phase 0–11 plan. The current R3 artifact is reused immutably. It remains a PARTIAL_GRID and has a CC-BY-NC-4.0 non-commercial research restriction.

## 2. Research questions
- RQ8P.1: On matched and point-in-time-aligned decision rows, do a fixed Greek/IV feature block and a fixed spot-only feature block yield different future-direction probabilities out of sample?
- RQ8P.2: Does any observed gain persist across the registered daily horizons (1, 2, 3, 5, 10 sessions) and intraday horizons (5, 15, 30, 60, 120 minutes), rather than appearing only in one horizon?
- RQ8P.3: How sensitive are conclusions to missing Greeks, inversion-vs-fallback IV provenance, and expiry-file-list-vs-Tuesday-rule proxy provenance?
- RQ8P.4: Is the feature panel's timestamp coverage sufficient to support a fair paired comparison with the frozen Phase 7 forecast panels?

## 3. Aim and objectives
Aim: measure incremental predictive value of the available Greek-enriched option panel without leakage or holdout contamination.

Objectives:
1. Verify immutable identities and hashes of the accepted R3 Greek artifact and saved Run #994 forecast-panel artifact.
2. Prove timestamp semantics from the manifests and column schemas before joining; reject ambiguous timestamp conventions instead of guessing.
3. Use only features observable by the forecast decision timestamp. Greek values generated from source minute candles are valued at source timestamp +60 seconds; therefore feature keys must reflect that bar-end time.
4. Construct a visible-panel feature table with explicit option-row coverage and provenance, never claim a complete-market Greek surface.
5. Compare matched spot-only and spot-plus-Greek variants with identical labels, decision rows, chronological splits and fixed model settings.
6. Retain BLOCKED_DATA or INSUFFICIENT_OVERLAP outcomes; never lower thresholds after seeing model performance.
7. Produce reproducible aggregate metrics, paired uncertainty/inference, data-coverage tables and a decision manifest without emitting plaintext market data.

## 4. Frozen inputs
### Greek feature source
- Developer run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38195812828
- Artifact ID: 11723198817; name nifty-1m-greeks-enriched-r3
- ZIP SHA-256: e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736
- Source HF revision: 0f4800e43e6f96cec0794369d78eb4d3c4211ef5
- License: CC-BY-NC-4.0; non-commercial research only.
- Coverage: 8,999,865 rows (8,490,723 option + 509,142 spot), 61 encrypted partitions; 8,418,616 option rows with Delta.
- Limitations: PARTIAL_GRID; estimated European Black–Scholes Greeks; r=0/q=0 proxies; expiry derived from a historical file-list proxy or Tuesday rule, not an official point-in-time contract master; no observed historical bid/ask evidence is established.

### Frozen prediction comparison source
- Run #994: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656
- Artifact ID 11638738288; ZIP SHA-256 3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9
- Embedded manifest SHA-256 f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091
- Aggregate SHA-256 96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39
- Ten frozen prediction panels / 50,555 rows, already independently validated. P01–P10 remain fixed references; this sub-study may not edit or reinterpret their outputs or the protected holdout.
- Baseline status to be rechecked from the accepted Phase 7 tester report: daily best AUC was approximately 0.579, balanced accuracy approximately 0.496, and all ten family-level moving-block bootstrap results were non-significant. These are context only, not a hypothesis outcome for this sub-study.

## 5. Dataset and timestamp gates (run before fitting)
- Download only the two pinned GitHub Actions artifacts; verify whole ZIP hashes before extraction.
- Greek artifact is encrypted using AES-256-GCM; its key is derived from the repository HF_TOKEN secret with the existing documented scrypt derivation. Use the secret only inside the hosted job; never print it or pass it on a command line.
- No new Hugging Face, Dhan, NSE, BSE or other data-source request is part of this scope.
- Decrypt/read only in runner temporary storage; remove temporary plaintext and do not upload raw rows, decrypted CSV/Parquet, token-derived key or sensitive intermediate datasets. Only manifests, aggregate counts, metrics and hashes may be artifacts.
- Parse saved forecast panel schema and target timestamp fields before join. If panel timestamps cannot be unambiguously aligned to the Greek feature's bar-end valuation timestamp, fail closed; do not add or subtract a minute by intuition.
- Join on exact UTC epoch/instant and the panel's layer+horizon; no nearest merge, forward fill, interpolation, or cross-session carry.
- The future label must end strictly after decision time. If the provided saved panel does not contain a usable, unambiguous target/decision contract, stop and submit a separate schema amendment; do not rebuild/change the Phase 3 labels silently.
- Report raw panel rows, exact matched rows, match rate, unmatched reasons, feature-valid rows, days/sessions and coverage by horizon before the model stage.

## 6. Frozen features
### A. Spot-only comparator
Use only the same artifact's point-in-time spot history through the decision instant: fixed prior returns (1, 5, 15, 30, 60 minutes), 20- and 60-observation realized volatility, and prior-session return where defined. Feature engineering must be strictly backward-looking. This is an internal comparator, not asserted to reproduce the earlier Phase 7 baseline models.

### B. Spot + observed-panel option/Greek block
Pre-register a compact set of per-timestamp cross-sectional aggregates from rows whose Greek valuation time is no later than the decision time:
- counts of valid CE/PE option rows and Delta-valid rows;
- median CE Delta and absolute median PE Delta;
- CE-vs-PE Delta imbalance using signed Delta;
- median Gamma, Theta/day, Vega per 1% IV, and IV among eligible CE and PE rows;
- put-minus-call IV difference;
- prior-observed-panel put/call open-interest and volume ratios, only if fields are present and nonnegative;
- count/coverage and data-quality indicators, including the IV source and expiry-mapping source coverage proportions.

Aggregates are of the observed partial panel, not the full exchange option chain. Exclude invalid-IV and source-flagged non-trading-session rows in the primary Greek block. Do not use option-close, OI or volume observations whose bar-end is after the decision timestamp. Missing-feature imputation/scaling is fit on training rows only. No label or future-return statistics may enter the feature block.

## 7. Fixed model arms and chronology
- Models: L2 logistic regression (C=1.0; deterministic solver; class weighting disabled) and HistGradientBoostingClassifier (max_iter=200, learning_rate=0.03, max_leaf_nodes=15, min_samples_leaf=30, deterministic seed where supported). No hyperparameter search.
- For each model/horizon, compare spot-only vs spot-plus-Greek on identical eligible timestamps and the same label.
- Expanding walk-forward; refit every 20 completed trading sessions; train only on labels whose outcome window has fully matured before the next test decision. Purge labels that overlap the test block. Minimum training size and session grouping must reuse validated Phase 3/7 conventions; fail closed if a required split rule cannot be recovered byte-for-byte from the approved protocol.
- Never use the final untouched holdout. If panel metadata does not distinguish the protected segment, do not fit on any candidate rows until the exact development-only boundary is located and tester-approved.
- All model preprocessing, missing-data treatment, and any probability calibration are training-only. The primary comparison cannot use a post-hoc selected feature subset.

## 8. Outcomes and inference
Primary metric: paired change in Brier score (spot-only minus spot-plus-Greek; positive means the augmented variant is better). Report paired ROC-AUC, PR-AUC, balanced accuracy, log loss, calibration slope/intercept and class rates as secondary diagnostics. Report the full panel-match/coverage table beside metrics.

Use same-row paired comparisons. Use a deterministic moving-block bootstrap (seed 42, 500 resamples) with horizon-appropriate registered block lengths (daily 20 sessions; intraday 60 decision observations, following Phase 7 settings) and the same bootstrap indices for both arms. Correct the family of 20 primary comparisons (2 model types × 10 horizons) with Holm's step-down procedure. No candidate is promoted merely because an unadjusted metric is highest. If exact Phase 7 bootstrap semantics cannot be reused for the panel structure, the inference job must be blocked pending a tester-reviewed amendment.

## 9. Coverage and stop rules
- Pre-flight minimum for a model cell: at least 60% exact feature join among eligible development panel rows, at least 1,000 eligible train rows at the first fit, at least 500 out-of-sample rows and at least 20 chronological test blocks. These are feasibility gates, not performance criteria.
- If the thresholds fail, emit INSUFFICIENT_OVERLAP/BLOCKED_DATA with counts and do not tune the threshold or switch datasets based on results.
- No final holdout, option P&L, execution simulation, brokerage/slippage modeling, trading strategy, or strategy promotion in this sub-study.
- No new external source calls or data refresh. Encrypted artifacts remain immutable.
- If the augmented models fail to improve on registered paired metrics, record that outcome. It is not permission to expand indefinitely or search the holdout.

## 10. Required deliverables and gates
1. Scope approval by tester.
2. Developer implementation + synthetic-only tests, which must pass an independent code gate before any data artifact is opened by the new runner.
3. Hosted preflight gate: exact artifact identity/hash, schema, timestamp alignment, coverage/holdout boundary and encryption cleanup; no model fit unless tester-approved preflight passes.
4. Hosted prediction run with immutable aggregate-only artifact.
5. Independent tester recalculates metrics/inference and checks split/purge logic, mathematics, signs, joins, leakage, Holm correction and hashes.
6. Update README, research status, error log, chat/research log and a reproducible decision packet; no downstream phase advancement without tester report.

## Status
Current step: **scope submitted; tester review required**. No new prediction run or results have been generated by this scope request.

**Developer → Tester:** independently inspect the target/time alignment, holdout exclusion, fixed model family, coverage thresholds, paired Brier primary metric, Holm correction, and encrypted-only data handling. Return PASS for scope only or REQUEST CHANGES with concrete reasons; this is not empirical authorization.

**Tester → Developer:** do not implement/launch the model job until the scope gate is recorded. Even after scope approval, require a separate exact-code gate and a separate pre-flight decision before model fitting.
