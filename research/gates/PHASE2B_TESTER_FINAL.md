# Phase 2B Tester Final Report — Source Audit PASS / Phase 2 Overall OPEN

## Independent review of the resumed hosted run

The latest Phase 2 GitHub Actions run completed successfully on the developer branch. Static validators, source acquisition, both reconciliation paths and the mandatory artifact validator all completed successfully.

### S08 — thetrademarkk/india-index-options-1m

- 96 matched NIFTY contract keys in the pre-declared near-ATM active universe.
- Official-side coverage = 100%.
- Derived-side coverage = 100%.
- Strict +/-0.25%/tick LastPric agreement = 95.8333%.
- Practical +/-1% corroboration fraction = 97.9167%.
- Maximum relative discrepancy = 2.8037%.
- Median relative error = 0.
- Spot field was unavailable in selected rows; report explicitly marks source_field_unavailable.
- Status = PASS under the separately declared practical corroboration gate, but S08 remains non-canonical.

### S31 — artist-23/nifty-options-data

- WEEK/ATM_CE and WEEK/ATM_PE produced 376 target-date rows each.
- The current files do not yield a reliable exact contract-key match to official expiry/strike/type.
- S31 therefore remains NOT_COMPARABLE / research-only and must not be used as an executable option-price feed.

### Official NSE source

- Legacy 05-Jul-2024 and UDiFF 08-Jul-2024 samples were acquired from official NSE archives and restored from the raw-data cache.
- Both schema checks passed.
- Snapshot manifests include hashes and row counts.

### Global-source layer

Endpoint probes passed for Cboe VIX, RBI reference rates/home page, LBMA, EIA, Stooq global indices, NSE sector indices and breadth. The current US Treasury source URL returned HTTP 404 and must be corrected or replaced before US-rate features are used.

## Gate decision

**PHASE 2B SOURCE-AUDIT GATE PASSED.**

**PHASE 2 OVERALL DATA GATE REMAINS OPEN.**

The repository now has a functioning canonical/derived-source framework, but this is not yet enough to begin predictive modeling.

## Required Phase 2C work

1. Freeze the actual research data window for intraday and positional studies.
2. Bulk-acquire/cache official NIFTY underlying and option EOD history for that window.
3. Acquire/validate an intraday NIFTY underlying source and a contract-level intraday options source strong enough for executable backtesting.
4. Reconcile India VIX, FII/FPI/DII and BSE timing.
5. Correct/replace the broken US Treasury source.
6. Demonstrate effective-dated historical lot-size and strike/expiry contract-master rules.
7. Produce missingness, duplicate, timestamp and PIT reports over the actual research window.
8. Demonstrate raw-cache hit repeatability.
9. Only after those checks pass should Phase 3 labels/baselines start.

## Tester instruction to developer

Create Phase 2C only after preserving this report unchanged. The next gate must target bulk data quality/PIT integrity, not prediction-model performance. Do not start Phase 3.