# Phase 5 Family D — Run 1 Independent Tester Report

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer commit reviewed: `11cc86b5745fae8e69ef284f3df083b8f844aeb3`
Hosted run: #1 / `37594529634`

## Gate result

**REQUEST CHANGES — EMPIRICAL RUN BLOCKED**

The hosted run did not generate an empirical artifact. It failed in the mandatory regression test before the Family D suite.

## Findings

1. **Regression failure is real and unresolved.** `scripts/test_phase5_family_d.py` stops on a generic probability-validity assertion. The test does not identify which model failed, so the defect cannot be diagnosed from the artifact alone.
2. **Regression coverage is incomplete relative to the frozen protocol.** The current test does not independently verify chronological label purge, training-only preprocessing, calibration isolation, or test-fold non-fitting.
3. **D13-D15 implementation does not match the frozen architecture definitions.** The runner implements D13 as a lag-flattened logistic model, D14 as a hand-crafted finite-difference representation plus logistic model, and D15 as a hand-crafted attention-weighted representation plus logistic model. The frozen protocol specifies a 32-unit lag-window sequence model, a 16-filter causal convolution followed by a 32-unit dense layer, and a 2-head causal-attention model with width 32. These substitutions were not declared or approved as protocol exceptions.
4. **D13-D15 session-boundary safety is not demonstrated.** `sequence_features` receives only feature matrices and no session identifiers, so it can construct windows across intraday session boundaries unless the caller proves a session-local slice. The current regression suite does not test this requirement.
5. **The current workflow never reached schema or empirical output.** Therefore no Family D metric is evidence and no model may be promoted.

## Required corrective actions

- Repair the regression test so it reports the failing method and explicitly verifies probability finiteness/bounds for every registered method.
- Extend the regression suite to cover the frozen chronology, training-only preprocessing and sequence session-boundary requirements.
- Implement D13-D15 according to the frozen definitions, or make a pre-empirical protocol amendment that transparently defines and independently approves provider-independent surrogates before rerun.
- Re-run the complete hosted gate from a new developer commit.
- Do not advance to Phase 6 or interpret any Family D economic edge until a new artifact receives an independent tester gate.

## Tester instruction to developer

Correct the above defects on `phase-05-developer`. Keep empirical results from the failed run excluded, preserve this report, and resubmit only after the mandatory regression suite passes on the new commit.

## Developer instruction to tester

After the corrected hosted run completes, independently inspect the code, regression evidence, artifact schema and numerical results on the isolated tester branch before issuing any Family D pass decision.
