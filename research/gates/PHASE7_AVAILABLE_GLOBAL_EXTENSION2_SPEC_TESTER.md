# Independent Tester Review — Phase 7 Available-Data Prediction Extension 2 Specification

**Decision: REQUEST CHANGES — source-feasibility gate not yet authorized.**  
**Review date:** 2026-10-10  
**Reviewed developer spec:** `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md`  
**Scope:** specification/source-plan review only. No data was downloaded, no feature table was created, and no model was fit.

## What passes at proposal level

- The seven candidate IDs are already in the method registry: G03, G14, G15, G17, F03, F04 and F05.
- The proposal remains prediction-only, does not open the final untouched holdout, and does not enter Phase 8.
- Strict prior-session availability, explicit missingness/abstention, fixed horizons, training-only scaling, paired baselines and independent artifact validation are directionally appropriate.
- A single global maximum-statistic bootstrap across 35 method/horizon cells is a defensible way to limit selection across this new family, provided its common-row and missing-candidate rules are implemented exactly.
- The official source leads are real and relevant: NSE's F&O reports page exposes UDiFF Common Bhavcopy Final plus participant OI/volume reports; NSE's historical capital-market archive lists index history and Advances/Declines; the NSE FII/FPI/DII page provides downloadable reports and explicitly notes provisional/revisable values.

## Blocking corrections

### 1. The option-history format boundary is not specified

The NSE report catalogue says the legacy F&O bhavcopy formats were discontinued effective 2024-07-08 and points to UDiFF Common Bhavcopy Final thereafter. The proposed target sample begins with the current NIFTY research history, but F03–F05 are defined only against UDiFF. That either limits the options predictors to a short post-2024 sample or leaves the earlier archive silently absent.

**Required:** explicitly choose and freeze one of:
- a post-2024-only option feature sample with a clear minimum OOS sample requirement and reduced power; or
- a versioned canonical mapping from legacy F&O bhavcopy through 2024-07-05 to UDiFF from 2024-07-08 onward, with a documented transition-date audit and regression fixtures for field/contract identity equivalence.

Given the project's free-source/composite-data requirement, the preferred correction is the second option if the legacy archive can be validated. If the transition cannot be reconciled, mark pre-transition rows `BLOCKED_DATA`; do not silently mix formats.

### 2. FII/FPI and DII normalization denominator is undefined/unavailable as written

G14/G15 say to divide each category's net flow by "prior-session NIFTY traded value". There is no single traded-value field for the NIFTY index itself in the FII/DII report, and the spec does not define whether this means turnover in NIFTY 50 constituent equities, total NSE cash-market turnover, or combined NSE/BSE/MSEI turnover. These denominators are not interchangeable.

**Required:** freeze a denominator available from the same source/vintage. Recommended formula for category (c):
[
flow_imbalance_{c,t} = \frac{buy_{c,t}-sell_{c,t}}{buy_{c,t}+sell_{c,t}}
]
with explicit zero-denominator handling, while retaining net rupee flow as a separate diagnostic only. If a turnover-normalized alternative is preferred, specify the exact market universe and source file.

### 3. F04 and F05 need unambiguous arithmetic

F04 currently says "first difference ... and its causal one-session change", which can mean either one feature or two, and does not define the acceleration formula.

**Required:** explicitly define:
- (L_t = \log(1 + OI^{1-45DTE}_{put,t} + OI^{1-45DTE}_{call,t}))
- (Delta L_t = L_t-L_{t-1})
- (accel_t = Delta L_t-Delta L_{t-1})

All terms must use the frozen eligibility window as evaluated on their own source date; missing sessions must not be forward-filled. Document that expiry-window roll effects are part of this feature.

F05's "difference between aggregate put and call log(1+volume/OI)" does not specify aggregation order. Freeze it as:
[
pressure_t=\log(1+\frac{\sum put\ volume}{\sum put\ OI})-
\log(1+\frac{\sum call\ volume}{\sum call\ OI})
]
over eligible contracts with positive OI, and record eligible contract counts/coverage by side. Do not average per-contract ratios unless that is explicitly chosen and preregistered.

### 4. G03's sector universe needs canonical names/symbols

"Energy/Oil & Gas" is not a canonical index name and the spec provides no symbol mapping. The frozen set must not rely on an ambiguous alias.

**Required:** list exact NSE historical index names and provider/source identifiers for all ten sector series, including the exact Energy index. Verify identity and overlap coverage before fitting. If any required series is unavailable, the full frozen G03 candidate is `BLOCKED_DATA`; do not change constituents after seeing results.

### 5. Global bootstrap requires a deterministic data schema for incomplete horizons

The global max test says to use a common date grid where all horizon labels are observed and treat an unavailable candidate forecast as zero improvement. The spec must also define what happens when a candidate is unavailable on some dates due to a missing feature, while still being present on other dates: its paired metrics must use only eligible rows, but the family differential must use zero improvement on those common rows. Add a concrete synthetic fixture with a missing candidate forecast at one date and prove the global statistic remains defined and deterministic.

## Required resubmission

1. Amend the spec only; do not download full history or fit models yet.
2. Add exact sector identifiers, normalized flow formulas, F04/F05 formulas, and legacy-to-UDiFF transition handling.
3. Add the synthetic common-grid/abstention bootstrap example and source-transition fixtures to the planned regression requirements.
4. Update the developer submission and research logs with this tester decision.
5. Resubmit the new spec blob for an independent re-review.

