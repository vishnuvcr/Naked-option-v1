"""Synthetic-only tests for generalized Markov-switching logistic adapter."""
import unittest
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import expit, logsumexp
from prediction_markov_switching_logit_r3 import (
    MarkovSwitchingLogitAdapter, MarkovSwitchingLogitContractError,
)


class MarkovSwitchingTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(812)
        n = 240
        regime = np.zeros(n, dtype=int)
        for i in range(1, n):
            regime[i] = regime[i - 1] if rng.random() < 0.95 else 1 - regime[i - 1]
        self.x = np.column_stack([
            rng.normal(np.where(regime == 0, -1, 1), 0.7),
            rng.normal(size=n),
        ])
        self.y = (regime ^ (rng.random(n) < 0.2)).astype(int)

    def test_fit_predict_contract_for_two_and_three_regimes(self):
        for k in (2, 3):
            with self.subTest(n_regimes=k):
                model = MarkovSwitchingLogitAdapter(
                    n_regimes=k, transition_prior=2, max_iter=8, random_state=12
                ).fit(self.x[:180], self.y[:180])
                p = model.predict_proba(self.x[180:])
                self.assertEqual(p.shape, (60,))
                self.assertTrue(np.isfinite(p).all())
                self.assertTrue(((p >= 0) & (p <= 1)).all())
                self.assertEqual(model.transition_.shape, (k, k))
                np.testing.assert_allclose(model.transition_.sum(axis=1), np.ones(k), atol=1e-8)
                np.testing.assert_allclose(model.initial_.sum(), 1.0, atol=1e-8)
                np.testing.assert_allclose(model.last_state_posterior_.sum(), 1.0, atol=1e-8)
                self.assertTrue(np.isfinite(model.log_likelihood_))

                # Independently reconstruct the final forward recursion from the stored fit.
                z = (self.x[:180] - model.mean_) / model.scale_
                eta = np.column_stack([
                    model.intercepts_[s] + z @ model.coefficients_[s] for s in range(k)
                ])
                p_state = np.clip(expit(eta), 1e-9, 1 - 1e-9)
                log_emission = (
                    self.y[:180, None] * np.log(p_state)
                    + (1 - self.y[:180, None]) * np.log(1 - p_state)
                )
                log_transition = np.log(model.transition_)
                alpha = np.empty((len(z), k), dtype=float)
                alpha[0] = np.log(model.initial_) + log_emission[0]
                for t in range(1, len(z)):
                    alpha[t] = log_emission[t] + logsumexp(
                        alpha[t - 1, :, None] + log_transition, axis=0
                    )
                ref_log_likelihood = float(logsumexp(alpha[-1]))
                ref_terminal_posterior = np.exp(alpha[-1] - ref_log_likelihood)
                np.testing.assert_allclose(
                    model.last_state_posterior_, ref_terminal_posterior, atol=1e-12, rtol=0
                )
                self.assertAlmostEqual(model.log_likelihood_, ref_log_likelihood, places=10)

    def test_transition_update_matches_dirichlet_pseudocount_formula(self):
        for k in (2, 3):
            counts = np.arange(1, k * k + 1, dtype=float).reshape(k, k)
            for alpha in (2, 5):
                actual = MarkovSwitchingLogitAdapter._transition_update(counts, alpha)
                expected = (counts + alpha) / (
                    counts.sum(axis=1, keepdims=True) + k * alpha
                )
                np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)
                np.testing.assert_allclose(actual.sum(axis=1), np.ones(k), atol=1e-14)

    def test_transition_prior_contract_is_pinned_by_preregistration_v2(self):
        root = Path(__file__).resolve().parents[1]
        contract_path = root / "research/registry/MARKOV_SWITCHING_TRANSITION_PRIOR_CONTRACT_V1_2026-10-14.json"
        prereg_path = root / "research/registry/PREDICTION_PREREGISTRATION_V2_2026-10-14.json"
        contract_bytes = contract_path.read_bytes()
        git_blob_sha = hashlib.sha1(
            f"blob {len(contract_bytes)}\0".encode("utf-8") + contract_bytes
        ).hexdigest()
        contract = json.loads(contract_bytes)
        prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
        pinned = prereg["model_parameter_semantics_contracts"]["markov_switching_logit"]
        self.assertEqual(prereg["schema_version"], "prediction-preregistration-v2")
        self.assertEqual(prereg["status"], "TESTER_APPROVED_SEMANTIC_AMENDMENT_CODE_ONLY_NO_EMPIRICAL_RUNS")
        self.assertEqual(contract["status"], "TESTER_APPROVED_CODE_CONTRACT_ONLY_NO_EMPIRICAL_RUNS")
        self.assertEqual(pinned["review_status"], "TESTER_APPROVED_CODE_CONTRACT_ONLY")
        self.assertEqual(prereg["tester_review"]["outcome"], "NUMERICAL_AND_FORMULA_REVIEW_PASS")
        self.assertFalse(prereg["tester_review"]["empirical_fitting_authorized"])
        self.assertEqual(pinned["path"], str(contract_path.relative_to(root)))
        self.assertEqual(pinned["git_blob_sha"], git_blob_sha)
        self.assertEqual(contract["schema_version"], "markov-switching-transition-prior-contract-v1")
        self.assertEqual(contract["registered_parameters"]["transition_prior"]["allowed_values"], [2, 5])
        self.assertEqual(contract["registered_parameters"]["n_regimes"]["allowed_values"], [2, 3])
        self.assertIn("N_ij + alpha", contract["transition_update"]["estimator"])
        self.assertFalse(contract["review_and_execution_gates"]["empirical_fitting_authorized"])

    def test_transition_prior_changes_transition_matrix(self):
        low = MarkovSwitchingLogitAdapter(
            n_regimes=2, transition_prior=2, max_iter=4, random_state=7
        ).fit(self.x[:180], self.y[:180])
        high = MarkovSwitchingLogitAdapter(
            n_regimes=2, transition_prior=5, max_iter=4, random_state=7
        ).fit(self.x[:180], self.y[:180])
        self.assertFalse(np.allclose(low.transition_, high.transition_, rtol=0, atol=1e-12))

    def test_fail_closed_for_invalid_training_and_parameters(self):
        with self.assertRaisesRegex(MarkovSwitchingLogitContractError, "BOTH_CLASSES"):
            MarkovSwitchingLogitAdapter().fit(self.x[:60], np.zeros(60))
        with self.assertRaisesRegex(MarkovSwitchingLogitContractError, "MODEL_NOT_FIT"):
            MarkovSwitchingLogitAdapter().predict_proba(self.x[:2])
        bad = self.x[:60].copy()
        bad[0, 0] = np.nan
        with self.assertRaisesRegex(MarkovSwitchingLogitContractError, "NONFINITE"):
            MarkovSwitchingLogitAdapter().fit(bad, self.y[:60])
        for kwargs in ({"n_regimes": 4}, {"transition_prior": 3}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(
                MarkovSwitchingLogitContractError, "MODEL_PARAMETER_INVALID"
            ):
                MarkovSwitchingLogitAdapter(**kwargs).fit(self.x[:80], self.y[:80])


if __name__ == "__main__":
    unittest.main()
