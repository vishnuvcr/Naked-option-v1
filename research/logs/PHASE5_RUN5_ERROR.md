# Phase 5 Family D — Run 5 Error Record

Date: 2026-10-07
Developer commit tested: 6dc3f1fb7447fada84929c83bf068948378b4746
Workflow run: 37595530652

## Failure
Regression suite failed at D13 with `[nan, nan, nan]` after the grouped-fixture correction.

## Exact cause
The all-method probability fixture used a single group but retained `train_end=300`. A 20-observation causal sequence window therefore yields only 281 trainable endpoints (300 - 20 + 1), below the production minimum of 300. D13-D15 correctly returned NaN.

## Fix
The all-method probability fixture is moved to `train_end=360` with test rows 360–362, yielding at least 300 trainable sequence endpoints while retaining the same 420-row synthetic dataset. The separate session-boundary test remains unchanged.

## Acceptance
No Family D empirical result is accepted from run #5. Fresh hosted execution is required.
