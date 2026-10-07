# Phase 5 Family D — Run 6 Error Record

Date: 2026-10-07
Developer commit tested: dd10674f002286374ae179b346f0522c24532e97
Workflow run: 37595617781

## Failure
Family D regression passed, but the empirical suite failed during the intraday walk-forward loop before an artifact could be produced.

## Exact cause
The cutoff calculation passed a timezone-naive NumPy datetime value from `Timestamp.to_datetime64()` into `np.searchsorted` against timezone-aware pandas timestamps. This raised:
`TypeError: Cannot compare tz-naive and tz-aware timestamps`.

## Fix
Added `cutoff_train_end()`, which converts the ordered decision timestamps and cutoff to integer nanoseconds via `DatetimeIndex.asi8` and `Timestamp.value` before `searchsorted`. Added a regression test covering both timezone-naive and Asia/Kolkata timezone-aware timestamp arrays.

## Scientific status
No Family D empirical result is accepted from run #6. Data acquisition and the full regression suite passed; only the intraday empirical execution failed.
