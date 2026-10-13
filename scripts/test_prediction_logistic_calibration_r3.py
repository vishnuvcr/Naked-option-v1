"""Synthetic-only tests for chronological OOF calibration utilities."""
import unittest
import numpy as np
from sklearn.linear_model import LogisticRegression
from prediction_logistic_adapter_r3 import LogisticProbabilityAdapter
from prediction_logistic_calibration_r3 import (
    CalibrationContractError, PlattCalibrator, chronological_inner_oof, oof_log_loss,
)


class CalibrationTests(unittest.TestCase):
    def test_platt_calibration_fit_and_predict(self):
        rng=np.random.default_rng(73)
        raw=np.linspace(.05,.95,120)
        y=(rng.random(120)<raw).astype(int)
        cal=PlattCalibrator().fit(raw,y)
        p=cal.predict([.2,.5,.8])
        self.assertEqual(len(p),3)
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())

    def test_chronological_oof_has_strictly_prior_training_and_purge(self):
        rng=np.random.default_rng(12)
        x=rng.normal(size=(600,3))
        y=(x[:,0] + .3*x[:,1] > 0).astype(int)
        sessions=np.repeat(np.arange(60),10)
        folds=chronological_inner_oof(lambda: LogisticProbabilityAdapter(),
             x,y,sessions,purge_sessions=2,min_train_rows=50,min_validation_rows=50)
        self.assertEqual([f["fold"] for f in folds],[1,2,3])
        for f in folds:
            self.assertLess(sessions[f["train_indices"]].max(),
                            sessions[f["validation_indices"]].min()-2)
        self.assertTrue(np.isfinite(oof_log_loss(folds)))

    def test_chronological_oof_accepts_two_column_binary_probabilities(self):
        class TwoColumnAdapter:
            def fit(self, x_train, y_train):
                self.base = LogisticProbabilityAdapter().fit(x_train, y_train)
                return self
            def predict_proba(self, x_test):
                positive = self.base.predict_proba(x_test)
                return np.column_stack([1.0 - positive, positive])

        rng = np.random.default_rng(18)
        x = rng.normal(size=(600, 3))
        y = (x[:, 0] + 0.3 * x[:, 1] > 0).astype(int)
        sessions = np.repeat(np.arange(60), 10)
        folds = chronological_inner_oof(lambda: TwoColumnAdapter(), x, y, sessions,
             purge_sessions=2, min_train_rows=50, min_validation_rows=50)
        self.assertEqual(len(folds), 3)
        for fold in folds:
            self.assertEqual(fold["probabilities"].ndim, 1)
            self.assertEqual(len(fold["probabilities"]), len(fold["labels"]))

    def test_oof_accepts_two_column_predict_proba(self):
        class Wrapper:
            def fit(self, x, y):
                self.base = LogisticProbabilityAdapter().fit(x, y)
                return self
            def predict_proba(self, x):
                p = self.base.predict_proba(x)
                return np.column_stack((1.0-p, p))
        rng=np.random.default_rng(18)
        x=rng.normal(size=(600,3)); y=(x[:,0]+.3*x[:,1]>0).astype(int)
        sessions=np.repeat(np.arange(60),10)
        folds=chronological_inner_oof(lambda: Wrapper(),x,y,sessions,2,50,50)
        self.assertEqual(len(folds),3)
        for fold in folds:
            self.assertEqual(fold["probabilities"].ndim,1)
            self.assertEqual(len(fold["probabilities"]),len(fold["labels"]))

    def test_bad_calibration_inputs_fail_closed(self):
        with self.assertRaisesRegex(CalibrationContractError,"SHAPE_OR_SAMPLE"):
            PlattCalibrator().fit([.2,.8],[0,1])
        with self.assertRaisesRegex(CalibrationContractError,"PROBABILITIES_INVALID"):
            PlattCalibrator().fit([.2,np.nan]*10,[0,1]*10)

if __name__=="__main__":
    unittest.main()
