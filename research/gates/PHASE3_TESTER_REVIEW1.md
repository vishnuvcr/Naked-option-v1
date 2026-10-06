# Phase 3 Tester Review 1 — REQUEST CHANGES

## Independent mathematical/protocol audit

| Area | Result | Finding |
|---|---|---|
| Intraday horizons | PASS | 5/15/30/60/120-minute horizons are explicit. |
| Positional horizons | PASS | 1/2/3/5/10 sessions are explicit. |
| Future-only label timing | PASS | Horizon begins strictly after decision time. |
| Direction label | PASS | Log-return sign is mathematically valid. |
| Threshold label units | **FAIL** | `sigma_reference` is not explicitly defined in return units and horizon-matched estimation terms. An annualized volatility multiplied by a raw future return would be dimensionally wrong. |
| Triple barrier | **FAIL** | Barrier definition does not freeze how volatility is estimated (window, sampling, annualization, or whether barriers are fixed/updated). |
| Option P&L | PASS WITH CLARIFICATION | Formula is correct if `total_costs` includes both entry/exit legs; this must be explicit. |
| Delta first-order break-even | PASS WITH LIMITATION | Correct as a first-order diagnostic, but cost units must be per option unit and not per lot. |
| No-trade action | PASS | Explicitly registered. |
| Baseline families | **FAIL** | Several baselines are not fully frozen: moving-average periods, volatility-regime definition, global composite construction, breadth formula and logistic regularization are unspecified. |
| Cost scenarios | PASS | Four monotonic slippage scenarios are present and statutory rates remain unset pending period-specific verification. |
| Sample adequacy | PASS WITH CAUTION | Adequacy thresholds are stated as minimums rather than claims of sufficient power. |
| Leakage protocol | PASS | Strong timing and normalization controls. |
| Baseline-to-option linkage | PASS | Direction and option economics are separated. |

## Required corrections

1. Define `sigma_reference` in return units using a fixed historical window and the same sampling frequency as the label. Recommended frozen baseline: rolling standard deviation of the preceding 20 observations of the same decision-to-decision return frequency; annualization prohibited in label construction.
2. Freeze triple-barrier construction: for each decision, use the previous 20 same-frequency returns; barriers are ±k * standard deviation; no barrier update after decision.
3. Clarify `total_costs` as the complete round-trip cost for the exact trade, including both entry and exit statutory/brokerage charges where applicable.
4. Freeze B5 moving-average periods, e.g. 5/20 observations.
5. Freeze B7 volatility regime, e.g. rolling-20-volatility percentile over a 252-observation training history.
6. Freeze B9 global overnight composite as an equal-weight mean of standardized previous-available closes, with standardization fit only on training data.
7. Freeze B10 breadth as `(advances - declines)/(advances + declines)` using data available before the decision.
8. Freeze B11 logistic baseline: scaler fit on training fold only, L2 regularization, fixed C=1.0, solver `liblinear`, max_iter=1000, class_weight=None.
9. Add a hard rule that baseline feature parameters cannot be tuned in Phase 3; they are fixed a priori.

## Gate decision

**REQUEST CHANGES**

No model fitting should begin until the baseline definitions are deterministic enough for another researcher to reproduce exactly.

## Tester instruction to developer

Implement the nine corrections above, update the error/research logs, then resubmit Phase 3 protocol artifacts for independent tester re-review. Do not start Phase 4 methods.
