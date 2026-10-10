# PPR-3 — Configuration Matrix and Protocol Freeze Proposal

**Date:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Status:** **PROPOSED — TESTER REVIEW REQUIRED**  
**Allowed current work:** documentation and offline validation only. **No data requests, data downloads, model fit/tuning/scoring, final-holdout access or option P&L are authorized.**

## 1. Gate lineage and purpose

PPR-1 received **PASS WITH SCOPED RESTRICTIONS** for the 15 uploaded-PDF source inventory. PPR-2 received **PASS WITH SCOPED RESTRICTIONS** for the row-wise mapping of all 36 literature-registry sources. Those decisions authorize only the next documentation phase. They do not authorize empirical runs.

PPR-3 turns the source inventory into a finite, row-level estimator/target/feature/horizon matrix, records settings and ambiguities, defines compatible inferential families, freezes a bounded tuning subset, and specifies how the sealed final holdout is protected. The candidate inventory is a proposal until the tester signs off on the exact current blobs.

Authoritative companions:
- [Configuration matrix](PPR3_CONFIGURATION_MATRIX.csv) — common-task adaptation configs and explicit blocked entries.
- [Paper-native task ledger](PPR3_PAPER_NATIVE_TASK_LEDGER.csv) — 81 separate source-method records with native task details, source locators, fidelity/disposition and adaptation links; documentation only, not active fit cells.
- [Expanded candidate-cell ledger](PPR3_CANDIDATE_CELLS.csv) — one row per common-task model/configuration × feature pipeline × horizon.
- [Model settings](PPR3_MODEL_SETTINGS.json) — default estimator/architecture settings, feature pipeline definitions, seed policy and the exact tuning grids.
- [Machine-readable manifest](PPR3_CONFIGURATION_MANIFEST.json) — row counts, target families, fit-budget arithmetic, exact artifact hashes and fail-closed rules.
- [Target/inference contract](PPR_TARGET_INFERENCE_CONTRACT.json) — label equations, baseline formulae, point-in-time constraints and multiplicity procedure.
- [PPR-1 tester report](../gates/PHASE7_PPR1_REVIEW3_TESTER_REPORT.md) and [PPR-2 tester report](../gates/PHASE7_PPR2_TESTER_REPORT.md).

## 2. Research question, aim and objectives

**Research question:** Under a fixed, point-in-time-safe, chronological hold-forward comparison, do the paper-derived forecasting methods provide out-of-sample NIFTY 50 directional probability improvement over a causal class-frequency baseline, and do price-forecast models improve absolute price error over simple persistence?

**Aim:** freeze a comprehensive but finite candidate universe grounded in the uploaded papers while maintaining an explicit distinction between an author-implemented paper method, a paper-native task that is currently blocked, and a leakage-safe project adaptation.

**Objectives:**
1. Preserve a row-level link from every active model config to its source method and evidence locator.
2. Compare only compatible target schemas and primary losses within a family.
3. Predefine source/feature/horizon combinations before any fitting.
4. Put ambiguous source settings and source-ineligible methods into explicit blocked records instead of silently dropping or substituting them.
5. Keep familywise inference, fit-call budget, candidate coverage and the final-holdout boundary machine-checkable.
6. Use PPR-4 to establish source feasibility and the exact data-eligible set before any model training; require another exact-snapshot gate before implementation or fitting.

## 3. Configuration inventory and caps

Current developer draft (not yet independently approved):

| Item | Count | Meaning |
|---|---:|---|
| Configuration-ledger rows | 81 | Includes active common-task adaptations and blocked/source-task records |
| Rows counted against the maximum base-configuration cap | 73 | Unique model/target/settings rows; duplicate source references are merged only for identical common-task adaptation fits |
| Active candidate configuration rows | 72 | Candidate only; still needs PPR-4 data eligibility and later code/tester approval |
| Blocked model configuration | 1 | SOFNN native method; source implementation settings are not sufficiently reproducible in the current source audit |
| Other blocked/out-of-scope source backlog rows | 8 | Unclear native LSTM task, option-return/option-price targets, abstract/metadata-only targets and unreviewed public code |
| Expanded model × pipeline × horizon cells | 1,188 | Cell ledger defines the proposed common-task multiplicity universe |
| Core directional cells | 380 | 22 active directional configurations, including the explicit CCI(20) spot-direction adaptation |
| Close-price regression cells | 760 | 38 close-regression configurations × four eligible feature-pipeline classes × five horizons |
| Next-open regression cells | 48 | 12 regressors × four feature-pipeline classes × one-session horizon |

The configured maximum remains 93 base configuration rows, four pipeline classes and five common horizons. The 20 unused rows of theoretical headroom are **not permission to add models** after this proposal is reviewed. Any addition requires a reviewed amendment before results are inspected. The matrix's explicit rows—not the numeric cap—define the candidate universe.

