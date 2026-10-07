# Phase 5 Family D — Run 4 Error Record

Date: 2026-10-07
Developer commit tested: f80b08d9a4d9f244e3e9f1c8563d6cebb5d3c94b
Workflow run: 37595265108

## Failure
The corrected Family D hosted package again stopped at the mandatory regression suite. The empirical suite was skipped and no scientific artifact was produced.

## Exact cause
The strengthened regression suite correctly identified D13 as returning `[nan, nan, nan]`. The production D13 implementation requires at least 300 trainable 20-observation sequence endpoints. The regression fixture used three grouped synthetic sessions of 140 rows but also passed those groups into the all-method probability test with a training cutoff at row 300. That leaves fewer than 300 valid sequence endpoints before the test block, so D13-D15 correctly returned NaN under their minimum-training rule.

This was a regression-fixture design error, not evidence against D13-D15.

## Fix
The session-boundary property remains tested separately with three grouped sessions. The all-method finite-probability test now uses a single synthetic group so D13-D15 have enough causal sequence endpoints to exercise their probability outputs.

## Scientific status
No Family D empirical result is accepted from run #4. The corrected test fixture has been committed to the developer branch and a fresh hosted run is required.
