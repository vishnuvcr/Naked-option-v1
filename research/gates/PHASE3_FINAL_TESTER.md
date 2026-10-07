# Phase 3 Independent Tester Final Gate — PASS WITH SCOPED RESTRICTIONS

## Review target

Developer Phase 3 empirical run #117, commit `68aa1e06977a9076c9274367fb4f496411f90342`, artifact `phase3-data-and-baselines` (artifact 11464120657).

## Independent verification

The tester independently checked the immutable artifact and the current developer implementations against the frozen Phase 3 protocol.

### Verified

- Protocol CI passed for the run.
- Official/free NIFTY daily acquisition completed: 1,670 observations from 2020-01-01 to 2026-09-30, with official NSE overlap checks recorded.
- Intraday reference is pinned to HF revision `0f4800e43e6f96cec0794369d78eb4d3c4211ef5`; 486,050 source rows, with 471,346 regular-session rows and 8,441 frozen hourly-grid rows.
- Official NSE overlap checks for 2024-07-05 and 2024-07-08 matched exactly.
- Daily horizons are exactly {1,2,3,5,10}; intraday horizons exactly {5,15,30,60,120}.
- Every horizon contains explicit B0-B11 dispositions.
- All executed baseline confusion matrices reconcile to n and reported accuracy.
- Probability-bin counts equal the metric evaluation n for every executed baseline checked in the artifact.
- Intraday B3 uses previous-session close.
- Intraday B4 uses the registered `min(H,30)` momentum lookback.
- B6 uses a prior-range shift rather than including the current bar in the range.
- B11 uses a purged training endpoint and training-only scaling; the current developer implementation uses a pre-registered once-per-session intraday refresh.
- Daily and intraday B8 are now endpoint-aware: a historical label is eligible only when its future endpoint is strictly before the decision timestamp/date.
- The mandatory combined B8 synthetic regression test passed in the hosted run.
- The result-schema validator passed and enforces baseline coverage plus probability-bin denominator consistency and static B8 PIT guards.
- No accepted result from the previously rejected run #97 is carried forward as evidence.

## Scoped restrictions

1. B9 global-overnight remains `BLOCKED_DATA` because the PIT-safe global feature layer is not yet materialized in the Phase 3 baseline feature factory.
2. B10 breadth remains `BLOCKED_DATA` because the PIT-safe historical NSE breadth layer is not yet materialized in the Phase 3 baseline feature factory.
3. The daily bulk dataset uses Yahoo Finance as a free derived backfill after explicit NSE overlap validation; it is not treated as exchange-canonical.
4. The intraday dataset is a derived CC-BY-NC-4.0 research reference, not a canonical NSE execution feed.

These restrictions do not invalidate the registered B0-B8 and B11 baseline gate, but B9/B10 must not be described as tested until their PIT-safe layers are added.

## Phase 3 decision

**PASS WITH SCOPED RESTRICTIONS.**

Phase 3 label/data/baseline implementation is accepted for progression to Phase 4 single-family method research.

This is not a conclusion that direction is predictably profitable. The current baseline results are mostly near chance, with some modest positive/negative deviations that require formal statistical and economic testing. No strategy is promoted from Phase 3.

## Tester instruction to developer

Advance to Phase 4 only within the pre-registered method registry. Preserve the Phase 3 artifact and scoped B9/B10 restrictions, and submit each Phase 4 family through an independent tester gate before moving onward.
