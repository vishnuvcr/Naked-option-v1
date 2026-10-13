"""Synthetic-only shallow MLP tests."""
import unittest
import numpy as np
from prediction_shallow_mlp_adapter_r3 import ShallowMLPProbabilityAdapter, MLPContractError

class ShallowMLPTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(991)
        self.x=rng.normal(size=(180,4))
        p=1/(1+np.exp(-(.9*self.x[:,0]-.4*self.x[:,1])))
        self.y=(rng.random(180)<p).astype(int)
        self.train=np.arange(130); self.test=np.arange(130,180)

    def test_probability_contract_and_train_only_scaling(self):
        m=ShallowMLPProbabilityAdapter(hidden_units=16,dropout=.2,weight_decay=.001,epochs=30,random_state=9).fit(self.x[self.train],self.y[self.train])
        p=m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape,(50,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        np.testing.assert_allclose(m.mean_,self.x[self.train].mean(axis=0))
        self.assertFalse(np.allclose(m.mean_,self.x.mean(axis=0)))

    def test_deterministic_repeat(self):
        kwargs=dict(hidden_units=12,dropout=.2,weight_decay=.001,epochs=20,random_state=7)
        a=ShallowMLPProbabilityAdapter(**kwargs).fit(self.x[self.train],self.y[self.train]).predict_proba(self.x[self.test])
        b=ShallowMLPProbabilityAdapter(**kwargs).fit(self.x[self.train],self.y[self.train]).predict_proba(self.x[self.test])
        np.testing.assert_allclose(a,b,rtol=0,atol=0)

    def test_parameter_and_input_validation(self):
        with self.assertRaisesRegex(MLPContractError,"DROPOUT"):
            ShallowMLPProbabilityAdapter(dropout=.9).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(MLPContractError,"WEIGHT_DECAY"):
            ShallowMLPProbabilityAdapter(weight_decay=-1).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(MLPContractError,"BOTH_CLASSES"):
            ShallowMLPProbabilityAdapter().fit(self.x[:30],np.zeros(30))
        with self.assertRaisesRegex(MLPContractError,"MODEL_NOT_FIT"):
            ShallowMLPProbabilityAdapter().predict_proba(self.x[:2])

if __name__=="__main__": unittest.main()
