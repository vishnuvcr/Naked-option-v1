# Phase 3 Baseline Data Gaps

## Purpose

The Phase 3 baseline gate requires every registered B0-B11 baseline to appear explicitly in the result packet. A data-layer limitation may block a baseline, but it may not be silently omitted.

| Baseline | Phase 3 disposition | Reason / next action |
|---|---|---|
| B0-B8 | EXECUTE | Implemented from frozen protocol using PIT-safe NIFTY reference data. |
| B9 Global overnight | BLOCKED_DATA until required global daily histories are acquired on the Phase 3 branch with explicit availability timestamps | The Phase 2 global source manifest exists, but the current Phase 3 execution branch does not yet materialize those histories into the Phase 3 feature factory. No proxy is substituted. |
| B10 Breadth | BLOCKED_DATA until historical NSE breadth observations are acquired and publication/availability semantics are demonstrated | Official NSE breadth source is registered, but a historical PIT-safe series is not yet materialized in Phase 3. Missing denominator rows remain NO FEATURE. |
| B11 Logistic | EXECUTE with only the frozen features actually available | Available features are last return, trailing volatility and gap; India VIX/global/breadth are optional only when PIT-safe and otherwise reported as unavailable rather than replaced by unregistered features. |

## Gate rule

A `BLOCKED_DATA` result is a documented limitation, not a pass. It must include the source gap, the attempted free-source path, and the condition required to unblock it. The research may not describe B9/B10 as tested until those conditions are met.