### Configuration consolidation

Where the same estimator/settings/target/pipeline/horizon were intended under multiple source references, the matrix merges source provenance into one common project candidate and preserves old IDs as aliases. It does not count identical common model fits multiple times merely to inflate paper coverage. This consolidation is valid only for the *common adaptation*. The separate [paper-native task ledger](PPR3_PAPER_NATIVE_TASK_LEDGER.csv) retains all 81 individually named uploaded-PDF method/component records with source-native task details, source locator, fidelity/disposition and an adaptation link. These native-task records are not common inference cells and cannot be counted as exact replications unless separately frozen and gated.

## 4. Target families and compatible primary metrics

### 4.1 Direction — `COMMON_DIRECTION_3CLASS`

At decision session (t), after the official close is published, define (r_{t,h}=C_{t+h}/C_t-1) for (h in {1,2,3,5,10}) NSE sessions. Label UP if (r>10^{-8}), DOWN if (r<-10^{-8}), and FLAT otherwise. **FLAT means only a numerical zero-return tie under the frozen 10^{-8} tolerance; it is not an economically neutral move, cost-aware no-trade state, or claim that an option has no edge.** This tolerance cannot be tuned after results are inspected. Every candidate emits probabilities in the fixed order `DOWN, FLAT, UP`, summing to 1 within the registered numerical tolerance.

Primary loss is three-class Brier score:
[
\mathrm{BS}_t=\sum_{k\in\{DOWN,FLAT,UP\}}(p_{t,k}-\mathbb{1}[y_t=k])^2.
]
Improvement is baseline loss minus candidate loss, so positive values favor the candidate. The causal baseline is the expanding historical class frequency with Laplace (alpha=1), using only labels whose endpoints have matured before the decision. Simple crossover rules get probabilities from past-only class frequencies conditional on the signal state; they do not submit a hard label as if it were a calibrated probability.

### 4.2 Close-price regression — `COMMON_CLOSE_REGRESSION`

Target is (C_{t+h}) for (hin{1,2,3,5,10}). Score absolute error in NIFTY index points; the persistence baseline predicts (widehat C_{t+h}=C_t). Each price model is evaluated in this regression family. Converting its predicted close into a hard UP/DOWN/FLAT direction is descriptive only and does **not** enter the primary Brier family, because a point forecast is not a three-class probability vector.

### 4.3 Next-open regression — `NEXT_OPEN_REGRESSION`

Target is the next session's (O_{t+1}), horizon 1 only. Persistence baseline predicts (widehat O_{t+1}=C_t). It is a separate price-regression family. It is not converted into a close-direction label.

**No mixed statistics:** classification Brier scores, regression MAE, binary tasks, price levels, option returns and strategy P&L are never combined in the same maximum-statistic family.

## 5. Feature-pipeline classes

Pipelines are additive and use the fixed recipes in `PPR3_MODEL_SETTINGS.json`:

1. `CORE_OHLCV_TECH`: NIFTY OHLCV lags and predeclared causal features (returns, range, SMA 10/20, RSI 14, rolling return standard deviation 20). Close-derived data is usable only after that close is published.
2. `EXTERNAL_MARKET`: core plus latest-as-of global equity, USD/INR, gold/crude, Cboe VIX and rate series only where source symbol, units and availability timestamp pass PPR-4.
3. `FLOWS_OPTIONS`: core plus PIT-valid FII/FPI/DII activity, India VIX and option OI/volume/PCR/IV/Greeks only where contract mapping, capture time and source history pass PPR-4.
4. `TIMESTAMPED_SENTIMENT_FUSION`: core plus historical, timestamp-valid text sentiment and only source-specified context features whose own publication/capture timestamps also pass PPR-4.

A source missing a defensible timestamp is not assumed valid. Current articles must not substitute for historical news or tweet archives. The prior one-use Dhan approval remains spent. The pipelines in the matrix indicate permitted classes, not evidence that their data have been acquired.

## 6. Source fidelity and known exclusions

