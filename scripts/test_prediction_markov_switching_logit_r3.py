"""Synthetic-only tests for generalized Markov-switching logistic adapter."""
import unittest
import numpy as np
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
