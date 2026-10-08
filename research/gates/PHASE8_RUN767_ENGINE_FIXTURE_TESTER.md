# Phase 8 Run #767 — Tester Request Changes

## Finding
Run #767 (`37815745993`) passed protocol, workflow-contract regression and reconstruction regression; the free-source audit path is otherwise clean. Execution-engine regression failed at `test_moneyness_fallback_does_not_compare_to_delta_target`.

The fallback test again uses expiry 2026-10-30 from decision 2026-10-01 but requests D1. Under the frozen session-based DTE convention this is 21 sessions, so the valid bucket is D3. The test failure is a fixture error, not evidence against the execution engine.

## Required correction
Change only the two fallback-test DTE arguments from D1 to D3 and retain the assertions that changing the delta target cannot change the moneyness fallback choice. Add/retain the explicit 21-session D3 assertion. No engine or cost logic changes.

**Tester → Developer:** correct the fixture only, log Run #767 as non-evidence, obtain tester recheck, and rerun the engineering gate. Empirical option P&L remains prohibited.
