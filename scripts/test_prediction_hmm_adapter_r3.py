"""Synthetic-only tests for diagonal Gaussian HMM adapter."""
import unittest
import numpy as np
from prediction_hmm_adapter_r3 import GaussianHMMDirectionalAdapter,HMMContractError

class HMMTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(321)
        n=240
        regime=np.zeros(n,dtype=int)
        for i in range(1,n): regime[i]=regime[i-1] if rng.random()<.94 else 1-regime[i-1]
        self.x=np.column_stack([rng.normal(np.where(regime==0,-1,1),.55),rng.normal(size=n)])
        self.y=(regime ^ (rng.random(n)<.15)).astype(int)
    def test_fit_and_predict_probabilities(self):
        m=GaussianHMMDirectionalAdapter(n_states=2,max_iter=100,random_state=12).fit(self.x[:180],self.y[:180])
        p=m.predict_proba(self.x[180:])
        self.assertEqual(p.shape,(60,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        self.assertEqual(m.transition_.shape,(2,2))
        np.testing.assert_allclose(m.transition_.sum(1),np.ones(2),atol=1e-8)
        np.testing.assert_allclose(m.initial_.sum(),1.0,atol=1e-8)
    def test_reject_invalid_training(self):
        with self.assertRaisesRegex(HMMContractError,"BOTH_CLASSES"):
            GaussianHMMDirectionalAdapter().fit(self.x[:40],np.zeros(40))
        with self.assertRaisesRegex(HMMContractError,"NONFINITE"):
            bad=self.x[:40].copy(); bad[0,0]=np.nan
            GaussianHMMDirectionalAdapter().fit(bad,self.y[:40])
        with self.assertRaisesRegex(HMMContractError,"N_STATES"):
            GaussianHMMDirectionalAdapter(n_states=1).fit(self.x[:80],self.y[:80])
    def test_reject_prediction_before_fit_and_nonfinite(self):
        m=GaussianHMMDirectionalAdapter()
        with self.assertRaisesRegex(HMMContractError,"MODEL_NOT_FIT"): m.predict_proba(self.x[:2])
        m.fit(self.x[:180],self.y[:180])
        with self.assertRaisesRegex(HMMContractError,"NONFINITE"):
            bad=self.x[180:182].copy(); bad[0,0]=np.inf; m.predict_proba(bad)

if __name__=="__main__": unittest.main()
