# Phase 5 Family D — Run 4 Tester Follow-up

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer commit reviewed: `f80b08d9a4d9f244e3e9f1c8563d6cebb5d3c94b`
Hosted run: #4 / `37595265108`

## Gate result

**REQUEST CHANGES — REGRESSION FIXTURE ONLY**

The production code reached the mandatory regression suite, but the suite failed at D13 with a deterministic `[nan, nan, nan]` result.

## Independent diagnosis

The failure is explained by the fixture rather than a probability-calculation error. The test created three grouped synthetic sessions of 140 rows and passed those groups into the all-method probability check. With `train_end=300` and a 20-observation causal window, only 243 sequence endpoints are available before the test block, below the production minimum of 300. D13-D15 therefore correctly return NaN.

## Required action

Keep the separate grouped session-boundary assertion. For the all-method probability-validity check, use a single synthetic group (or a sufficiently long group) so every registered method has >=300 trainable sequence endpoints.

No empirical metric is accepted from run #4. After the fixture correction, review the fresh hosted artifact independently.

## Tester instruction to developer

Commit only the deterministic fixture correction, rerun the complete Family D workflow, and submit the resulting artifact for independent review. Do not alter model hyperparameters or promote any result.

## Developer instruction to tester

Review the fresh artifact independently, including D13-D15 session-boundary behavior in the actual intraday run, training chronology, calibration isolation, schema completeness, and all numerical metrics before any Phase 5 gate decision.
