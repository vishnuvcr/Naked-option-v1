# Phase 5 D07 Post-Amendment Tester Gate

Date: 2026-10-07
Tester branch: phase-05-tester
Developer head reviewed: c8603d76efcae7d555e7bc61432f077c72c46e0a
Fresh hosted run: 37611880308

## Independent diff review

The developer change was checked against the prior Phase 5 correction head.

The D07 protocol now exactly pins the existing implementation as a calibrated logistic meta-stack with:
- 80% chronological base-training / 20% calibration split;
- minimum base-training guard of 200 observations;
- D01-D06 fitted on base-training only for calibration predictions;
- logistic meta-model fitted only on calibration outputs/labels;
- D01-D06 refit on the complete eligible training block for test prediction;
- unchanged D01-D06 hyperparameters and chronology;
- no post-cutoff labels entering any fitted component.

The regression test independently reconstructs the same stack and checks invariance to mutation of post-cutoff labels.

No feature family, horizon, refit cadence, cost model, promotion rule, D01-D06 parameter, or D13-D15 representation was changed by the amendment.

The workflow comment change is operational only.

## Regression result

Hosted run 37611880308 has passed the mandatory Family D regression step after the D07 correction.

## Gate decision

**PASS — FRESH EMPIRICAL EXECUTION AUTHORIZED**

The developer may rely on the fresh hosted run only as execution output. The final Family D empirical gate remains pending until the immutable result artifact is independently audited.

Run #16 remains non-accepted evidence.

## Tester instruction to developer

Do not promote any D01-D15 result yet. Preserve the immutable fresh artifact, then submit it for independent numerical, chronology, denominator, D07 calibration-isolation, D13-D15 session-boundary, probability-bound and schema checks.

## Developer instruction to tester

Review the fresh immutable artifact as soon as it appears and issue the final Family D empirical gate without relying on developer interpretation.
