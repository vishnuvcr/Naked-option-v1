"""Synthetic-only tests for Bayesian dynamic logistic adapter."""
import unittest
import numpy as np
from prediction_bayesian_dynamic_logit_r3 import BayesianDynamicLogitAdapter,BayesianDynamicLogitContractError
class BayesianDynamicLogitTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(91); self.x=rng.normal(size=(180,3))
        self.y=(rng.random(180)<1/(1+np.exp(-(.8*self.x[:,0]-.5*self.x[:,1])))).astype(int)
    def test_fit_predict_and_reproducible_calls(self):
        m=BayesianDynamicLogitAdapter().fit(self.x[:130],self.y[:130])
        p=m.predict_proba(self.x[130:]); p2=m.predict_proba(self.x[130:])
        self.assertEqual(p.shape,(50,)); self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all()); np.testing.assert_allclose(p,p2)
        self.assertTrue(np.all(np.linalg.eigvalsh(m.covariance_)>0))
    def test_fail_closed(self):
        with self.assertRaisesRegex(BayesianDynamicLogitContractError,"BOTH_CLASSES"):
            BayesianDynamicLogitAdapter().fit(self.x[:50],np.zeros(50))
        with self.assertRaisesRegex(BayesianDynamicLogitContractError,"MODEL_NOT_FIT"):
            BayesianDynamicLogitAdapter().predict_proba(self.x[:2])
        bad=self.x[:40].copy(); bad[0,0]=np.nan
        with self.assertRaisesRegex(BayesianDynamicLogitContractError,"NONFINITE"):
            BayesianDynamicLogitAdapter().fit(bad,self.y[:40])
if __name__=="__main__": unittest.main()
