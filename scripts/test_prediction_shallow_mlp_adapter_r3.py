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

    def test_mlp_backprop_gradients_match_finite_differences(self):
        rng=np.random.default_rng(13)
        xb=rng.normal(size=(9,2)); yb=np.array([0,1,0,1,1,0,1,0,1],dtype=float)
        w1=rng.normal(size=(2,3))*.2; b1=rng.normal(size=3)*.1
        w2=rng.normal(size=3)*.2; b2=.1; mask=np.ones((9,3)); wd=.15
        _,grads=ShallowMLPProbabilityAdapter._batch_loss_and_grad(xb,yb,w1,b1,w2,b2,mask,wd)
        params=[w1.copy(),b1.copy(),w2.copy(),np.array([b2])]
        analytic=[grads[0],grads[1],grads[2],np.array([grads[3]])]
        eps=1e-6
        for pi,param in enumerate(params):
            for idx in np.ndindex(param.shape):
                plus=[p.copy() for p in params]; minus=[p.copy() for p in params]
                plus[pi][idx]+=eps; minus[pi][idx]-=eps
                fp=ShallowMLPProbabilityAdapter._batch_loss_and_grad(xb,yb,plus[0],plus[1],plus[2],float(plus[3][0]),mask,wd)[0]
                fm=ShallowMLPProbabilityAdapter._batch_loss_and_grad(xb,yb,minus[0],minus[1],minus[2],float(minus[3][0]),mask,wd)[0]
                numeric=(fp-fm)/(2*eps)
                self.assertAlmostEqual(float(analytic[pi][idx]),float(numeric),places=5)

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
