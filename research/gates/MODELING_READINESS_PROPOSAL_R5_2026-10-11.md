# Modeling-Readiness Proposal — R5 Canonical Dataset

**Status:** PROPOSED — NOT AUTHORIZED FOR EMPIRICAL EXECUTION  
**Developer branch:** phase-07-developer  
**Tester branch:** phase-07-tester  
**Dataset identity:** NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_SPOT_GAPFILL_DERIVED_REPAIR_V1  
**Frozen decoded CSV SHA-256:** cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204  
**Structural result:** R5 run 38147761301, PASS WITH SCOPED RESTRICTIONS  
**Scope:** data/target/feature/split feasibility only; no model fitting or outcome inspection.

## 1. Research question

After source-lineage and canonical-key structural validation, does the existing composite contain a sufficiently well-defined, point-in-time-valid NIFTY 50 target panel and causal feature history to support the pre-registered prediction tasks, with missingness, session membership, holdout boundaries and target endpoints made explicit?

## 2. Aim and objectives

**Aim:** determine whether, and for which feature families and target horizons, this frozen dataset is eligible for a defensible prediction experiment.

Objectives:
1. Reconcile structural results with the separately accepted derived-repair report and preserve its residual coverage restrictions.
2. Establish timestamp/candle semantics and valid NSE-session membership from already cached source metadata/calendar evidence; do not infer a valid exchange session from a weekday label alone.
3. Quantify valid standalone SPOT coverage by session and determine whether target prices/endpoints can be constructed without interpolation, nearest-time joins, or invented values.
4. Assess each feature family separately, including spot OHLCV, option-derived data, expiry/TTE, Greeks, rates/dividends, FII/DII, volatility indices, global markets, news and sentiment, using point-in-time evidence.
5. Freeze explicit eligibility/exclusion rules for all planned decision origins and compute whether training/validation minimums, label purging and holdout-exclusion proof are possible.
6. Publish a sanitized metadata-only report and a tester decision before any fitting/scoring.

## 3. Evidence currently established

R5 workflow [38147761301](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38147761301) completed successfully and its tester-role result is recorded in [REAL_FILE_PREFLIGHT_RESULT_TESTER_REVIEW_R5_2026-10-11.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/REAL_FILE_PREFLIGHT_RESULT_TESTER_REVIEW_R5_2026-10-11.md). The frozen decoded content hash matched exactly; the dataset has 8,999,865 rows and 47 columns (8,490,723 OPTION, 509,142 SPOT); canonical OPTION and separate SPOT timestamp duplicate counts, incomplete key rows, row-width errors and timestamp parse errors were zero. Plaintext/temporary database cleanup passed.

This is a **structural preflight pass only**. It does not verify NSE calendar alignment, bar timestamp convention, daily closing-price equivalence, exact target labels, session completeness, OHLC semantics, option-price semantics or leakage safety. R4's 4,148,431 duplicate count remains rejected.

The separately reviewed repair report has scoped restrictions:
- 19,021 OPTION rows remain unmatched across 421 timestamps.
- 24,847 rows retain the weekend-session-review flag.
- 382 joined OPTION rows had underlying OHLC masked for invalid exact-timestamp SPOT OHLC.
- 12 standalone SPOT rows had invalid OHLC masked; 309 SPOT volume and 11 OPTION volume values were masked.
- expiry_date, time_to_expiry_years, Greek assumptions/values, risk-free rate and dividend-yield fields are blank across all 8,999,865 rows in the R5 snapshot.
- R5 separately reports 19,415 blanks for each of NIFTY open/high/low/close and 19,330 blanks in NIFTY volume. The readiness report must reconcile these per session/row type; these counts must not be mistaken for independently verified invalid targets.

## 4. Hard boundary

This document authorizes **no execution yet**. The only proposed next execution is a single deterministic, metadata-only feasibility audit against the same pinned encrypted artifact lineage, with sanitized summary output. It must not:
- fit, tune, calibrate, score or rank any estimator;
- reveal or read final holdout observations or labels;
- issue any new market-data/network/source requests;
- change reviewed R5 runtime files or re-run with another dataset;
- use option P&L, backtests, strategy economics or trading endpoints;
- publish raw row values, secrets, private keys or plaintext data to GitHub artifacts.

