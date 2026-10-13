"""Synthetic-only tests for causal change-point segment probability adapter."""
import unittest
import numpy as np
from prediction_change_point_adapter_r3 import ChangePointSegmentProbabilityAdapter,ChangePointContractError
class ChangePointTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(77)
        self.x=np.r_[rng.normal(-1,.4,(100,2)),rng.normal(1,.4,(100,2))]
        self.y=np.r_[np.zeros(100,dtype=int),np.ones(100,dtype=int)]
    def test_fit_predict_uses_last_training_regime(self):
        m=ChangePointSegmentProbabilityAdapter(min_segment=20,penalty=3.0).fit(self.x,self.y)
        p=m.predict_proba(np.ones((10,2)))
        self.assertEqual(p.shape,(10,)); self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        self.assertEqual(m.boundaries_[0],0); self.assertEqual(m.boundaries_[-1],len(self.x))
    def test_fail_closed(self):
        with self.assertRaisesRegex(ChangePointContractError,"BOTH_CLASSES"):
            ChangePointSegmentProbabilityAdapter(min_segment=20).fit(self.x[:50],np.zeros(50))
        with self.assertRaisesRegex(ChangePointContractError,"MODEL_NOT_FIT"):
            ChangePointSegmentProbabilityAdapter().predict_proba(self.x[:2])
        bad=self.x[:50].copy(); bad[0,0]=np.nan
        with self.assertRaisesRegex(ChangePointContractError,"NONFINITE"):
            ChangePointSegmentProbabilityAdapter(min_segment=20).fit(bad,self.y[:50])
if __name__=="__main__": unittest.main()
