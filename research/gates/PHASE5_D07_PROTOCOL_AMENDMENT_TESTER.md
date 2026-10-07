# Phase 5 D07 Protocol Amendment Tester Review

Date: 2026-10-07
Tester branch: phase-05-tester
Developer submission reviewed: research/gates/PHASE5_D07_PROTOCOL_AMENDMENT_SUBMISSION.md
Developer run under preservation rule: 37606785909

## Independent review

The submission correctly identifies a genuine frozen-protocol versus implementation mismatch. The repository-wide METHOD_REGISTRY definition is “D07 calibrated stacking”, while the active implementation uses a chronological base/calibration split, logistic meta-model and full-training base-model refit.

The proposed amendment does not introduce a new predictor family, feature, horizon, refit cadence, cost assumption or economic selection rule. It makes the existing calibrated-stacking implementation explicit.

## Required precision before implementation

The final amended protocol must pin the current implementation exactly, including:

- chronological split of the eligible training block at 80% base-training / 20% calibration, with the existing minimum-base-training guard of 200 observations;
- D01-D06 are fitted on base-training only for calibration predictions;
- the logistic meta-model is fitted only on the calibration subset;
- D01-D06 are then refit on the complete eligible training block before test prediction;
- the same fixed hyperparameters already registered for D01-D06 are retained;
- no post-cutoff labels enter any fitted component.

The tester will treat any change to these details as a new model-definition amendment rather than a wording clarification.

## Disposition

**PASS — PROTOCOL AMENDMENT APPROVED WITH REQUIRED WORDING PRECISION**

The developer may update the main Phase 5 protocol and add the requested deterministic D07 regression pin, provided the exact controls above are copied without result-driven alteration.

Run #16 remains rejected/non-accepted evidence because the frozen protocol wording was inconsistent with the implementation at execution time. No Run #16 metric may be used for model selection, tuning or promotion.

## Developer instruction to tester

After the main protocol and regression pin are amended, independently inspect the exact diff for D07 and confirm no other Family D definition changed. Then issue the fresh hosted-run authorization gate.

## Tester instruction to developer

Apply only the approved D07 clarification and deterministic regression pin. Preserve run #16 as non-evidence, update README/status/error/research logs, and await the tester's post-amendment gate before relying on any new Family D empirical result.
