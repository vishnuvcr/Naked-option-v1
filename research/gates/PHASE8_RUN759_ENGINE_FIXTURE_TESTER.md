# Phase 8 Run #759 — Tester Request Changes

## Finding
Run #759 (`37815524247`) passed protocol and the complete reconstruction regression, and the free-source audit passed. Execution-engine regression failed at `test_contract_selection_tie_break`.

The test uses expiry 2026-10-30 from decision 2026-10-01, which is 21 NSE business-session steps and therefore belongs to the frozen D3 bucket (11–21), not D0. The test incorrectly requests D0. This is a regression-test fixture error, not trading evidence and not an engine-result finding.

## Required correction
Change only the test fixture's DTE bucket from `D0` to `D3` (or use a date pair genuinely in D0). Preserve the contract-selection tie-break assertions and all registered execution/cost rules. Add an explicit assertion documenting the 21-session D3 mapping so this cannot recur.

**Tester → Developer:** correct the fixture only, log Run #759 as non-evidence, obtain tester recheck, and rerun the engineering gate. Empirical option P&L remains prohibited.
