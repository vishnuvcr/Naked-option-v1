"""Synthetic-only contract tests for LDA/QDA adapters."""
import unittest
import numpy as np
from prediction_discriminant_adapter_r3 import DiscriminantContractError, DiscriminantProbabilityAdapter

class DiscriminantAdapterTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(20261014)
        self.x=rng.normal(size=(320,5))
        p=1/(1+np.exp(-(.9*self.x[:,0]-.5*self.x[:,1]+.2*self.x[:,2])))
        self.y=(rng.random(320)<p).astype(int)
        self.train=np.arange(240); self.test=np.arange(240,320)

    def test_lda_probability_contract(self):
        m=DiscriminantProbabilityAdapter(kind="lda",shrinkage="auto").fit(self.x[self.train],self.y[self.train])
        p=m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape,(80,)); self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        np.testing.assert_array_equal(m.predict_class(self.x[self.test]),(p>=.5).astype(int))

    def test_qda_probability_contract(self):
        m=DiscriminantProbabilityAdapter(kind="qda",reg_param=.2).fit(self.x[self.train],self.y[self.train])
        p=m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape,(80,)); self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())

    def test_train_only_scaling_and_invalid_inputs(self):
        m=DiscriminantProbabilityAdapter(kind="lda").fit(self.x[self.train],self.y[self.train])
        np.testing.assert_allclose(m.scaler_.mean_,self.x[self.train].mean(axis=0))
        with self.assertRaisesRegex(DiscriminantContractError,"BOTH_CLASSES"):
            DiscriminantProbabilityAdapter().fit(self.x[:40],np.zeros(40))
        with self.assertRaisesRegex(DiscriminantContractError,"SHRINKAGE"):
            DiscriminantProbabilityAdapter(kind="lda",shrinkage=2).fit(self.x[self.train],self.y[self.train])

    def test_reject_before_fit_and_nonfinite_prediction(self):
        with self.assertRaisesRegex(DiscriminantContractError,"MODEL_NOT_FIT"):
            DiscriminantProbabilityAdapter().predict_proba(self.x[:2])
        m=DiscriminantProbabilityAdapter(kind="qda").fit(self.x[self.train],self.y[self.train])
        bad=self.x[:2].copy(); bad[0,0]=np.nan
        with self.assertRaisesRegex(DiscriminantContractError,"NONFINITE"):
            m.predict_proba(bad)

if __name__=="__main__": unittest.main()
