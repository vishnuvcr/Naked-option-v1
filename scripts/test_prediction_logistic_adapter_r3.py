"""Synthetic-only contract tests for the logistic probability adapter; no market data."""
import unittest
import numpy as np

from prediction_logistic_adapter_r3 import (
    AdapterContractError, LogisticProbabilityAdapter, binary_log_loss,
)


class LogisticAdapterTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(20261013)
        self.x = rng.normal(size=(240, 4))
        latent = 1.2 * self.x[:, 0] - 0.7 * self.x[:, 1] + 0.2
        self.y = (latent > 0).astype(int)
        self.train = np.arange(0, 180)
        self.test = np.arange(180, 240)

    def test_train_only_pipeline_emits_valid_probability_and_fixed_threshold(self):
        m = LogisticProbabilityAdapter(c=1.0).fit(self.x[self.train], self.y[self.train])
        p = m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape, (len(self.test),))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p >= 0) & (p <= 1)).all())
        np.testing.assert_array_equal(m.predict_class(self.x[self.test]), (p >= .5).astype(int))

    def test_transform_parameters_are_fit_on_training_rows_only(self):
        m = LogisticProbabilityAdapter().fit(self.x[self.train], self.y[self.train])
        np.testing.assert_allclose(m.model.named_steps["scale"].mean_, self.x[self.train].mean(axis=0))
        self.assertFalse(np.allclose(m.model.named_steps["scale"].mean_, self.x.mean(axis=0)))

    def test_logloss_matches_sklearn_reference(self):
        y = np.array([0, 1, 1, 0])
        p = np.array([.1, .8, .7, .3])
        self.assertAlmostEqual(binary_log_loss(y, p), .2899092476, places=8)

    def test_fail_closed_on_invalid_data_and_unfitted_model(self):
        m = LogisticProbabilityAdapter()
        with self.assertRaisesRegex(AdapterContractError, "MODEL_NOT_FIT"):
            m.predict_proba([[1, 2, 3, 4]])
        with self.assertRaisesRegex(AdapterContractError, "TRAINING_FEATURES_NONFINITE"):
            m.fit([[1, np.nan], [2, 3]], [0, 1])
        with self.assertRaisesRegex(AdapterContractError, "THRESHOLD_MUST"):
            LogisticProbabilityAdapter().fit(self.x[self.train], self.y[self.train]).predict_class(
                self.x[self.test], threshold=1.0
            )

    def test_no_silent_probability_clipping_for_invalid_values(self):
        with self.assertRaisesRegex(AdapterContractError, "LOGLOSS_PROBABILITIES_INVALID"):
            binary_log_loss([0, 1], [.2, np.nan])


if __name__ == "__main__":
    unittest.main()
