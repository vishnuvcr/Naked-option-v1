# Phase 5 Protocol Tester Review

Date: 2026-10-07
Branch: phase-05-tester

## Review

The frozen Phase 5 protocol was independently inspected against the registered Family D universe and the project-wide leakage/cost/holdout rules.

### Checks
- D01-D15 are explicitly enumerated.
- Hyperparameters are fixed before empirical inspection.
- Chronological training and purge rules are explicit.
- Training-only preprocessing and calibration are explicit.
- Sequence methods have a session-boundary requirement.
- Deterministic seeds are required.
- Final holdout remains protected.
- Family C outputs are not allowed to drive the primary Family D result.
- Phase 5 is correctly treated as directional screening, not option-strategy promotion.
- Tester approval is required before empirical execution and before advancement.

### Finding

**PASS WITH SCOPED RESTRICTIONS — PROTOCOL ONLY**

Restrictions:
1. Provider-independent surrogates for D04-D06 must be reported transparently and must not be described as exact XGBoost/LightGBM/CatBoost implementations.
2. The implementation must demonstrate the stated session-boundary and training-only preprocessing controls.
3. Sequence models D13-D15 must be tested only after their regression suite passes.
4. No Family D result may be promoted until the independent artifact review is complete.

## Tester instruction to developer

Implement D01-D15 exactly as frozen, add the required regression suite, and submit the immutable hosted-run artifact for independent review. Do not change hyperparameters after observing empirical results.