A separate exact-snapshot tester decision must authorize the feasibility-audit implementation and one-use request. A completed audit still would not authorize model fitting. The paper-replication protocol contract is currently PROPOSED_NOT_AUTHORIZED; this proposal does not override PPR-2/PPR-3/PPR-4/PPR-6 or authorize empirical paper replication.

## 5. Finite workflow and gates

| Gate | Work | Deterministic evidence required | Exit states |
|---|---|---|---|
| MR-0 | Input/source inventory using repository files and cached manifests only | Frozen data identity, existing source and calendar artifacts, timestamps/vintages, report lineage | PASS / BLOCKED_MISSING_PROVENANCE |
| MR-1 | SPOT time/session audit | Timestamp-zone convention, per-date first/last timestamp, bars/session, duplicate session keys, calendar join, weekend flags reconciled by unique timestamp/session | PASS / PASS_WITH_EXCLUSIONS / NOT_ESTIMABLE |
| MR-2 | Target feasibility | Explicit bar timestamp semantics, session-close rule, OHLC checks, target observation counts for each 1/2/3/5/10-session horizon, missing endpoint and gap counts | PASS / PASS_WITH_RESTRICTIONS / NOT_ESTIMABLE |
| MR-3 | Feature-family coverage | Non-null/valid counts by row type/date/feature, source availability timestamps, exact-join coverage, allowed causal lookback and masking propagation | Eligible / BLOCKED_DATA / NOT_ESTIMABLE per family |
| MR-4 | Split and leakage feasibility | Pre-existing sealed-holdout exclusion metadata verified without reading holdout data; chronological origin lists and label endpoints hashed; training purge and validation counts; no-lookahead checks | PASS / BLOCKED_HOLDOUT_PROOF / NOT_ESTIMABLE |
| MR-5 | Tester review | Exact code/data hashes, all summary tables, fail-closed rules, artifact/cleanup proof and machine-readable decision | PASS_WITH_SCOPED_RESTRICTIONS / REQUEST_CHANGES |

The process ends after MR-5 with each feature family and target receiving a terminal state. A failed source/feature family does not stop a distinct estimable family, but does not license invented values or unapproved source pulls. Do not create an indefinite search loop.

## 6. Target definitions and target-provenance rule

Use the target contract only after its own status becomes authorized by its governing phase. The current contract in [PPR_TARGET_INFERENCE_CONTRACT.json](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/phase7/PPR_TARGET_INFERENCE_CONTRACT.json) is PROPOSED_NOT_AUTHORIZED. Its intended common daily tasks are:
- direction classes DOWN, FLAT, UP, fixed numerical tie tolerance |return| <= 1e-8, for 1/2/3/5/10 NSE sessions; and
- close-level regression for 1/2/3/5/10 NSE sessions, plus next-session open regression.

Target construction must use standalone, valid SPOT bars and documented candle timing. Determine from pinned source metadata whether minute timestamps denote the start or end of a candle. Establish a defensible daily closing-price rule and the relation between the last minute-bar close and an official daily close from an existing authorized source cache. Do not silently assume that the final timestamped bar is the official daily close.

If cached provenance cannot establish that rule, set the exact official-close task to NOT_ESTIMABLE for this artifact. A separately labeled adapted target (e.g., final eligible intraday-bar close) is a different estimand and cannot be substituted into a paper-native task without a prior protocol amendment and tester approval. No new official data pull is allowed in this step; source collection must separately pass PPR-4.

Labels require valid exchange-session endpoints at the exact horizon. No interpolation, nearest-bar or nearest-day substitution, forward-filling targets, or relabeling non-session dates as sessions. Missing target endpoints make that origin ineligible for that task/horizon and are counted in the sanitized report. All horizon-specific eligible rows must be enumerated before any prediction outcome is seen.

## 7. Session, missingness and quality rules

