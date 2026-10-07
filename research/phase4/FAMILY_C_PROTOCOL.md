# Phase 4 Family C — Statistical / Time-Series Protocol

## Frozen methods

| ID | Method | Frozen implementation |
|---|---|---|
| C01 | Logistic regression | Reference to accepted Phase 3 B11 logistic baseline; no second tuning run |
| C02 | Probit | Probit on fixed lag features returns t-{1,2,3,5,10}, standardized from training only; no hyperparameter search |
| C03 | LDA/QDA | LDA and QDA on the same fixed lag-feature vector; class priors estimated from training only |
| C04 | AR direction state | AutoReg lag=5 with deterministic trend; predict next-period return sign |
| C05 | GARCH-family volatility-conditioned direction | GARCH(1,1) volatility fitted on training returns; fixed 1.2× training-median volatility state threshold; low-vol state uses persistence sign, high-vol state uses sign of the recent five-return mean |
| C06 | Markov-switching direction | Two-state Gaussian regime filter with fixed 0.95 self-transition probability; state means/variances estimated on training by return sign; online Hamilton-style filtering only |
| C07 | HMM direction | Two-state Gaussian HMM with transition probabilities estimated from training hard-state transitions; online forward filtering only; no backward smoothing on test data |
| C08 | Bayesian/local state-space | Fixed linear local-trend Kalman filter with training-estimated observation variance and fixed 0.01 process-noise multiplier; predict sign from filtered trend state |
| C09 | Change-point detection | Two-sided standardized CUSUM with fixed threshold 2.5; signal remains in detected direction until reset |
| C10 | Hawkes/self-exciting events | BLOCKED_DATA until a PIT-safe event-intensity data layer is materialized |
| C11 | Copula/dependence | BLOCKED_DATA until PIT-safe synchronized cross-market features are materialized in the Phase 4 feature factory |

## Point-in-time rule

All training data end strictly before the decision timestamp. Test probabilities are generated with forward-only filtering; no smoothed posterior or future test observations are used.

## Evaluation

Use the frozen Phase 3 horizons. Probability mapping for deterministic signals is not used here; probabilistic models emit calibrated probabilities where available. CUSUM/GARCH-regime state outputs use 0.55/0.45/0.50.

Report the same discrimination/calibration/confusion/bootstrap diagnostics as Phase 3.

## Gate

Family C passes only after independent tester reconstruction and leakage review. It is not a strategy gate; option economics remain deferred to Phase 8.
