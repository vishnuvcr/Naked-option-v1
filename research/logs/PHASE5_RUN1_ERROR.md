# Phase 5 Family D — Run 1 Error Record

Date: 2026-10-07
Developer commit: 11cc86b5745fae8e69ef284f3df083b8f844aeb3
Workflow run: 37594529634

## Failure
The first hosted Family D run failed during the mandatory regression-test step. The empirical suite was skipped and no result artifact was produced.

## Immediate cause
The regression test asserted finite probability bounds without identifying the offending registered method. The failure occurred before empirical execution.

## Independent tester findings
The tester separately found that the regression suite did not cover all frozen controls and that the original D13-D15 implementations did not conform closely enough to their registered sequence architectures or demonstrate intraday session-boundary protection.

## Corrective action
- strengthened the regression suite to identify the offending method;
- added chronological purge, training-only preprocessing and session-boundary checks;
- implemented D13 as a 20-observation 32-unit MLP;
- implemented D14 as 16 fixed causal 3-tap filters followed by a 32-unit dense learner;
- implemented D15 as a fixed 2-head causal-attention representation of width 32 followed by a 32-unit dense learner;
- made the intraday primary Family D fit/evaluation operate on the frozen hourly decision grid while retaining exact 1-minute H-step labels;
- corrected D07 to use a chronological, training-only calibration split.

## Acceptance
The failed run is excluded from scientific evidence. The corrected developer head must pass the hosted regression gate and the independent tester gate before any Family D metric is accepted.