1. Use the NSE official session calendar only if already present in an authorized local cache with provenance. A Monday-Friday rule alone is insufficient. Unmatched calendar records remain NOT_ESTIMABLE.
2. Reconcile the 24,847 weekend-review flags by unique timestamp, row_type and session_date, including any real special trading sessions. Exclude unresolved flagged records from target construction and affected feature windows; do not remove records from the immutable source file.
3. Use standalone SPOT rows for index target construction; joined NIFTY fields on OPTION rows are not a replacement for a validated SPOT target panel.
4. A target OHLC bar must pass nonblank/finite checks and OHLC inequalities (high >= max(open, close), low <= min(open, close), high >= low). Masked or invalid bars cannot form targets. Rolling features depending on invalid/missing bars become missing according to a fixed lookback rule; no zero fill or backward-looking imputation.
5. Preserve missingness reasons by feature/date/row type. “Blank” is not silently mapped to zero. Exclude or flag affected labels/windows before the row eligibility manifest is frozen.
6. Treat the 19,021 unmatched OPTION observations as ineligible for any feature requiring joined underlying values. Do not nearest-time join, interpolate, or infer target prices from option prices. The pure-SPOT task family may remain assessable if its own gates pass.
7. Record per-session bar counts, first/last bar times, gaps, exact-join match rates, masked bars, target-horizon completeness and excluded-origin reasons. Only sanitized counts/ranges/hashes may leave the secure runner.

## 8. Feature-family dispositions to evaluate

| Feature family | Proposed readiness rule | Known current risk |
|---|---|---|
| Standalone NIFTY SPOT OHLC | Candidate for target and causal lag/return/rolling features only after session and bar-close semantics pass | 509,142 SPOT rows; 19,415 blanks each in NIFTY OHLC fields; session coverage unverified |
| SPOT volume | Candidate only where observed, finite and nonnegative | 19,330 NIFTY volume blanks plus 309 standalone SPOT volume values masked in repair |
| OPTION OHLC/IV/OI/volume | Separate option-feature family; must pass source-request identity, exact underlying timestamp join, per-contract completeness, no future-contract or unavailable-time leakage | 19,021 unmatched option rows; 11 option-volume values masked; SPOT-only rows have these fields blank by design |
| Expiry date / time-to-expiry | BLOCKED_DATA unless future approved artifact or already authorized cache has verifiable expiry mapping | Current fields blank in all 8,999,865 rows |
| Greeks, risk-free rate, dividend yield | BLOCKED_DATA / NOT_ESTIMABLE; never synthesize values in this gate | Current fields blank in all rows |
| FII/DII, VIX/PCR, gold or global-market features | NOT_ESTIMABLE until local cache provenance, publication/availability time and point-in-time lag are documented | Not cleared by R5; no new source retrieval authorized here |
| News/social sentiment | NOT_ESTIMABLE until original publication and ingestion/vintage timestamps precede decision time | Not cleared by R5; no new source retrieval authorized here |
| Corporate actions / index constituents | NOT_ESTIMABLE for affected historical periods without point-in-time adjustment/vintage evidence | No new source retrieval authorized here |

Feature families are reported independently. An absent field may block only the feature family that needs it; it cannot be zero-imputed or used to stop otherwise valid pure-SPOT research.

## 9. Point-in-time and split requirements

- All timestamps are normalized to Asia/Kolkata for decision logic, while raw source timestamps and epoch values remain immutable.
- Every predictor must have a defensible availability time no later than its decision cutoff. For news/social data, both source publication and ingestion times must precede cutoff. For FII/DII and volatility snapshots, publication/capture time is required; event date alone is insufficient.
- Every training target endpoint must be strictly earlier than the next decision origin used to train/validate. Purge any training row whose label reaches or overlaps the validation interval. For horizons 1/2/3/5/10 sessions, use actual eligible NSE sessions, not calendar days.
- Do not use final holdout contents to choose features, target endpoints, missingness rules, sample dates or eligible configurations. Prove exclusion only from existing holdout metadata/hash. If that metadata cannot be verified without reading holdout data, return BLOCKED_HOLDOUT_PROOF and do not fit.
- The target contract proposes at least 252 training origins and at least 250 common validation origins. Check counts from eligibility metadata only; if these minima or common-origin completeness cannot be met, mark that family NOT_ESTIMABLE/INCOMPLETE and do not lower the threshold after viewing outcomes.
- Feature scaling, imputation (if approved in a future phase), feature selection, calibration and tuning must be fit within each training prefix only. This readiness phase does not run any of them.

