"""Numerical regression tests for preregistered statistical utilities."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prediction_statistics as stats


class PredictionStatisticsTests(unittest.TestCase):
    def test_log_loss_brier_and_balanced_accuracy_known_vector(self):
        y = [0, 1, 0, 1]
        p = [0.2, 0.8, 0.8, 0.2]
        self.assertAlmostEqual(stats.binary_log_loss(y, p), (-math.log(0.8) * 2 - math.log(0.2) * 2) / 4, places=12)
        self.assertAlmostEqual(stats.brier_score(y, p), 0.34, places=12)
        self.assertAlmostEqual(stats.balanced_accuracy(y, p), 0.5, places=12)

    def test_probability_and_label_validation_fail_closed(self):
        for y, p in [([0, 2], [0.2, 0.8]), ([False, True], [0.2, 0.8]), ([0.0, 1.0], [0.2, 0.8]), ([0], [0.2, 0.8]), ([0, 1], [0.2, float("nan")]), ([0, 1], [0.2, 1.1])]:
            with self.subTest(y=y, p=p), self.assertRaises(ValueError):
                stats.binary_log_loss(y, p)

    def test_balanced_accuracy_requires_both_classes(self):
        with self.assertRaises(ValueError):
            stats.balanced_accuracy([1, 1], [0.7, 0.8])

    def test_calibration_requires_both_classes(self):
        with self.assertRaises(ValueError):
            stats.calibration_intercept_slope([1, 1, 1], [0.6, 0.7, 0.8])

    def test_calibration_intercept_slope_recovers_identity_mapping(self):
        # Replicated predictions are deliberately not all identical; labels approximate the supplied probability.
        p = [0.1] * 100 + [0.3] * 100 + [0.7] * 100 + [0.9] * 100
        y = [0] * 90 + [1] * 10 + [0] * 70 + [1] * 30 + [0] * 30 + [1] * 70 + [0] * 10 + [1] * 90
        result = stats.calibration_intercept_slope(y, p)
        self.assertEqual(result["status"], "CONVERGED", result)
        self.assertAlmostEqual(result["intercept"], 0.0, delta=0.15)
        self.assertAlmostEqual(result["slope"], 1.0, delta=0.2)

    def test_moving_block_bootstrap_is_deterministic_and_directional(self):
        folds = [
            [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10],
            [0.02, 0.04, 0.03, 0.05, 0.04, 0.06, 0.05, 0.07, 0.06, 0.08],
        ]
        first = stats.paired_moving_block_bootstrap(folds, block_length=5, replicates=1000, seed=123)
        second = stats.paired_moving_block_bootstrap(folds, block_length=5, replicates=1000, seed=123)
        self.assertEqual(first, second)
        self.assertGreater(first["observed_mean_improvement"], 0)
        self.assertEqual(first["inferential_status"], "OK")
        self.assertGreater(first["bootstrap_unique_estimates"], 1)
        self.assertLessEqual(first["ci_low"], first["ci_high"])
        self.assertGreaterEqual(first["raw_two_sided_p_value_centered_bootstrap"], 1 / 1001)
        self.assertLessEqual(first["raw_two_sided_p_value_centered_bootstrap"], 1.0)
        self.assertEqual(first["fold_session_counts"], [10, 10])

    def test_constant_positive_or_zero_improvement_is_non_identifiable(self):
        for value in (0.1, 0.0):
            with self.subTest(value=value):
                result = stats.paired_moving_block_bootstrap([[value] * 10], replicates=100, seed=9)
                self.assertAlmostEqual(result["observed_mean_improvement"], value)
                self.assertEqual(result["inferential_status"], "NON_IDENTIFIABLE_DEGENERATE_RESAMPLING")
                self.assertIsNone(result["ci_low"])
                self.assertIsNone(result["ci_high"])
                self.assertIsNone(result["raw_two_sided_p_value_centered_bootstrap"])
                self.assertEqual(result["bootstrap_unique_estimates"], 1)

    def test_single_admissible_block_is_non_identifiable(self):
        # n == block_length leaves exactly one admissible moving-block start.
        result = stats.paired_moving_block_bootstrap([[0.01, 0.02, 0.03, 0.04, 0.05]], block_length=5, replicates=100, seed=9)
        self.assertAlmostEqual(result["observed_mean_improvement"], 0.03)
        self.assertEqual(result["inferential_status"], "NON_IDENTIFIABLE_DEGENERATE_RESAMPLING")
        self.assertIsNone(result["ci_low"])
        self.assertIsNone(result["ci_high"])
        self.assertIsNone(result["raw_two_sided_p_value_centered_bootstrap"])

        with self.assertRaises(ValueError):
            stats.paired_moving_block_bootstrap([[0.1] * 4], block_length=5)

    def test_by_adjustment_matches_known_family_and_keeps_input_ids(self):
        p = {"A": 0.001, "B": 0.01, "C": 0.04, "D": 0.2}
        result = stats.benjamini_yekutieli(p, q=0.05)
        self.assertEqual(set(result), set(p))
        self.assertTrue(result["A"]["reject_at_q"])
        self.assertTrue(result["B"]["reject_at_q"])
        self.assertFalse(result["C"]["reject_at_q"])
        self.assertFalse(result["D"]["reject_at_q"])
        adjusted = [result[key]["by_adjusted_p_value"] for key in ["A", "B", "C", "D"]]
        self.assertEqual(adjusted, sorted(adjusted))
        self.assertAlmostEqual(adjusted[0], 0.008333333333333333)
        self.assertAlmostEqual(adjusted[1], 0.041666666666666664)
        self.assertAlmostEqual(adjusted[2], 0.1111111111111111)
        self.assertAlmostEqual(adjusted[3], 0.4166666666666667)

    def test_bootstrap_requires_integer_parameters(self):
        folds = [[0.01, 0.02, 0.03, 0.04, 0.05]]
        for kwargs in ({"block_length": 2.5}, {"replicates": 10.5}, {"seed": 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                stats.paired_moving_block_bootstrap(folds, **kwargs)

    def test_by_invalid_values_and_empty_family(self):
        self.assertEqual(stats.benjamini_yekutieli({}), {})
        with self.assertRaises(ValueError):
            stats.benjamini_yekutieli({"A": -0.1})
        with self.assertRaises(ValueError):
            stats.benjamini_yekutieli({"A": 0.1}, q=1.0)


if __name__ == "__main__":
    unittest.main()
