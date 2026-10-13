# Phase 8P R3 — Chronological execution supplement

**Status:** FROZEN PRE-RESULT IMPLEMENTATION SUPPLEMENT
**Amendment ID:** PHASE8P_CHRONOLOGICAL_EXECUTION_SUPPLEMENT_R3_2026-10-13

## Purpose and boundary

This supplement makes the preregistered chronological splits, row-level disposition and result-bundle completeness executable. It does not change the ten horizons, eight outer date windows, per-label purge/embargo, data-support limits, statistical metrics or correction procedure. This supplement does not itself authorize empirical fitting; all method eligibility flags remain unchanged.

Machine-readable contract: [PREDICTION_CHRONOLOGICAL_EXECUTION_CONTRACT_R3_2026-10-13.json](../registry/PREDICTION_CHRONOLOGICAL_EXECUTION_CONTRACT_R3_2026-10-13.json).

## Outer split rules

Use the eight inclusive windows frozen in the preregistration. Index data by the label-specific official eligible exchange-session sequence. A training label is mature only when its endpoint session is strictly before validation start. Also require the decision session to be strictly earlier than validation_start_index minus the frozen purge sessions. During validation, exclude the initial registered embargo sessions and score only labels whose target endpoint is inside the same validation window.

The five data-preflight blocks remain limited to positional F01 label cells. A blocked label/fold cell is not grounds to block F02–F08.

## Inner splits

Within each outer training window, use all official eligible exchange sessions before that outer validation begins. For n sessions, freeze integer cutpoints as floor(0.40n), floor(0.60n), floor(0.80n), n, producing the three expanding validation intervals [40%, 60%), [60%, 80%), [80%, 100%). No random split or result-guided boundary adjustment is allowed.

Each inner fold applies the same label-specific target maturity, purge, embargo and minimum support rules. If one inner fold fails, the config/outer-fold is blocked before fitting; it is not rerun with a replacement split.

## Row completeness and terminal states

The full registry implies 40,000 configurations × 8 outer folds = 320,000 terminal result rows. Every row, including blocked, failed and non-significant outcomes, must be preserved. Terminal states are EXECUTED_AUDITED, BLOCKED_DATA, BLOCKED_GATE, FAILED_TECHNICAL and REJECTED_EMPIRICAL.

For blocked or technical-failure rows, predictive metric, confidence-interval and p-value fields must be null. Every result bundle must have unique config/fold keys and exactly complete coverage before it is frozen. Technical failures are logged with config, method, label, fold, step, exception type and traceback hash; retries must use the same frozen inputs.

## Statistics and prohibited work in this stage

Use the registered log-loss baseline, Brier score, balanced accuracy, ROC-AUC, average precision and calibration metrics, with the preregistered session-block bootstrap and Benjamini–Yekutieli adjustment. Log-loss improvement is baseline minus candidate and both must use the same evaluation rows. Family/model selection waits until the full bundle is frozen and hashed.

No options trading strategy, entry/exit rule, trading-cost optimization or P&L-based selection belongs in this prediction-only gate. The untouched holdout remains sealed.
