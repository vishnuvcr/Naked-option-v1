"""Markov-switching logistic classifier with 2/3 filtered regimes.

The registered transition_prior is a symmetric Dirichlet pseudocount added to
each expected transition count (allowed values: 2 or 5). This definition is
explicit so the parameter cannot be accepted and then silently ignored.
Training uses only rows supplied to fit(); test labels are never read.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logsumexp


class MarkovSwitchingLogitContractError(ValueError):
    pass


@dataclass
class MarkovSwitchingLogitAdapter:
    n_regimes: int = 2
    transition_prior: int = 2
    max_iter: int = 30
    ridge: float = 1.0
    random_state: int = 42
    mean_: np.ndarray | None = None
    scale_: np.ndarray | None = None
    coefficients_: np.ndarray | None = None
    intercepts_: np.ndarray | None = None
    transition_: np.ndarray | None = None
    initial_: np.ndarray | None = None
    converged_: bool = False
    last_state_posterior_: np.ndarray | None = None
    log_likelihood_: float | None = None

    @staticmethod
    def _transition_update(expected_counts, alpha):
        counts = np.asarray(expected_counts, dtype=float)
        if (counts.ndim != 2 or counts.shape[0] != counts.shape[1]
                or counts.shape[0] < 2 or not np.isfinite(counts).all()
                or np.any(counts < 0) or not np.isfinite(alpha) or alpha <= 0):
            raise MarkovSwitchingLogitContractError("TRANSITION_COUNTS_OR_PRIOR_INVALID")
        smoothed = counts + float(alpha)
        return smoothed / smoothed.sum(axis=1, keepdims=True)

    @staticmethod
    def _fit_logistic(z, y, weights, ridge, initial=None):
        d = z.shape[1]
        theta0 = np.zeros(d + 1) if initial is None else np.asarray(initial, dtype=float).copy()

        def objective(theta):
            eta = theta[0] + z @ theta[1:]
            p = np.clip(expit(eta), 1e-9, 1 - 1e-9)
            loss = -np.sum(weights * (y * np.log(p) + (1 - y) * np.log(1 - p)))
            loss += 0.5 * ridge * np.sum(theta[1:] ** 2)
            grad_eta = weights * (p - y)
            grad = np.r_[grad_eta.sum(), z.T @ grad_eta + ridge * theta[1:]]
            return float(loss), grad

        result = minimize(objective, theta0, jac=True, method="L-BFGS-B",
                          options={"maxiter": 2000, "ftol": 1e-12})
        if not np.isfinite(result.fun) or not np.isfinite(result.x).all():
            raise MarkovSwitchingLogitContractError("LOGIT_OPTIMIZER_NONFINITE")
        if not result.success:
            raise MarkovSwitchingLogitContractError("LOGIT_OPTIMIZER_FAILED")
        return result.x[1:].copy(), float(result.x[0])

    @staticmethod
    def _forward_pass(z, y, coefficients, intercepts, transition, initial):
        n = len(y)
        k = len(initial)
        eta = np.column_stack([intercepts[s] + z @ coefficients[s] for s in range(k)])
        p = np.clip(expit(eta), 1e-9, 1 - 1e-9)
        emission = y[:, None] * np.log(p) + (1 - y[:, None]) * np.log(1 - p)
        log_transition = np.log(transition)
        alpha = np.empty((n, k), dtype=float)
        alpha[0] = np.log(initial) + emission[0]
        for t in range(1, n):
            alpha[t] = emission[t] + logsumexp(alpha[t - 1, :, None] + log_transition, axis=0)
        return alpha, float(logsumexp(alpha[-1]))

    def fit(self, x_train, y_train):
        x = np.asarray(x_train, dtype=float)
        y_raw = np.asarray(y_train)
        if (x.ndim != 2 or y_raw.ndim != 1 or len(x) != len(y_raw)
                or len(x) < 60 or x.shape[1] < 1):
            raise MarkovSwitchingLogitContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all():
            raise MarkovSwitchingLogitContractError("TRAINING_FEATURES_NONFINITE")
        if (not np.isfinite(y_raw.astype(float)).all()
                or not set(np.unique(y_raw).tolist()).issubset({0, 1})):
            raise MarkovSwitchingLogitContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y_raw).tolist()) != {0, 1}:
            raise MarkovSwitchingLogitContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if (isinstance(self.n_regimes, bool) or self.n_regimes not in {2, 3}
                or not isinstance(self.n_regimes, int)
                or isinstance(self.transition_prior, bool)
                or self.transition_prior not in {2, 5}
                or not isinstance(self.transition_prior, int)
                or isinstance(self.max_iter, bool) or self.max_iter < 1
                or not np.isfinite(self.ridge) or self.ridge <= 0):
            raise MarkovSwitchingLogitContractError("MODEL_PARAMETER_INVALID")

        y = y_raw.astype(float)
        self.mean_ = x.mean(axis=0)
        self.scale_ = x.std(axis=0)
        self.scale_[self.scale_ == 0] = 1.0
        z = (x - self.mean_) / self.scale_
        n, d = z.shape
        k = self.n_regimes

        # Deterministic rank-quantile initialization generalizes to both 2 and 3 regimes.
        order = np.argsort(z[:, 0], kind="stable")
        groups = np.empty(n, dtype=int)
        groups[order] = np.minimum((np.arange(n) * k) // n, k - 1)
        coefficients = np.zeros((k, d))
        intercepts = np.zeros(k)
        for state_id in range(k):
            mask = groups == state_id
            if len(np.unique(y[mask])) < 2:
                mask = np.ones(n, dtype=bool)
            coef, intercept = self._fit_logistic(
                z[mask], y[mask], np.ones(int(mask.sum())), self.ridge
            )
            coefficients[state_id] = coef
            intercepts[state_id] = intercept

        transition = np.full((k, k), 0.1 / (k - 1), dtype=float)
        np.fill_diagonal(transition, 0.9)
        initial = np.full(k, 1.0 / k, dtype=float)
        old_log_likelihood = None

        for _ in range(self.max_iter):
            eta = np.column_stack([intercepts[s] + z @ coefficients[s] for s in range(k)])
            p = np.clip(expit(eta), 1e-9, 1 - 1e-9)
            log_emission = y[:, None] * np.log(p) + (1 - y[:, None]) * np.log(1 - p)
            log_transition = np.log(transition)
            log_initial = np.log(initial)

            log_alpha = np.empty((n, k), dtype=float)
            log_alpha[0] = log_initial + log_emission[0]
            for t in range(1, n):
                log_alpha[t] = log_emission[t] + logsumexp(
                    log_alpha[t - 1, :, None] + log_transition, axis=0
                )

            log_beta = np.zeros((n, k), dtype=float)
            for t in range(n - 2, -1, -1):
                log_beta[t] = logsumexp(
                    log_transition
                    + log_emission[t + 1, None, :]
                    + log_beta[t + 1, None, :],
                    axis=1,
                )

            log_likelihood = float(logsumexp(log_alpha[-1]))
            log_gamma = log_alpha + log_beta
            gamma = np.exp(log_gamma - logsumexp(log_gamma, axis=1, keepdims=True))

            expected_transitions = np.zeros((k, k), dtype=float)
            for t in range(n - 1):
                log_xi = (
                    log_alpha[t, :, None] + log_transition
                    + log_emission[t + 1, None, :] + log_beta[t + 1, None, :]
                )
                expected_transitions += np.exp(log_xi - logsumexp(log_xi))

            # Symmetric Dirichlet transition prior: alpha is applied per matrix cell.
            initial = np.maximum(gamma[0], 1e-12)
            initial /= initial.sum()
            transition = self._transition_update(expected_transitions, self.transition_prior)

            for state_id in range(k):
                weights = gamma[:, state_id]
                theta0 = np.r_[intercepts[state_id], coefficients[state_id]]
                coef, intercept = self._fit_logistic(z, y, weights, self.ridge, theta0)
                coefficients[state_id] = coef
                intercepts[state_id] = intercept

            # Compare convergence on the likelihood of the updated (M-step) fit.
            final_alpha, updated_log_likelihood = self._forward_pass(
                z, y, coefficients, intercepts, transition, initial
            )
            if (old_log_likelihood is not None
                    and abs(updated_log_likelihood - old_log_likelihood)
                    < 1e-5 * (1 + abs(old_log_likelihood))):
                self.converged_ = True
                old_log_likelihood = updated_log_likelihood
                break
            old_log_likelihood = updated_log_likelihood

        # Keep the stored likelihood and terminal filter synchronized with final parameters.
        final_alpha, final_log_likelihood = self._forward_pass(
            z, y, coefficients, intercepts, transition, initial
        )
        self.coefficients_ = coefficients
        self.intercepts_ = intercepts
        self.transition_ = transition
        self.initial_ = initial
        self.last_state_posterior_ = np.exp(final_alpha[-1] - final_log_likelihood)
        self.log_likelihood_ = final_log_likelihood
        return self

    def predict_proba(self, x_test):
        if self.coefficients_ is None or self.last_state_posterior_ is None:
            raise MarkovSwitchingLogitContractError("MODEL_NOT_FIT")
        x = np.asarray(x_test, dtype=float)
        if x.ndim != 2 or x.shape[1] != len(self.mean_):
            raise MarkovSwitchingLogitContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all():
            raise MarkovSwitchingLogitContractError("PREDICTION_FEATURES_NONFINITE")
        z = (x - self.mean_) / self.scale_
        state = self.last_state_posterior_.copy()
        out = []
        for row in z:
            state = state @ self.transition_
            p_state = expit(self.intercepts_ + self.coefficients_ @ row)
            out.append(float(state @ p_state))
        result = np.asarray(out)
        if not np.isfinite(result).all() or np.any((result < 0) | (result > 1)):
            raise MarkovSwitchingLogitContractError("PREDICTION_PROBABILITY_INVALID")
        return result
