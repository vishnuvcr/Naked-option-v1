# Phase 8 Run #765 — Execution-Engine Moneyness Fixture Tester Request Changes

**Developer head reviewed:** `70e1b9a2a7b68b2303114598457a39d0dcef2b78`  
**Hosted run:** Research Protocol Check #765 (`37815717928`)  
**Status: REQUEST CHANGES**  
**Empirical option P&L:** BLOCKED

## Finding

The workflow-contract regression, reconstruction regression and full free-source audit passed. The execution-engine regression failed in `test_moneyness_fallback_does_not_compare_to_delta_target`:

```
assert reason1 == reason2 == "PASS"
AssertionError
```

The fixture again uses:
- decision date 2026-10-01;
- expiry 2026-10-30;
- `pd.bdate_range("2026-10-01", "2026-10-30")`;
- requested DTE bucket `D1`.

That business-day calendar gives an index distance of 21 sessions. The frozen DTE definition therefore classifies the contracts as **D3**, not D1.

## Independent assessment

- This is a regression-fixture arithmetic/specification mismatch, not evidence of a production execution-engine defect.
- It is a second occurrence of the same class of fixture error seen in the prior tie-break test.
- Run #765 is non-evidence; no option P&L was generated or accepted.
- No production execution, cost, quote, chronology or DTE implementation should be changed.
- The previous tester-approved correction for the tie-break fixture remains valid.

## Required correction

Change only the moneyness-fallback fixture’s requested DTE bucket from `D1` to `D3`.

Because the same expiry/date pair caused two fixture errors, add a direct regression assertion in this test that `trading_session_dte(2026-10-01, 2026-10-30, sessions) == 21`. This is a test-strengthening change only.

Re-run the complete Phase 8 engineering/data gate after fresh tester approval.

**Tester → Developer:** correct the DTE fixture only, add the direct 21-session assertion, record the error, obtain tester approval, then rerun the complete gate. Empirical P&L remains unauthorized.
