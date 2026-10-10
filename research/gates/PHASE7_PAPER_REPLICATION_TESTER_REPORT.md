# Independent Tester Report — PPR-1 Paper Replication Crosswalk

**Review date:** 2026-10-10  
**Reviewer role:** Phase 7 independent tester  
**Branch:** phase-07-tester  
**Decision:** **REQUEST CHANGES — DO NOT AUTHORIZE PPR-2 OR EMPIRICAL EXECUTION YET**

## Exact snapshots reviewed

- Crosswalk research/literature/PAPER_PREDICTION_METHOD_CROSSWALK.md, blob 68839b2e427b7d5883cb5a65061a2899381f8a26.
- Protocol research/phase7/PAPER_REPLICATION_EXTENSION_SPEC.md, blob c630ef1cb41142367bd7253b1154081114075d8a.
- Developer submission research/gates/PHASE7_PAPER_REPLICATION_DEVELOPER_SUBMISSION.md, blob d435003d0ebfa09fd4ee246d86c9c0cbecdada75.

This is an independent review of the submitted crosswalk/protocol text and its statistical/data-governance logic. It is **not** a claim that all 15 source PDFs have been re-audited line-by-line in this pass. Source-text verification remains unresolved and is itself a reason not to pass this gate.

## Findings

### P1 — Familywise inference is not operationally defined

The proposal specifies one familywise maximum-statistic test over paper-method × feature pipeline × horizon, but the grid mixes non-comparable statistics and target types: AUC, Brier/log loss, balanced accuracy, regression MAE/RMSE/R², price targets, and direction targets. The exact null statistic, direction of improvement, standardization/ranking, resampling unit, dependence block length, missing-cell handling, and multiplicity-adjusted confidence interval procedure are not frozen.

**Required correction:** predefine separate inferential families for (a) directional probabilistic scores and (b) price regression, or define a defensible common standardized statistic. Specify one-sided/two-sided hypotheses, block construction/selection, maximum-statistic algorithm, missing-cell policy, and the exact adjusted p-value calculation before any fitting. Do not select the best model from mixed raw metrics.

### P1 — Common target and paper-native target can disagree

The crosswalk says the common directional label is future close-to-close return sign; the protocol says sign of return from decision-time close to future close, which is coherent, but it also says derive direction from forecast-close versus current close for papers predicting price. That mapping is only equivalent when the forecasted close and target endpoint are aligned exactly. Next-day open/close papers, one-week tasks, and 30-session forecasts need explicit endpoint alignment and no ambiguous calendar-day/session mapping.

**Required correction:** add a target table per paper/config with decision timestamp, forecast endpoint, target formula, label threshold/flat tolerance, forecast output conversion, and valid rows. Assert in code that each forecast endpoint matches the scored label endpoint. Treat paper-native targets as distinct tasks when endpoints differ.

### P1 — Feature availability and label-endpoint leakage need machine-checkable rules

The protocol states PIT principles, but does not fully define data availability timestamps for daily OHLCV, close-derived indicators, FII/DII publications, VIX, option-chain fields, news/tweets, and revised/corrected vendor records. For a close-time forecast, same-day close or an indicator calculated from it is unavailable unless the decision is explicitly after that close. The generic rule “available by cutoff” is not enough to settle this.

**Required correction:** freeze a per-source availability-time convention, decision timestamp/time zone, exchange calendar, publication timestamp versus event date, revision policy, and strict label-end < decision-time checks for training rows. Add regression tests for close-time boundaries, same-day FII publication timing, news timestamps, and horizon endpoints.

### P1 — Paper-fidelity versus common adaptation is not tracked at row level

The crosswalk correctly warns against reproducing leakage-prone random splits as the primary result, but the proposed causal walk-forward evaluation changes several papers' published protocol. Some papers also have conflicting dates, underdefined “accuracy,” ambiguous train/test ordering, or incomplete architecture details. The present status is at paper level, not a complete configuration ledger, so exact replication and safe adaptation can be conflated.

