# MR-0 to MR-5 Feasibility Run Proposal — R5 Frozen Composite

**Status:** PROPOSED — NOT AUTHORIZED FOR EXECUTION  
**Developer branch:** `phase-07-developer`  
**Tester branch:** `phase-07-tester`  
**Dataset:** `NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_SPOT_GAPFILL_DERIVED_REPAIR_V1`  
**Decoded CSV SHA-256:** `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`  
**Structural audit:** [R5 run 38147761301](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38147761301), tester verdict PASS WITH SCOPED RESTRICTIONS for structure only.

## Research question

Does the exact frozen composite contain a defensible point-in-time NIFTY 50 target panel and sufficient causal feature coverage for the preregistered 1, 2, 3, 5 and 10 observed-session prediction horizons, after exchange-session validation, invalid-row masking, exact timestamp matching, label-endpoint rules and holdout isolation?

## Aim and objectives

**Aim:** decide which prediction tasks and feature families are feasible before fitting any model.

Objectives:
1. Inventory only existing cached source manifests, timestamps, calendar evidence and source vintages; no new network/source requests.
2. Establish candle timestamp convention and NSE session membership from recorded provenance, not weekday heuristics alone.
3. Quantify standalone SPOT target coverage and exact future-session endpoints; never interpolate or substitute option prices.
4. Classify feature families by nonblank coverage, timestamp join validity and point-in-time evidence.
5. Check minimum training/validation origins, label-endpoint purge and immutable holdout exclusion metadata without reading holdout observations.
6. Emit only a sanitized metadata report and a tester decision; no row-level data or financial values in artifacts/logs.

## Frozen gates

| Gate | Purpose | Required evidence | Fail-closed outcome |
|---|---|---|---|
| MR-0 | Existing cache/source/calendar inventory | exact dataset identity, source vintage manifest, cached calendar provenance | `BLOCKED_MISSING_PROVENANCE` |
| MR-1 | Session and timestamp semantics | candle convention, exchange-session membership, weekend/session flags, duplicate/gap counts | `NOT_ESTIMABLE` or `PASS_WITH_EXCLUSIONS` |
| MR-2 | Target endpoint feasibility | valid standalone SPOT OHLC, exact observed-session endpoints at horizons 1/2/3/5/10, coverage counts | `NOT_ESTIMABLE` or `PASS_WITH_RESTRICTIONS` |
| MR-3 | Feature-family availability | coverage counts plus point-in-time and join-validity evidence, family by family | `BLOCKED_DATA` or `NOT_ESTIMABLE` |
| MR-4 | Split and leakage proof | train/validation origin counts, label endpoint purge, manifest proof that holdout is excluded from all fitting/tuning decisions | `BLOCKED_HOLDOUT_PROOF`, `BLOCKED_LEAKAGE`, or `INCOMPLETE_NOT_PROMOTABLE` |
| MR-5 | Tester acceptance | exact input hashes, report schema, cleanup evidence, gate-by-gate limitations | no promotion without written tester decision |

## Input and execution contract

- The only eligible input is the existing frozen composite with the decoded SHA-256 above plus already cached, versioned source/calendar manifests.
- The run must verify input identity before processing. Any mismatch, missing provenance, ambiguous candle convention or unrecognized schema fails closed.
- The implementation must run in bounded-memory chunks. Plaintext data may exist only transiently in the authorized runner's workspace; never commit or upload it.
- No external requests, token use, downloads, data gap-filling, new feature construction using future values, model libraries, fitting, tuning, predictions, performance scoring or holdout observation reads.
- Holdout exclusion must be established from metadata/manifests only. If the split manifest cannot prove isolation without inspecting outcomes, stop at MR-4 as blocked.
- All numeric outputs are aggregate counts/coverage rates, hashes, status enums and explicit exclusion counts. No price, strike, premium, timestamp-level row, symbol-level row or per-trade value may be emitted.
- The report must pass both the Python sanitizer and JSON Schema validation. Only allowlisted metadata is published.

## Predefined feature families

Check availability separately; do not assume fields exist:
- Standalone SPOT OHLCV and session-derived features.
- OPTION quote/price/volume/open-interest fields and contract metadata, with point-in-time expiry/strike identity checks.
- Expiry, time-to-expiry, Greeks, rates and dividends.
- India volatility/risk indices and NSE/BSE breadth or cross-market indicators.
- FII/DII flows and other official market statistics.
- Global index/futures/FX/commodity features, including gold where relevant.
- News/sentiment/macro features only if cached vintages prove information was available by the decision time.

Blank expiry/TTE/Greeks/rates/dividend columns must remain unavailable unless the frozen input itself contains validated nonblank observations. No synthetic reconstruction is allowed in this phase.

## Target and split protocol

- Horizons are 1, 2, 3, 5 and 10 **observed NSE sessions**, not calendar days or arbitrary minute bars.
- Target direction is based on signed simple return from the defined valid start/end SPOT prices, with the already frozen absolute-return flat tolerance (10^{-8}); invalid or missing endpoints are excluded, never imputed.
- Candle semantics and close linkage must be proved. If no official close linkage exists for a task, that task is `NOT_ESTIMABLE`.
- The current primitive minimums are at least 252 eligible training origins and 250 common validation origins, but these are necessary, not sufficient. The tester may require stricter sample-size and statistical-power justification before modeling.
- Every label's endpoint must precede the next split boundary. Any overlap/leakage blocks the gate.
- The final holdout stays sealed. This feasibility phase may verify exclusion metadata only, not view holdout observations or compute holdout labels/metrics.

## Statistical analysis in this phase

No inferential model comparison is authorized. Report descriptive denominators, missingness/coverage by session and feature family, exclusion counts, join rates, target-class counts if they can be derived without exposing row-level/holdout outcomes, and eligibility status. Avoid significance claims. If class counts would require unauthorized holdout observation access, do not calculate them.

## Deliverables

1. Exact input/source-manifest hash receipt.
2. MR-0–MR-4 sanitized gate results, including `NOT_ESTIMABLE`/blocked reasons.
3. Report-schema validation result and cleanup confirmation.
4. Updated status/error/conversation logs and README hyperlinks.
5. Tester report and machine-readable decision.

## Acceptance and stop conditions

Stop this phase after one authorized bounded execution and one tester decision. Do not retry indefinitely on a failed input; log the error and propose a corrected exact-hash request. No fitting/scoring or next research phase starts without tester acceptance of the feasibility report and a separately approved model-evaluation protocol. A blocked result is a usable research conclusion about data feasibility, not permission to bypass the gate.

**Current permissions:** proposal/design only. Real-file execution, model fitting/tuning/scoring, holdout observation access, new source requests, strategy/P&L and trading remain unauthorized.

**Developer → Tester:** Review this proposal and its exact scope; return a written decision before any implementation or empirical execution.
**Tester → Developer:** Reject any execution that lacks exact-hash authorization, source/calendar provenance, holdout isolation proof, report-schema validation or cleanup evidence.
