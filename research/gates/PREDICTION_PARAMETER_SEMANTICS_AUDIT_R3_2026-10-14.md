# Parameter-level implementation audit — 2026-10-14

Status: **BLOCKED — parameter semantics not yet fully reconciled.**

## Source-derived configuration domains

The full registry audit found these registered parameter keys that require exact adapter mapping:

- Logistic regression: C, penalty, solver (penalty=l2, solver=lbfgs).
- Bayesian dynamic logistic: coefficient_drift (0.001 or 0.01), adapter currently names this process_variance.
- Markov-switching logistic: n_regimes (2 or 3), transition_prior (2 or 5); current adapter is implemented as two regimes and does not expose transition_prior.
- HMM: covariance=diag and n_states (2 or 4); adapter is diagonal-Gaussian, so the covariance contract is compatible only for the frozen diag value.
- Temporal convolution: channels (16 or 32), kernel_size (3 or 5), dropout (0.2 or 0.4); current adapter does not implement the registered dropout parameter.
- Shallow MLP: hidden_units, dropout, weight_decay; adapter exposes these fields.

The adapter mapping audit passed file availability and registry accounting, but that is not enough to establish semantic parameter support. These mismatches are blockers, not permission to silently ignore configuration parameters.

## Required corrections before empirical fitting

1. Add a deterministic parameter-binding layer from each frozen configuration to its adapter, including value validation.
2. Add the Bayesian coefficient_drift to process_variance mapping explicitly and test equality.
3. Implement and test all registered Markov-switching regime counts and the transition-prior effect, or keep those methods blocked.
4. Implement and test the registered temporal-convolution dropout setting, or keep those methods blocked.
5. Assert HMM covariance is exactly diag for every relevant config and fail closed otherwise.
6. Verify every other family parameter is actually consumed by its adapter; reject unknown, ignored, or mismatched parameters.
7. Add synthetic tests showing parameter changes affect the intended model component, and numerical tests where applicable.
8. Re-run all family tests and independent review. No empirical fitting or holdout access until this gate is approved.

No market data was loaded, no model was fitted on market data, and the holdout remains sealed.