**Required correction:** in PPR-2/PPR-3, create separate rows for (1) exact paper configuration and reported split/metric, (2) leakage-safe adaptation, and (3) common-comparison task. Record each deviation and whether exact replication is impossible. Never call an adapted run an exact replication.

### P1 — Source-paper verification and citation traceability are incomplete

The crosswalk has 15 paper rows but no page/section/table references or short traceable source locators for each asserted model, date range, split, metric and horizon. The developer submission requests full-text confirmation, but the current snapshot alone does not demonstrate that every model was actually implemented rather than only discussed in a literature review. This is particularly material for background models, undefined accuracy claims, ANN optimizer variants, sentiment/SOFNN and hybrid architectures.

**Required correction:** add PDF page and section references (or a separate source evidence table) for every paper-method claim, distinguish “implemented by authors” from “mentioned/background,” and list ambiguous or unverified claims. The full-text audit must be recorded before PPR-1 can pass.

### P2 — Multiplicity grid can expand after inspecting data

The candidate list includes optional architectures, feature ablations, horizons and adaptations, but there is no numeric upper bound on configurations/training budgets or a rule preventing post hoc additions after source coverage is known.

**Required correction:** at PPR-3 freeze a complete enumerated configuration manifest, maximum number of configurations, seeds, tuning budget, feature pipelines, and amendment policy. New candidates after seeing outcomes must be exploratory and cannot enter the confirmatory family.

### P2 — Baseline and score interpretation require stronger controls

The 50/50 random reference is not a sufficient baseline for imbalanced labels; ROC AUC is undefined for single-class cells; PR AUC depends on prevalence; MAPE/SMAPE need explicit zero/near-zero rules. “Persistence/previous-direction” is ambiguous for return-sign prediction.

**Required correction:** define exact causal baselines mathematically, report prevalence and valid n, set explicit NOT_ESTIMABLE conditions for AUC/PR AUC, and predefine denominator/epsilon rules for percentage errors. A failed or undefined metric must not be silently coerced to zero.

### P2 — Data-window availability is not reconciled with the required paper tasks

The stated 2020–2026 cache cannot reproduce the 2005–2021, 2006–2016, 2011–2021, or 5/10/20-year windows. The proposal correctly recognizes this but must preserve per-paper native-window and common-window results as distinct statuses.

**Required correction:** report exact eligible dates/rows per paper × feature pipeline before fitting; use BLOCKED_DATA only after the free-source gate; label shortened-sample runs as adaptations and never as paper-native replications.

## Checks passed at proposal level

- Prediction tasks are separated from strategy-only/option-signal papers; no option P&L is authorized.
- Existing Run #44 is explicitly not treated as proof of paper-specific replication.
- Final holdout access and new full-history acquisition are prohibited before the corresponding gates.
- The finite PPR-0–PPR-10 sequence and failure statuses prevent a requirement to find a profitable model at any cost.
- The crosswalk says model-family overlap alone is not evidence of exact replication.

These positives do not offset the P1 defects above.

## Gate decision and allowed next step

**REQUEST CHANGES.** PPR-1 is not passed. No PPR-2 registry reconciliation, new source pull, model fitting/tuning/scoring, holdout access, or option P&L is authorized by this report.

The developer may correct the crosswalk/protocol on phase-07-developer and submit a new exact-snapshot review. The next submission must include:
1. source page/section traceability for all 15 PDFs and implementation-vs-background distinctions;
2. explicit target/endpoint/decision-time table;
3. executable multiplicity/inference specification;
4. per-source PIT availability conventions and leakage regression tests;
5. separate exact-replication versus safe-adaptation rows;
6. frozen configuration-count and tuning-budget bounds.

After corrections, the tester must review the new blob hashes. Do not alter the tester branch's protected developer files.

**Developer → Tester:** Resubmit a corrected exact snapshot and identify every changed blob.  
**Tester → Developer:** Keep the gate fail-closed; re-review the corrected snapshot and approve only the explicitly permitted next phase.