- Every active model row in the common grid is labelled as a `PROJECT-ADAPTATION` where the source-native target, data or split changes. The fact that a source paper implemented an algorithm does not make the NIFTY adaptation an exact replication.
- The 15-PDF matrix preserves source ambiguities: the ISMLA dataset contains option-like `callOpen/callHigh/callLow/callClose` fields with unresolved spot-index target; JIER uses inconsistent moving-average periods/date windows; accuracy claims in IJSDR and Naik/Inamdar lack sufficiently comparable definitions; Kumar & Sharma's 99.2152% abstract claim is located but undefined; JRFM's published full-sample feature selection is leakage-prone; the CCI table has a 68-versus-80 count mismatch.
- `C011` SOFNN remains `BLOCKED_METHOD` until a reproducible configuration is justified from the source. It is not substituted with a generic neural net.
- `C023` is a pre-registered CCI(20) state-conditioned probability-rule adaptation of the uploaded CCI options strategy. It predicts common spot direction from completed NIFTY OHLC bars and training-only conditional class rates. It is not the source's native options strategy and includes no CE/PE entries or option P&L.
- The IJSDR native 30-day LSTM task remains blocked until target endpoint and accuracy formula are resolved.
- L012 option return forecasts, L018 option-price forecasts and strategy-only papers are not NIFTY spot-direction models; they are separately labelled out-of-scope here. L031, L032, L033, L034 and L036 stay blocked as indicated in the cell matrix because only abstract/metadata/README-level evidence has been verified.
- The registry crosswalk maps all L001–L036 but does not claim full-text validation of those records. A conceptual method-family overlap is never counted as exact replication.

## 7. Fixed-fit chronological evaluation — PPR3-specific choice

The existing Phase 7 method specification uses 20-session test blocks and refits every 20 sessions. Applying that refit cadence across the full paper × pipeline × horizon × seed grid would exceed the currently approved 8,000-fit budget. PPR3 therefore proposes a distinct, bounded design: **one model fit at the outer split, held frozen over the hold-forward validation segment**. This is a deliberate protocol deviation and results must be labelled PPR3 fixed-fit hold-forward; they must not be represented as results from the prior 20-session-refit Phase 7 protocol.

1. PPR-4 must identify an eligible development panel from source- and PIT-valid records and prove the final untouched holdout's exclusion using existing holdout metadata only. The holdout observations and labels cannot be read to determine split boundaries.
2. Sort eligible development decision origins chronologically. The first 80% forms the training prefix; the following 20% forms the hold-forward validation segment. The exact row-ID lists, boundary, exclusions and hashes are frozen in the PPR-4 manifest.
3. Purge any training row whose label endpoint is equal to or later than the first validation decision timestamp. Every training label endpoint must be strictly earlier than that cutoff.
4. Fit each eligible model/pipeline/horizon/seed once using the purged training prefix. Feature scaling, imputation, feature selection, text mapping, calibration and tuning may use training rows only. Model parameters stay frozen over validation; current feature values continue to update using only data available by each decision timestamp.
5. The common validation-origin index is intersected/frozen per inferential family before any model scores are inspected. For each horizon, require the target endpoint to be known before the sealed holdout boundary. Do not drop candidate-specific dates after scoring to improve a comparison.
6. Require at least 250 valid common validation origins per family after the label-endpoint purge and data-eligibility checks. If a family cannot meet the minimum, report `NOT_ESTIMABLE`; do not promote a candidate based on a smaller subset.
7. The final untouched holdout remains unopened. PPR3/PPR4 validation is development-period screening only, not the final forward test.

This single-fit validation has lower adaptation to recent regime change than repeated refitting. That trade-off is explicit; a future refit-cadence comparison could only be added by a reviewed amendment before looking at outcomes.

## 8. Tuning, seeds and fit budget

Only 12 model/pipeline/horizon cells receive hyperparameter search, all in `CORE_OHLCV_TECH`:
- `R010` Random Forest close regression at horizons 1/2/3/5/10.
- `R029` XGBoost close regression at horizons 1/2/3/5/10.
- `R038` Random Forest next-open regression at horizon 1.
- `R041` XGBoost next-open regression at horizon 1.

This mirrors the Cureus source's explicit TimeSeriesSplit tuning emphasis on Random Forest/XGBoost while keeping search bounded. Random Forest has one enumerated list of 18 settings; XGBoost has eight settings. Each candidate setting uses five chronological inner-fold fits. Hyperparameter selection uses mean validation MAE. After selecting the best setting, the selected estimator's outer fit on the full purged training prefix is counted once per predeclared seed in the outer-fit budget; the implementation must not refit every hyperparameter setting on the full prefix. The other cells use the fixed defaults in `PPR3_MODEL_SETTINGS.json`; no other search is permitted.

The settings file predeclares neural seeds 20261010, 20261011 and 20261012. The budget is deliberately conservative and counts three seeds for every active cell even though ordinary non-neural estimators use a single seed:

- 1,188 active model/pipeline/horizon cells.
- Up to 3,564 outer fit calls (three seeds per cell).
- 780 additional inner-fold calls: 6 RF cells × 18 settings × 5 folds + 6 XGBoost cells × 8 settings × 5 folds.
- **Current matrix upper bound: 4,344 fit calls.**
- Global cap remains 8,000; the contract's theoretical ceiling (93 configurations × 4 pipelines × 5 horizons × 3 seeds plus 20 tuning cells × 20 settings × 5 folds) is 7,580. The 73 current counted rows are frozen; unused cap capacity is not authorization for more candidates.

