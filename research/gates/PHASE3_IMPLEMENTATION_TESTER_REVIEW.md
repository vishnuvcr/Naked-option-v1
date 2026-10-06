# Phase 3 Implementation Tester Review — REQUEST CHANGES

## Scope
Independent audit of the Phase 3 data/baseline implementation before accepting any empirical result.

## Findings
| Check | Result |
|---|---|
| Daily horizon-purge in B11 | PASS | h-step training labels are purged through i-h. |
| Intraday full-path horizon construction | PASS after correction | H-minute labels/features are constructed from the full 1-minute series, then evaluated on the frozen hourly grid. |
| Intraday gap feature | PASS after correction | Prior-day close is mapped from the previous session's first/last chronology rather than previous minute. |
| Intraday data adequacy | PASS | Acquisition marks LOW_POWER unless >=50k rows and >=3 years. |
| Daily B0-B8/B11 determinism | PASS | Rules and logistic parameters are fixed. |
| **Daily B0 semantics** | PASS | Constant 0.5 probability is a proper neutral benchmark. |
| **Daily B8 semantics** | REQUEST | B8 uses Thursday as a calendar-only deterministic shift; this is acceptable as a weekday effect but must not be described as an expiry-day effect. |
| **Daily B7 implementation** | **FAIL** | The code computes a volatility percentile but does not actually condition the prediction on the regime; it returns the same persistence probability in all regimes. |
| **Daily B6 definition** | PASS WITH CLARIFICATION | Range position uses current close and current-day rolling range; for a decision-time signal this is valid, but the baseline report must state that the range is strictly historical at the decision timestamp. |
| **Intraday B7 implementation** | **FAIL** | Same issue: percentile is calculated but not used in the prediction. |
| **B9/B10 status** | PASS | Not yet silently approximated; they are pending explicit global/breadth feature construction. |
| **Option economics** | NOT STARTED | No option P&L baseline has been fit yet; appropriately deferred. |

## Required corrections

1. Make B7 an actual volatility-conditioned rule. Frozen rule:
   - low volatility < 33rd training-only percentile: use persistence probability 0.55/0.45;
   - middle regime 33rd–67th: neutral 0.50;
   - high volatility > 67th: **contrarian** probability 0.45/0.55 to test whether persistence reverses in stress.
   No optimization.
2. Preserve all three regime-specific predictions in the report, including sample counts.
3. Apply the same exact rule intraday.
4. Explicitly report B6 as a past-20-observation range-position feature computed at the decision timestamp, not future range.
5. Do not re-label Thursday B8 as expiry; call it weekday/calendar.

## Gate decision
**REQUEST CHANGES**

No baseline result should be accepted until B7 is corrected and the regime-specific sample counts are reported.

## Tester instruction to developer
Fix B7 and B6/B8 documentation, append the error, then resubmit the implementation for independent tester review. Do not interpret any current B7 results.
