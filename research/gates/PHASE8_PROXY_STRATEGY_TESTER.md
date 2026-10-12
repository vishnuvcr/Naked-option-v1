# Phase 8 OHLC Proxy Strategy — Independent Tester Gate (R3)

STATUS: PASS — OHLC PROXY BACKTEST AUTHORIZED

Developer branch: phase-08-prediction-developer
Reviewed code commit: 39980ad09438e6070026cb4778b597bb7d59a15e
Runner blob SHA: 1689a00b16813795ec5256158ee10c27a92bcc1a
Synthetic test blob SHA: a128d48d2fc41851bd54a9e9c32d4809cc6a8ba2
Workflow blob SHA: e6ada53ad0070106b54888117c551fa0037ad10a

## Independent review and change rationale

- The runner, synthetic tests, full workflow, frozen cost schedule, and Phase 8 test plan were reviewed.
- The synthetic suite passed against the exact current runner/test blobs in hosted run 38219833960. The most recent workflow edit changes only source-artifact pins, adds source provenance to successful reports, and writes sanitized diagnostics to the repository after a failed run; a fresh workflow regression pass is required before the empirical job starts.
- Failed run 38219967649 is non-evidence. It reported that all 8,490,723 option rows had non-date expiry text; timestamps, strike and option side were present. No trades or strategy metrics were generated.
- Root cause is the selected original repaired composite artifact (11698879857): it preserves source OPTION rows but has the expiry_date column empty for all option rows. The repository's pre-existing enrichment run 38195812828 already created the expiry-enriched artifact 11723198817 from the same cached composite, with historical expiry mapped from a public expiry-partition file list and a weekly Tuesday-rule proxy after the latest listed date. Use that already-created artifact instead of downloading market prices or starting acquisition again.
- The workflow now pins the existing enriched artifact by ZIP SHA-256 e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736 and the immutable Phase 7 Run #994 forecast artifact by its previously approved hash. No new market-data request is introduced by this strategy run.
- The enriched dataset is still an expiry-mapping proxy, not an official point-in-time contract master. Preserve this caveat. The source data license is CC-BY-NC-4.0; non-commercial research only.
- The 4,800-config grid and four C0-C3 scenarios remain frozen. Costs retain synthetic spread/slippage, Paytm Money's historical-unverified ₹20/order fallback, and the date-effective charges from the frozen schedule.
- Results must be labelled Q1/OHLC proxy, never quote-executable. IID p-values/BH q-values are exploratory. No automatic strategy promotion.
- The new workflow success path records the enriched source artifact and expiry mapping method in the run report. The failure path writes sanitized, aggregate diagnostics, STATUS, README, ERROR_LOG and research/chat logs to the repo.

## Decision

PASS for one hosted attempt using these exact runner/test/workflow blobs, after the current workflow's regression job passes. The run may use the already-existing enriched artifact and frozen forecast only. It does not require bid/ask or a new data-validation phase. If the resulting enriched artifact still produces no eligible option rows, stop with the sanitized diagnostic and do not report that as trading performance.

**Tester → Developer:** run these exact blobs, preserve the existing artifacts, publish the full grid and trade ledger, and record any runtime failure with safe aggregate diagnostics. Do not alter the model, cost scenarios, or grid after seeing results.

**Developer → Tester:** independently audit result counts, source pins, timestamp/entry ordering, contract-expiry/lot-size caveats, fills/cost arithmetic, P&L signs, win/loss metrics and drawdowns. Return a result-level PASS/REQUEST CHANGES. Do not demand bid/ask.