## 10. Sanitized outputs and acceptance criteria

The one-use audit, if later authorized, must emit:
1. A machine-readable report with exact dataset/content SHA, source lineage, schema, row counts, session coverage, quality flags, key and endpoint coverage, per-feature-family disposition, target/horizon counts, origin-index hashes, split/purge counts and reason-coded exclusions.
2. A coverage table with no raw row-level prices or contract values.
3. A test receipt, workflow/run ID, exact file hashes and plaintext-cleanup proof.
4. A terminal tester decision that explicitly says which readiness scope passed; model fitting stays closed by default.

All of the following are required for a pure-SPOT family to pass readiness: valid and provenance-grounded bar semantics; session membership reconciled; OHLC and timestamp constraints pass; label endpoints exactly defined and complete enough to meet frozen sample minima; leakage/purge checks pass; sealed holdout exclusion proven; and exact snapshot/data lineage reviewed. Option-derived or external feature families require their own additional coverage and PIT evidence. A successful workflow alone does not change permission flags.

## 11. Deterministic synthetic test plan required before implementation approval

The developer must deliver offline tests for:
- valid versus non-session/special-session calendar membership;
- minute timestamp start-versus-end ambiguity causing a fail-closed state when unresolved;
- duplicate or missing SPOT session keys;
- OHLC inequality failures, nonfinite values and missing volume propagation;
- a weekend flag on an official special session versus a genuinely unresolved weekend row;
- exact horizon indexing over NSE sessions (1/2/3/5/10) without calendar-day arithmetic;
- absent target endpoints, label sign and FLAT tolerance;
- train/validation boundary and label-end purge at each horizon;
- missing holdout manifest metadata producing BLOCKED_HOLDOUT_PROOF;
- unavailable publication/ingestion timestamps blocking feature families;
- fully blank Greeks/TTE/rate/dividend columns remaining BLOCKED_DATA instead of imputed;
- common-origin minimums and a planned candidate missing predictions producing INCOMPLETE_NOT_PROMOTABLE;
- metadata-only artifacts, no plaintext output, cleanup on success and failure.

## 12. Current terminal statuses and next work

- R5 structural integrity: PASS WITH SCOPED RESTRICTIONS.
- SPOT session and target integrity: NOT YET ASSESSED.
- Official close target: NOT ESTIMABLE until candle semantics and existing official-close provenance are demonstrated.
- Pure-SPOT causal features: CANDIDATE, NOT CLEARED.
- OPTION feature families: PENDING exact-match and availability review.
- Expiry/TTE/Greek/rate/dividend feature families: BLOCKED_DATA on the current snapshot.
- FII/DII, volatility, global market, news/social and corporate-action families: NOT_ESTIMABLE until existing cache and point-in-time provenance audit; no new sources in this gate.
- Holdout exclusion: PENDING metadata proof; if no proof, BLOCKED_HOLDOUT_PROOF.
- Prediction fit/scoring and option strategy/P&L: CLOSED.

**Finite stopping rule:** complete the approved MR-0–MR-5 evidence collection once. Publish PASS, PASS_WITH_RESTRICTIONS, BLOCKED or NOT_ESTIMABLE for every target/feature family. Continue only through a newly reviewed finite phase with a specific scope; no indefinite retries and no model fit until all upstream literature/protocol/data gates explicitly allow it.

**Developer → Tester:** Audit this proposal and JSON scope for scientific target validity, coverage logic, leakage, holdout protection and scope boundaries. Approve documentation/contract only if sound.

**Tester → Developer:** Return an exact-hash decision. Do not authorize data fitting, holdout access, source requests, or strategy/P&L by implication.