**Tester → Developer:** Correct the five items above and resubmit the exact specification. Do not proceed to source-feasibility downloads until a new tester decision explicitly passes Gate A.

**Developer → Tester:** Re-review the corrected exact spec, formulas, source-format boundary and missing-candidate bootstrap behavior. A spec pass may authorize only the small-sample source-feasibility step, not full-history acquisition or empirical prediction.


## Final specification re-review — 2026-10-10

**Decision: PASS WITH SCOPED RESTRICTIONS — Gate A small-sample source feasibility ONLY.**  
**Full-history acquisition: NOT AUTHORIZED. Model fitting/empirical prediction: NOT AUTHORIZED.**  
**Exact reviewed developer spec blob:** `8b5f17dd05c2f2d379142ca8eb2779149ca0fdbc`.

### Corrections verified

1. The legacy F&O bhavcopy / UDiFF transition is explicitly mapped at the 2024-07-08 format boundary; unreconciled fields/periods must be marked `BLOCKED_DATA`.
2. G14/G15 use the defined same-report flow imbalance `(buy-sell)/(buy+sell)` with zero-denominator handling; the undefined "NIFTY traded value" denominator is removed.
3. F04 now explicitly defines log total OI, first difference, and acceleration. F05 freezes aggregation order as sum volume / sum OI by option side, then log, with counts and abstention rules.
4. G03 has two explicit sector-excess-return features and ten canonical NSE index identities; secondary provider use is conditional on a pre-run overlap audit and row-level provenance.
5. The global inference grid has a 500-common-date minimum, retains missing candidate forecasts as zero improvement before null recentering, and specifies one max-statistic bootstrap across all 35 method/horizon cells.
6. The spec preserves the strict prior-session rule, revised/provisional FII/DII vintage caveat, finite seven-method scope, untouched holdout, and no-Phase-8/no-strategy restriction.

### Gate A authorization scope

Developer may now retrieve only small deterministic samples sufficient to test source access and schema feasibility:
- one pre-transition legacy F&O archive date and one post-transition UDiFF date, plus dates around the transition boundary;
- a small set of sector-index history dates for all ten frozen identities;
- representative FII/FPI and DII report CSV rows, including at least one missing/zero-denominator edge case if present;
- representative Advances/Declines rows.

Allowed work is limited to documenting URLs, retrieval timestamps, sample hashes, schema/units, date coverage, timezone/session semantics, contract identifiers and the provisional/revision caveat. A minimal sample may be retained in the repo. Do not create full historical datasets, labels, forecast features, model fits, metrics, or p-values at Gate A.

### Next gate

After Gate A, developer must submit a source-feasibility report with the exact sample hashes, canonical field mappings, missingness and coverage summary, and any source fallback decision. Tester must independently review that report before full acquisition/code implementation is authorized. The source fallback tolerance for G03 must be fixed in that report before any model fitting.

**Tester → Developer:** Perform Gate A only under this scope and submit a sample-source manifest. Do not expand downloads or run a predictor.

**Developer → Tester:** Independently audit the sample hashes/schema/transition mapping and explicitly pass or reject Gate A output before full-history acquisition or model fitting.


## G17 source fallback amendment review — 2026-10-10

**Decision: PASS WITH SCOPED RESTRICTIONS — amended specification may proceed to revised Gate A source sampling only.**  
**Reviewed amended spec blob:** `a5e65b56f9aa23c8292b718403c3db4448dad2e3`.  
**Full-history acquisition/model fitting remain NOT AUTHORIZED.**

### Review finding

The official Advances/Declines page sample did not expose a dated historical table. The amended proposal therefore uses a deterministic source-selection rule: use official historical A/D only if Gate A verifies at least 500 dated sessions; otherwise derive the same directional breadth form from official daily equity bhavcopy, provided the derived source passes the sample and schema checks. The fallback is defined before fitting and cannot be chosen based on model results.

The derived-universe rule is explicit: `SERIES=EQ`, ISIN prefix `INE`, positive close and positive traded quantity on both source sessions, matched by ISIN; counts advances, declines and unchanged closes; computes net breadth and its causal five-session sum. The definition is acceptable for a separately labelled derived-breadth source variant, with these restrictions:

1. Record the source variant (`official_archive` or `derived_equity_bhavcopy`) in the source manifest and freeze the choice before full-history acquisition/model fitting.
2. Gate A must confirm the actual legacy and UDiFF equity-bhavcopy column names, units, ISIN coverage and distinct trade dates on both sample dates.
3. The derived fallback must not be described as the official exchange-published breadth series. It is a reproducible breadth estimate from the frozen eligible equity universe.
4. Keep row-level eligible-security counts and source hashes. If source/ISIN coverage is inadequate or date alignment fails, mark G17 `BLOCKED_DATA`; do not relax the filter or substitute current constituents.
5. This source-selection rule is part of the registered spec and may not be changed after model results are seen.

### Next gate

The developer may revise the Gate A sampler to include official `ind_close_all_DDMMYYYY.csv` samples and two daily equity bhavcopy samples, then submit the exact revised sampler for code review before its workflow runs. No full history, feature table, labels, or model fit is authorized.

**Tester → Developer:** Proceed with a revised bounded sampler and tests, then request independent code review. The source feasibility output must verify both sector-index identity and derived-breadth field mapping.

**Developer → Tester:** Do not run a revised workflow until the exact sampler/tests receive a code-gate PASS; do not proceed beyond small samples without a separate artifact review.
