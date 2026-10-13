"""Synthetic-only calibration tests; no market data, fold generation or holdout."""
import unittest
import numpy as np

from prediction_chronological_calibration_r3 import ChronologicalOOFPlattCalibrator, ChronologicalScorePlattCalibrator
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



class ChronologicalScoreCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.t=np.arange(60)
        self.y=np.array([0,1]*30)
        self.s=np.where(self.y==1,1.2,-.8)+np.linspace(-.2,.2,60)

    def test_raw_score_calibration_emits_valid_probabilities(self):
        c=ChronologicalScorePlattCalibrator().fit(self.s,self.y,self.t)
        p=c.predict([-2.0,0.0,2.0])
        self.assertEqual(p.shape,(3,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        self.assertGreater(p[-1],p[0])

    def test_reject_nonchronological_scores_and_invalid_values(self):
        with self.assertRaisesRegex(AdapterContractError,"NOT_STRICTLY_CHRONOLOGICAL"):
            ChronologicalScorePlattCalibrator().fit(self.s,self.y,self.t[::-1])
        with self.assertRaisesRegex(AdapterContractError,"NONFINITE"):
            ChronologicalScorePlattCalibrator().fit(np.r_[self.s[:-1],np.nan],self.y,self.t)
        with self.assertRaisesRegex(AdapterContractError,"BOTH_CLASSES"):
            ChronologicalScorePlattCalibrator().fit(self.s,np.zeros(60),self.t)
        with self.assertRaisesRegex(AdapterContractError,"NOT_FIT"):
            ChronologicalScorePlattCalibrator().predict([0.0])

if __name__ == "__main__":
    unittest.main()
