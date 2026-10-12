# Phase 8 Run 38222296903 — Preliminary Developer Audit

Date: 2026-10-12  
Run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38222296903  
Artifact: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38222296903/artifacts/11736907952  
Run commit: `368a3d19e615f8ea09a2006b6b709fc66d8946e3`  
Artifact ZIP SHA-256: `07ede4908c9a49e78de9a3aec711ac514de78f16437a825a063b6d4eb0902d54`

## Disposition

**Computed proxy results exist; result-level acceptance is pending independent tester review. No strategy is promoted.** The workflow's overall failure is a publication/rebase failure, not a failure of the numerical grid itself.

The artifact report declares `COMPLETE_PROXY_BACKTEST`, 4,800 configurations, 19,200 config/scenario summary rows, and 1,596,680 ledger rows per cost scenario. The workflow later attempted to commit the generated report and CSV summaries but encountered merge conflicts in `README.md`, `research/logs/CHAT_LOG.md`, and `research/logs/RESEARCH_LOG.md`. The failure-handler then wrote a contradictory `FAILED_NO_METRICS` diagnostic even though the artifact contains metrics. That status must be corrected; do not use the failure-handler JSON as evidence that no metrics exist.

## Preliminary C3 results

Only two configurations have both at least 30 trades and positive net P&L in scenario C3:

| Configuration | Trades | Net P&L | Win rate | Profit factor | BH screening q |
|---|---:|---:|---:|---:|---:|
| `daily-H2-P05-D0.40-D3-X0` | 72 | ₹2,398.86 | 47.22% | 1.024 | 0.3990 |
| `intraday-H120-P02-D0.40-D1-X2` | 220 | ₹836.66 | 16.82% | 1.015 | 0.0365 |

These remain exploratory. The second candidate has a negative reported mean return (-23.05%) and median return (-54.57%) despite positive rupee P&L, which requires independent reconciliation of return denominators and P&L aggregation. The BH-adjusted IID screening values are not confirmatory significance tests. Other high-P&L rows often have fewer than 30 trades and should not be selected from an in-sample grid.

## Developer-side ledger diagnostics (tester must reproduce independently)

- C0–C3 net P&L is non-increasing trade-by-trade across all ledger rows: zero monotonicity violations observed.
- All 1,596,680 trade rows use `BLACK_SCHOLES_RAW_IV_AT_DECISION_PROXY`. Point-in-time availability of the raw IV input has not been independently established. Until provenance is proven, all affected contract-selection results remain unverified.
- All intraday ledger entries occur exactly 60 seconds after decision timestamps. Daily signals have next-session entries and must be assessed against the daily convention, not the intraday 120-second cap.
- Off-tick fills are widespread (tick ₹0.05). Counts out of 1,596,680 rows for entry/exit fill values:
  - C0 entry 1,504,060; exit 1,513,781
  - C1 entry 1,539,840; exit 1,544,942
  - C2 entry 1,483,857; exit 1,493,659
  - C3 entry 1,381,963; exit 1,403,171
  These counts show the need for a conservative tick-rounding sensitivity; they do not by themselves quantify the P&L impact.
- Existing R1–R9 audit risks still apply, including incorrect maximum drawdown percentage calculation, OHLC structural validation, raw-IV timing/provenance, tick rounding, and the missing registered contemporaneous-liquidity tie-break.
- Do not sum P&L across the 4,800 configurations and describe it as portfolio P&L; the configurations reuse overlapping signals and do not share a capital-allocation model.
- Execution quality remains Q1 OHLC proxy, not quote-executable. The report also documents lot-size transition uncertainty, so absolute rupee P&L is exploratory.

## Required tester gate

Independently verify artifact hash/schema/counts; reconcile ledger to summaries; recalculate cost arithmetic, P&L signs, win/loss counts, profit factor, drawdown rupees and a corrected drawdown percentage; verify as-of IV provenance, tick rounding sensitivity, OHLC structure, entry/exit order, duplicates, and the liquidity tie-break; then issue PASS or REQUEST CHANGES with pinned evidence.

**Developer → Tester:** reproduce every diagnostic independently and issue a hash-pinned result-level decision. Do not rely on this preliminary audit as the tester conclusion.  
**Tester → Developer:** do not promote a configuration or advance Phase 9 until the result-level gate passes.
