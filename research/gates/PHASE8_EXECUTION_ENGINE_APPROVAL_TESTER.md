# Phase 8 Execution Engine — Corrected Independent Tester Gate

**Developer branch:** `phase-08-developer`  
**Status: PASS WITH SCOPED RESTRICTIONS**  
**Empirical option P&L:** NOT AUTHORIZED YET

## Independent re-review

The prior five execution-engine defects were corrected, and the current developer lineage was independently inspected.

### 1. Expiry/D0 eligibility

The engine now normalizes a date-only expiry to **15:30 IST on the expiry session** before applying the strict `expiry > planned_exit` test. A D0 contract can therefore remain eligible for a 15:15 forced/primary exit.

Regression coverage includes a D0 contract whose expiry is the same calendar session as the planned exit.

### 2. Non-Greek fallback

When observed delta and Black–Scholes delta are unavailable, `selection_delta()` returns a non-numeric value with `MONEYNESS_FALLBACK`. `choose_contract()` then ranks fallback candidates by smallest absolute log-moneyness rather than pretending that moneyness is delta.

The delta-target configuration is therefore not silently reinterpreted as a moneyness target.

Regression coverage verifies that the 0.40 and 0.60 configurations can intentionally collapse to the same nearest-moneyness fallback contract.

### 3. Q2 quote causality

Q2 fills now require:
- a quote timestamp;
- an executable timestamp;
- a fixed maximum quote-forward age.

Quotes before the executable timestamp or beyond the frozen stale window are rejected. Missing/stale quotes cannot silently fall through to a future quote.

### 4. Overlap ordering

The engine now distinguishes:
- signal before liquidation → blocked;
- signal exactly at liquidation → admitted only after `close_processed=True`;
- signal after liquidation → admitted.

This makes the event ordering explicit and reproducible.

### 5. Timezone/session robustness

A further consistency defect was found and corrected during re-review: trading-session DTE and the daily exit helper now compare **calendar dates** for session-indexing and return a timezone-aware 15:15 IST exit timestamp. This avoids aware/naive datetime mismatches in live execution.

Regression coverage now includes a timezone-aware session/DTE case and timezone-aware daily exit.

## Cost and mathematical checks

The previously reviewed cost decomposition remains unchanged:
- two brokerage orders;
- entry+exit premium for exchange/IPFT/SEBI turnover components;
- sale-side option STT;
- buyer-side stamp duty;
- GST on the registered taxable broker/exchange/SEBI charge base.

The delta, break-even, DTE and fill arithmetic remains internally consistent.

## Scoped restrictions

1. The actual historical option panel must provide a point-in-time session calendar. The engine will reject a contract whose decision or expiry date is not in that calendar; no calendar inference is permitted.
2. Q1 OHLC/proxy fills remain explicitly non-quote-executable.
3. The 0% dividend-yield Black–Scholes convention is frozen for ranking only and must not be tuned after observing option results.
4. This gate approves the **pure engine only**. It does not authorize the 4,800-cell empirical grid.

## Gate decision

**PASS WITH SCOPED RESTRICTIONS.**

The next required gate is the GitHub Actions/data gate: restore/cache approved data, verify the immutable Run #654 artifact digest, run reconstruction regression, run execution-engine regression, run free-source audit, and validate the generated forecast panel. Empirical option P&L remains blocked.

**Tester → Developer:** implement the workflow and forecast-panel validator exactly as specified, then submit the workflow/data gate for independent review. Do not activate empirical execution yet.