Every top-level fit call, inner fold, refit, calibration step and seed must be logged. PPR-5's offline validator must reconcile the estimator-specific fit-count calculation before any run can be authorized. If implementation requires additional calibration fits not included in the contract, amend the fit budget and obtain tester approval before execution.

## 9. Statistical analysis

The exact executable equations are in `PPR_TARGET_INFERENCE_CONTRACT.json`. Key points:
- Separate inferential families for three-class direction Brier, close-price MAE improvement and next-open MAE improvement.
- Paired loss improvements computed on identical common decision origins for every candidate/horizon inside a family.
- One-sided maximum studentized mean-improvement test under a null-centered moving-block bootstrap, deterministic seed 20261010 and 10,000 replicates.
- Block length is `max(5, longest horizon in that family)`; the same sampled block-origin indices are used for every candidate and horizon within the family.
- Familywise adjusted p-value: `(1 + count(T_star >= T_obs))/(1 + B)`. Report paired mean improvement and simultaneous 95% max-statistic intervals.
- If a family has a candidate/horizon with insufficient valid common rows, finite losses or positive finite bootstrap standard error, label the family `INCOMPLETE_NOT_PROMOTABLE`; don't silently delete a cell or report a confirmatory p-value.

## 10. PPR-4 and later gates

PPR-3 approval **does not** authorize source access or model execution.

| Phase | Permitted work | Exit evidence | Status |
|---|---|---|---|
| PPR-0 | Governance/source-state review | branch roles, status/logs, existing authorizations checked | COMPLETE |
| PPR-1 | Uploaded-PDF evidence matrix | tester PASS with scoped restrictions | COMPLETE |
| PPR-2 | Map 36 literature records | tester PASS with scoped restrictions | COMPLETE |
| PPR-3 | Freeze config matrix and protocol | exact-snapshot tester report and offline check | AWAITING TESTER REVIEW |
| PPR-4 | Search permitted free sources, audit cache, dates, timestamps, missingness and sealed-holdout boundary; no model fitting | source hashes, row counts/schema/availability report, data-eligible configuration subset and frozen origin index; exact tester approval | NOT AUTHORIZED |
| PPR-5 | Deterministic model runner and offline target/sign/leakage/fit-count tests | offline CI success on exact snapshot | NOT AUTHORIZED |
| PPR-6 | Independent pre-run gate | exact tester PASS plus source/cache/workflow hashes and explicit allowed run | NOT AUTHORIZED |
| PPR-7 | Gated empirical prediction run | immutable metrics/panels/provenance artifact; no final holdout | BLOCKED |
| PPR-8 | Independent numerical/statistical artifact recomputation | tester report reproducing targets, losses, p-values and intervals | BLOCKED |
| PPR-9 | Coverage reconciliation | every proposed cell gets tested/audited, negative, blocked-data/method or rejected-at-gate status | BLOCKED |
| PPR-10 | Manuscript and final synthesis | full methods/tables/figures/appendices, all null results, limitations, future directions and final independent sign-off | BLOCKED |

**No options P&L is in PPR3.** Any subsequent long-option economics work remains behind the separate strategy/economic gate and must use current Paytm Money brokerage/statutory charges, bid/ask spreads, slippage, order/lot constraints, realistic latency and contract availability. The present proposal makes no profitability claim.

## 11. Exact-snapshot review request

Please review these current developer artifacts before authorizing PPR-4:
- `PPR3_CONFIGURATION_MATRIX.csv` — all 81 rows; 72 active configs including the CCI(20) spot-direction adaptation; one blocked SOFNN config; eight non-candidate source/task blockers.
- `PPR3_CANDIDATE_CELLS.csv` — exactly 1,188 common-task model × pipeline × horizon cells.
- `PPR3_MODEL_SETTINGS.json` — frozen defaults, pipeline recipes, seeds, exact 18-/8-setting RF/XGBoost grids and 12 tuning cells.
- `PPR3_CONFIGURATION_MANIFEST.json` — hashes, cell counts, fit budget and boundaries.
- `PPR_TARGET_INFERENCE_CONTRACT.json` — target/inference contract and PPR3 fixed-fit hold-forward protocol.

**Developer → Tester:** Audit the exact source-to-config links, task/target compatibility, duplicates, source ambiguity preservation, pipeline/horizon grid arithmetic, hyperparameter grids, training/validation chronology, label purging, max-statistic formulas, fit-call arithmetic and holdout protection. Return PASS/REQUEST CHANGES and state the exact next permitted phase.

**Tester → Developer:** Do not start source acquisition, code execution, model fitting, tuning/scoring or holdout access until an exact-snapshot decision explicitly permits the next gate.
