# Independent Tester Review — Daily H=1 source-derived future-return mismatch

**Decision: REQUEST CHANGES**  
**Date:** 2026-10-11  
**Evidence run:** [#38162517430](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38162517430)  
**Failed job:** `phase8-long-option-gated / phase8-forecast-reconstruction` (job `114538420772`)  
**Diagnostic artifact:** [11710103232](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38162517430/artifacts/11710103232)

## Evidence independently checked

The source-alignment check failed in daily H=1 with 64 exact-float mismatches and reported maximum absolute difference `3.469446951953614e-18`. Sample pairs differed by about one ULP at their respective magnitude, e.g. `0.006094646255253335` vs `0.006094646255253336` (absolute difference `8.673617379884035e-19`). The error came from `verify_panel_source_alignment()` using `np.array_equal(future_actual, future_expected, equal_nan=True)`.

The source lineage checks preceding this assertion passed: immutable Run #994 artifact/manifest hashes and source-file hashes were accepted; daily source had 1,670 rows (2020-01-01 to 2026-09-30; SHA-256 `5816b0e73f4bd1327e567249f366fbebb01a549bd539fd4743424fbefe70f5c1`); the historical `run_phase3_daily_baselines.py` blob matched the current code and uses `np.log(close.shift(-h) / close)`. The frozen Run #994 artifact remains unchanged. The observed differences are consistent with low-order floating-point rounding, but the complete observed array has not yet been independently shown to fit a bounded ULP policy; the developer must quantify that before this issue is accepted.

## Required correction

Do **not** simply change or increase the aggregate tolerance `TOL=1e-9`, round saved forecast values, regenerate the reference artifact, or loosen label/timestamp checks.

1. Add a dedicated float64 source-alignment comparator for **`future_return` only**. Accept exact-equal values (including paired NaNs and identical infinities) or finite values no more than **2 IEEE-754 float64 ULPs** apart. Reject shape changes, non-finite mismatches, and any finite mismatch greater than 2 ULPs. Return diagnostics including mismatch count, maximum absolute difference, maximum ULP distance, and representative rows.
2. Preserve exact label-direction equality and exact decision-timestamp equality. Do not mutate or round either source-derived arrays or saved artifact values. This comparator must not change metric/aggregate reproducibility tolerance or forecast-selection rules.
3. Add deterministic tests proving a 1-ULP and 2-ULP perturbation are accepted; a 3-ULP perturbation, sign/direction change, NaN-vs-number and infinity-vs-finite are rejected; paired NaNs and identical infinities are handled explicitly.
4. Re-run the hosted reconstruction from the frozen Run #994 reference. The report must show observed daily H=1 mismatch count/max ULP and that every difference is within the registered 2-ULP limit. If any row is farther than 2 ULP, **remain blocked** and diagnose it rather than raising the limit.
5. Review the exact validator/test blob hashes before accepting the fix. Keep the accepted Run #994 archive, panel bytes, metric tolerance and source pins unchanged.

## Scope and impact

This is a validation failure, not evidence that the model's forecasts are profitable or unprofitable. Forecast reproducibility is not fully accepted until this source-alignment discrepancy is safely characterized and rerun. No option P&L, holdout access, new market-source request or strategy promotion is authorized by this review. Phase 8 empirical execution remains blocked separately by missing expiry/contract metadata and unproven historical bid/ask coverage.

**Tester → Developer:** implement the comparator and synthetic tests above, report maximum ULP distance from the unchanged source arrays, then resubmit the exact file hashes. Do not access or alter the untouched holdout or promote any strategy.
