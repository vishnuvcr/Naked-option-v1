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
