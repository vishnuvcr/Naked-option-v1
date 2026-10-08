# Phase 7 Run #654 — Independent Tester Gate

## Scope
Run #654 / GitHub Actions run 37763242007, developer head `4f1d695f291ed32996c07f01710afcecc6f2a540`.

Artifact: `phase7-ensemble-results`, artifact ID 11551679532, GitHub artifact digest `sha256:c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`.

## Workflow gate
PASS:
- protocol validation passed
- Phase 7 detector passed
- regression suite passed
- daily/intraday/global acquisition passed
- empirical execution passed
- result schema validation passed
- artifact upload passed

## Independent artifact audit
PASS:
- 2 layers × 5 horizons × 10 candidates = 100 candidate cells present and EXECUTED.
- All candidate n values are positive.
- Accuracy, balanced accuracy and Brier scores are in valid ranges.
- Log loss is finite.
- ROC-AUC values are valid.
- Confusion-matrix arithmetic reconciles exactly to n for all 100 cells.
- P08/P09/P10 regime diagnostic counts equal chronological diagnostic counts for every layer/horizon.
- Family bootstrap p-values are in [0,1].
- Corrected moving-block bootstrap is represented in the production code and regression tests.

## Statistical result
No Phase 7 family passes the pre-registered family-level significance gate at alpha 0.05.

Daily family p-values:
- +1: 0.742
- +2: 0.738
- +3: 0.962
- +5: 0.788
- +10: 0.464

Intraday family p-values:
- +5: 0.248
- +15: 0.992
- +30: 1.000
- +60: 0.994
- +120: 0.512

The strongest raw accuracy observations are not sufficient for promotion. For example, daily P06 reaches 59.88% accuracy at +10, but balanced accuracy is 0.470 and the family-level test is non-significant (p=0.464). This is consistent with class-imbalance/base-rate behavior rather than demonstrated predictive edge.

## Gate decision
**PASS WITH SCOPED RESTRICTIONS — PHASE 7 CLOSED.**

Restrictions:
1. No P01–P10 candidate is promoted to a trading strategy.
2. Phase 8 may proceed only as a translation/execution-cost stress test of the registered candidate universe, not as evidence that Phase 7 discovered an edge.
3. Paytm Money brokerage/charges, exchange costs, spread and slippage must be applied in Phase 8.
4. Final holdout remains untouched.
5. Phase 9/10 promotion gates remain mandatory.

## Tester conclusion
Run #654 resolves the previously identified moving-block bootstrap and regime-diagnostic reconciliation defects. The empirical evidence does not establish a statistically significant Phase 7 ensemble edge. The correct research conclusion is therefore **no Phase 7 predictive candidate is promoted**, while the research proceeds to the pre-planned Phase 8 execution-cost translation.

## Developer instruction
Record this gate verbatim in the research status/error/research logs, update README status, keep the final holdout sealed, and proceed to Phase 8 only after the required Phase 8 developer/tester branches and frozen execution-cost specification are created and independently reviewed.
