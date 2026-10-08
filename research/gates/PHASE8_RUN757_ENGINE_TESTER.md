# Phase 8 Run #757 — Execution-Engine Regression Tester Request Changes

**Developer head reviewed:** `73b6eeb7a637a91348e5ff31fb6612d2841232fd`  
**Hosted run:** Research Protocol Check #757 (`37815458405`)  
**Status: REQUEST CHANGES**  
**Empirical option P&L:** BLOCKED

## Finding

The corrected reconstruction regression now passes, and the free-source audit completed successfully. The execution-engine regression then failed at:

```
scripts/test_phase8_execution_engine.py::test_contract_selection_tie_break
AssertionError: assert reason == "PASS"
```

The fixture supplies:
- decision date: 2026-10-01;
- contract expiry: 2026-10-30;
- NSE-session calendar: business days 2026-10-01 through 2026-10-30;
- requested DTE bucket: `D0`.

The supplied session calendar has 22 business sessions from 1 October through 30 October. Therefore the trading-session DTE from 1 October to 30 October is **21**, which belongs to **D3 (11–21)**, not D0 (0–1).

The production `trading_session_dte()` / `choose_contract()` logic is consistent with the frozen DTE definition. The defect is in the regression fixture assertion.

## Independent assessment

- This is a tester-found regression-fixture arithmetic/specification mismatch, not evidence of an execution-engine production defect.
- Run #757 is non-evidence for Phase 8 empirical results.
- No Run #654 reconstruction result was invalidated.
- The free-source audit passed all registered acquisition/reconciliation/lot-size checks.
- Empirical authorization remained false and the 4,800-cell grid did not execute.

## Required correction

Correct the test fixture only so the tie-break test requests `D3` for the 21-session expiry distance. Preserve all production execution logic and all frozen economic definitions.

Re-run the full Phase 8 hosted engineering/data gate after correction.

**Tester → Developer:** change only the incorrect DTE fixture bucket, record the error, obtain fresh tester approval, then rerun the complete engineering/data gate. Do not execute empirical option P&L.
