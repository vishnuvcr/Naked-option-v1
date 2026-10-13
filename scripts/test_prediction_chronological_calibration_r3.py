"""Synthetic-only calibration tests; no market data, fold generation or holdout."""
import unittest
import numpy as np

from prediction_chronological_calibration_r3 import ChronologicalOOFPlattCalibrator
from prediction_logistic_adapter_r3 import AdapterContractError


class ChronologicalCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.t = np.arange(40)
        self.y = np.array([0, 1] * 20)
        self.p = np.where(self.y == 1, .62, .38)

    def test_fit_and_predict_probability_contract(self):
        c = ChronologicalOOFPlattCalibrator().fit(self.p, self.y, self.t)
        out = c.predict([.2, .5, .8])
        self.assertEqual(out.shape, (3,))
        self.assertTrue(np.isfinite(out).all())
        self.assertTrue(((out >= 0) & (out <= 1)).all())
        self.assertEqual(c.fitted_start, "0")
        self.assertEqual(c.fitted_end, "39")

    def test_reject_nonchronological_or_duplicate_timestamps(self):
        with self.assertRaisesRegex(AdapterContractError, "NOT_STRICTLY_CHRONOLOGICAL"):
            ChronologicalOOFPlattCalibrator().fit(self.p, self.y, self.t[::-1])
        with self.assertRaisesRegex(AdapterContractError, "DUPLICATED"):
            ChronologicalOOFPlattCalibrator().fit(self.p, self.y, np.r_[self.t[:-1], self.t[-2]])

    def test_reject_bad_probabilities_and_small_samples(self):
        with self.assertRaisesRegex(AdapterContractError, "STRICTLY_INTERIOR"):
            ChronologicalOOFPlattCalibrator().fit(np.r_[self.p[:-1], 1.0], self.y, self.t)
        with self.assertRaisesRegex(AdapterContractError, "SHAPE_OR_SIZE"):
            ChronologicalOOFPlattCalibrator().fit(self.p[:10], self.y[:10], self.t[:10])

    def test_reject_single_class_labels_and_unfitted_prediction(self):
        with self.assertRaisesRegex(AdapterContractError, "BOTH_CLASSES"):
            ChronologicalOOFPlattCalibrator().fit(self.p, np.zeros(40), self.t)
        with self.assertRaisesRegex(AdapterContractError, "NOT_FIT"):
            ChronologicalOOFPlattCalibrator().predict([.4, .6])


if __name__ == "__main__":
    unittest.main()
