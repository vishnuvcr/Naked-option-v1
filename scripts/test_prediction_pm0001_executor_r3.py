"""Synthetic-only tests for the PM0001 chronological fold fitter."""
from __future__ import annotations
import unittest
import numpy as np

from prediction_pm0001_executor_r3 import PM0001ExecutionError, fit_pm0001_outer_fold


class PM0001ExecutorTests(unittest.TestCase):
    def fixture(self):
        rng = np.random.default_rng(20261014)
        n = 240
        session = np.arange(n)
        x = rng.normal(size=(n, 5))
        latent = 0.8 * x[:, 0] - 0.5 * x[:, 1] + 0.35 * np.sin(session / 9)
        y = (latent > np.median(latent)).astype(int)
        endpoint = session + 1
        # Last outer training labels mature before session 180.
        return x, y, session, endpoint

    def run_fit(self, *, endpoint_override=None, c=1.0):
        x, y, decision, endpoint = self.fixture()
        if endpoint_override is not None:
            endpoint = np.asarray(endpoint_override)
        return fit_pm0001_outer_fold(
            x, y, decision, endpoint,
            fold_id="F01", validation_start_session=180,
            validation_end_session_exclusive=230, purge_sessions=2,
            embargo_sessions=2, c=c, min_outer_train_rows=80,
            min_outer_validation_rows=20, min_inner_train_rows=20,
            min_inner_validation_rows=10,
        )

    def test_fit_is_chronological_and_returns_valid_metrics(self):
        result = self.run_fit()
        self.assertTrue(result.model_fitting_performed)
        self.assertFalse(result.holdout_accessed)
        self.assertTrue(all(i < 178 for i in result.train_indices))
        self.assertTrue(all(182 <= i < 229 for i in result.validation_indices))
        self.assertGreaterEqual(result.oof_rows, 20)
        self.assertAlmostEqual(result.log_loss_improvement,
                               result.baseline_log_loss - result.candidate_log_loss, places=12)
        for value in (result.baseline_log_loss, result.candidate_log_loss,
                      result.brier_score, result.balanced_accuracy,
                      result.roc_auc, result.average_precision):
            self.assertTrue(np.isfinite(value))

    def test_unmatured_training_target_is_excluded(self):
        x, y, decision, endpoint = self.fixture()
        endpoint[170] = 180
        result = self.run_fit(endpoint_override=endpoint)
        self.assertNotIn(170, result.train_indices)

    def test_validation_target_must_end_inside_fold(self):
        x, y, decision, endpoint = self.fixture()
        endpoint[220] = 230
        result = self.run_fit(endpoint_override=endpoint)
        self.assertNotIn(220, result.validation_indices)

    def test_invalid_c_fails_closed(self):
        with self.assertRaisesRegex(PM0001ExecutionError, "C_MUST_BE_FINITE_POSITIVE"):
            self.run_fit(c=0)

    def test_endpoint_before_decision_fails_closed(self):
        x, y, decision, endpoint = self.fixture()
        endpoint[20] = 19
        with self.assertRaisesRegex(PM0001ExecutionError, "TARGET_ENDPOINT_PRECEDES_DECISION"):
            self.run_fit(endpoint_override=endpoint)


if __name__ == "__main__":
    unittest.main()
