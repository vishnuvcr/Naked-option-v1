"""Synthetic-only tests for Markov-switching logistic adapter."""
import unittest
import numpy as np
from prediction_markov_switching_logit_r3 import MarkovSwitchingLogitAdapter,MarkovSwitchingLogitContractError
class MarkovSwitchingTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(812)
        n=240; regime=np.zeros(n,dtype=int)
        for i in range(1,n): regime[i]=regime[i-1] if rng.random()<.95 else 1-regime[i-1]
        self.x=np.column_stack([rng.normal(np.where(regime==0,-1,1),.7),rng.normal(size=n)])
        self.y=(regime ^ (rng.random(n)<.2)).astype(int)
    def test_fit_predict_contract(self):
        m=MarkovSwitchingLogitAdapter(max_iter=12).fit(self.x[:180],self.y[:180])
        p=m.predict_proba(self.x[180:])
        self.assertEqual(p.shape,(60,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        np.testing.assert_allclose(m.transition_.sum(1),np.ones(2),atol=1e-8)
        np.testing.assert_allclose(m.last_state_posterior_.sum(),1.0,atol=1e-8)
    def test_fail_closed(self):
        with self.assertRaisesRegex(MarkovSwitchingLogitContractError,"BOTH_CLASSES"):
            MarkovSwitchingLogitAdapter().fit(self.x[:60],np.zeros(60))
        with self.assertRaisesRegex(MarkovSwitchingLogitContractError,"MODEL_NOT_FIT"):
            MarkovSwitchingLogitAdapter().predict_proba(self.x[:2])
        bad=self.x[:60].copy(); bad[0,0]=np.nan
        with self.assertRaisesRegex(MarkovSwitchingLogitContractError,"NONFINITE"):
            MarkovSwitchingLogitAdapter().fit(bad,self.y[:60])
if __name__=="__main__": unittest.main()
