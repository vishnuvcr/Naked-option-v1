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
        endpoints=sessions + 1
        folds=chronological_inner_oof(lambda: LogisticProbabilityAdapter(),
             x,y,sessions,purge_sessions=2,min_train_rows=50,min_validation_rows=50,
             target_endpoint_session_positions=endpoints, embargo_sessions=1)
        self.assertEqual([f["fold"] for f in folds],[1,2,3])
        for f in folds:
            first_valid=f["validation_start_session"]
            self.assertLess(sessions[f["train_indices"]].max(), first_valid-2)
            self.assertTrue(np.all(endpoints[f["train_indices"]] < first_valid))
            self.assertGreaterEqual(sessions[f["validation_indices"]].min(), first_valid+1)
            self.assertTrue(np.all(endpoints[f["validation_indices"]] < f["validation_end_session_exclusive"]))
            self.assertLess(f["training_target_maturity_max_session"], first_valid)
        self.assertTrue(np.isfinite(oof_log_loss(folds)))

    def test_oof_requires_target_endpoint_positions(self):
        x=np.arange(600,dtype=float).reshape(200,3)
        y=np.tile([0,1],100)
        sessions=np.repeat(np.arange(20),10)
        with self.assertRaisesRegex(CalibrationContractError,"TARGET_ENDPOINT_SESSION_POSITIONS_REQUIRED"):
            chronological_inner_oof(lambda: LogisticProbabilityAdapter(),x,y,sessions,
                purge_sessions=1,min_train_rows=10,min_validation_rows=10)

    def test_oof_rejects_target_endpoint_before_decision(self):
        x=np.random.default_rng(9).normal(size=(200,3))
        y=np.tile([0,1],100)
        sessions=np.repeat(np.arange(20),10)
        endpoints=sessions.copy()
        endpoints[10]=sessions[10]-1
        with self.assertRaisesRegex(CalibrationContractError,"TARGET_ENDPOINT_PRECEDES_DECISION"):
            chronological_inner_oof(lambda: LogisticProbabilityAdapter(),x,y,sessions,
                purge_sessions=1,min_train_rows=10,min_validation_rows=10,
                target_endpoint_session_positions=endpoints)

    def test_bad_calibration_inputs_fail_closed(self):
        with self.assertRaisesRegex(CalibrationContractError,"SHAPE_OR_SAMPLE"):
            PlattCalibrator().fit([.2,.8],[0,1])
        with self.assertRaisesRegex(CalibrationContractError,"PROBABILITIES_INVALID"):
            PlattCalibrator().fit([.2,np.nan]*10,[0,1]*10)

if __name__=="__main__":
    unittest.main()
