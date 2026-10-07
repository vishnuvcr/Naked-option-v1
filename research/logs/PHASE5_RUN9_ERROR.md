# Phase 5 Family D — Run 9 Error Record

Date: 2026-10-07
Developer commit tested: 8389b701c9c3f7b4392640903e7c75dd781b813b
Workflow run: 37598414089

## Failure
The mandatory regression suite failed on the newly added timezone cutoff test before empirical execution.

## Exact cause
The initial nanosecond helper normalized neither side through a common UTC parser. Under the hosted pandas 3.0.6 environment, the regression expectation for a naive DatetimeIndex did not match the helper result. This showed that the timezone regression test was stricter than the implementation contract.

## Corrective action
The helper and the actual intraday decision-time construction are now normalized through `pd.to_datetime(..., utc=True)`, and the cutoff is converted through the same UTC path before nanosecond `searchsorted`.

## Scientific status
Run #9 is rejected pre-empirical. No Family D metric is accepted. A fresh hosted run with the corrected regression test is required.
