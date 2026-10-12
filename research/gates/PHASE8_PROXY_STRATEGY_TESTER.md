# Phase 8 OHLC Proxy Strategy — Independent Tester Gate (R4)

STATUS: PASS — OHLC PROXY BACKTEST AUTHORIZED

Developer branch: phase-08-prediction-developer
Reviewed code commit: e0d905071694aaa36ced63e190f2f6d4167cdf75
Runner blob SHA: 7e5a289187e1216768f7ba73dc92b74a82bf7788
Synthetic test blob SHA: 462aeb6364893af7678c691b9d45e114275d20ac
Workflow blob SHA: 074103e635a1c9b829a8f2794c512b0ee424d067

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


## R4 look-ahead review and additional limitations

- The previous R3 run 38220714996 may be completing on the pre-correction snapshot. Regardless of whether it produces tables, it is **NON-ACCEPTED** because it selected contracts using a stored delta derived with `greek_valuation_offset_seconds=60` while entering at the bar open. Do not promote or use it as valid performance evidence.
- The runner now accepts stored delta only where timestamp_epoch + greek_valuation_offset_seconds <= entry/decision time. Otherwise it recomputes a ranking delta from rolling_spot + source IV and expiry remaining at the entry timestamp; it does not reuse the close-valued time_to_expiry_years. Current minute nifty_close is no longer used for moneyness fallback when entry is at option_open.
- Regression tests cover stored-delta timing and exclude current-bar close fallback. The empirical job is gated behind a fresh pass of this exact runner/test snapshot and the independent tester report.
- Statistical acceptance remains exploratory; no historical winner is automatically promoted. The enriched expiry mapping remains a proxy and the output must remain Q1/OHLC proxy.
- Workflow concurrency is now isolated as `phase-08-proxy-strategy-asof-v2` so the corrected run can proceed while the superseded diagnostic run may still be active. This does not grant permission to accept the superseded output.
