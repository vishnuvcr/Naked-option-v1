# Phase 5 Family D — Run 4 Research Log

## Step
Hosted correction-set run #4 reached the mandatory regression suite after successful daily/intraday data acquisition.

## Finding
Regression failure was deterministic and diagnostic: D13 returned NaNs because the synthetic session-boundary groups left fewer than 300 sequence endpoints before the test block.

## Interpretation
The production minimum-training rule was working as coded. The regression fixture was over-constrained by simultaneously demanding three short session groups and >=300 sequence training examples.

## Correction
Keep session-boundary safety as an independent grouped-fixture assertion and run the finite-probability all-method check on a single-group fixture with the same 420-row dataset.

## Next gate
Fresh hosted Family D run; then independent tester review of the artifact. No Phase 6 transition.
