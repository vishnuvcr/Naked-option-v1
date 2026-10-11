# Independent Tester Review — Phase 8 authorization SHA correction and data-gap reporting

**Decision: REQUEST CHANGES**  
**Review date:** 2026-10-11  
**Developer branch:** `phase-08-developer`  
**Reviewed developer snapshot:** `6e1fe57ce0e1e21e82c676cf8bf2fcbb3561df11`  
**Hosted synthetic gate:** [Run #38163364534](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38163364534) — contract-test job PASS; authorization job PASS only in default-disabled mode; real cached-data job SKIPPED.

## Scope and disposition

This is an independent review of the current Phase 8 authorization/hash correction and the recently changed critical-data-gap summary. It does not re-open or replace the historical R1 approval. R1's one-use request has been consumed and is disabled. This decision **does not authorize** a new data read, option P&L, holdout access, new market-source requests, or strategy promotion.

## Checks that passed

1. Compared the frozen source identity across the authorizer, the synthetic fixture, request and dataset manifest. The correct canonical CSV SHA-256 is `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204` (64 characters). The misspelled hard-coded identity in `scripts/authorize_phase8_cached_composite_preflight.py` was corrected.
2. The stale test assertion in `scripts/test_phase8_cached_composite_preflight.py` was also updated to expect the correct value in the workflow text.
3. Hosted run #38163364534 passed the encrypted-bundle regression tests, authorization contract tests, 4,800-cell runner contract, execution-cost/arithmetic tests, synthetic-only runner self-test and critical-file pin check.
4. The run's preflight job was skipped because the request is disabled. No market-data rows or P&L were accessed/generated in this run.

## Blocking finding — logical error in the critical-data-gap summary

In `scripts/run_phase8_long_option.py`, `summarize_critical_data_gaps()` currently calculates:

```python
expiry_fields_blank_for_all_option_rows = bool(option_rows) and all(
    missing_expiry_columns or blank_expiry_option_rows.get(field, 0) >= option_rows
    for field in expiry_fields
)
```

`missing_expiry_columns` is a list. If **any** required expiry column is missing, that list is truthy for every iteration of `all(...)`. As a result the summary can report `expiry_fields_blank_for_all_option_rows=True` even when the other expiry columns are present and fully populated. That is not what the field name claims and can misstate source-quality diagnostics.

### Required correction

- Make `expiry_fields_blank_for_all_option_rows` true only when `option_rows > 0`, none of the required expiry columns is missing, and every required expiry column has blank values for all option rows. Keep `expiry_fields_missing` true whenever any required column is absent or any required value is blank.
- Add a deterministic synthetic regression where one expiry column is missing but the remaining columns are populated, and assert `expiry_fields_missing=True` but `expiry_fields_blank_for_all_option_rows=False`.
- Retain the existing all-present/all-blank and all-present/populated fixtures, and add a zero-option-row case if appropriate.
- Re-run the hosted synthetic contract/runner tests on the corrected exact snapshot, then resubmit the code hash set for independent review. Do not alter data identity pins or loosen numerical checks.

## Independent execution and data restrictions

The currently observed dataset result remains a **readiness finding**, not a trading-performance result: all 4,800 configurations were `INELIGIBLE`; `expiry_date`, `expiry_mapping_source`, and `time_to_expiry_years` were blank on all observed OPTION rows; `lot_size` and `tick_size` columns were absent; point-in-time contract master and historical bid/ask coverage remain unproven. Do not calculate/claim executable historical option P&L until the separate data and exact-snapshot gates pass.

The separate daily H=1 source-derived `future_return` anomaly from run [#38162517430](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38162517430) (64 mismatches, maximum absolute difference `3.469446951953614e-18`) remains a distinct unresolved numerical-policy gate and is not addressed by this review.

## Developer → Tester / Tester → Developer

**Tester → Developer:** Correct the per-field missing-column logic, add the mixed missing/present regression, run the hosted synthetic gate, and submit the new exact blob pins. Keep R1 disabled and all empirical/holdout/promotion flags false.
