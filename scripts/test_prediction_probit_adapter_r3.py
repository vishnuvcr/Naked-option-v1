"""Synthetic-only tests for the probit adapter."""
import unittest
import numpy as np
from prediction_probit_adapter_r3 import ProbitContractError, ProbitProbabilityAdapter

class ProbitAdapterTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(20261013)
        self.x=rng.normal(size=(300,4))
        p=1/(1+np.exp(-(.8*self.x[:,0]-.4*self.x[:,1])))
        self.y=(rng.random(300)<p).astype(int)
        self.train=np.arange(220); self.test=np.arange(220,300)

    def test_probit_objective_gradient_matches_central_finite_difference(self):
        rng=np.random.default_rng(17)
        z=rng.normal(size=(35,3))
        signed=np.where(rng.integers(0,2,size=35)==1,1.0,-1.0)
        theta=rng.normal(size=4)*0.2
        penalty=0.7
        _,analytic=ProbitProbabilityAdapter._objective_and_gradient(theta,z,signed,penalty)
        numeric=np.zeros_like(theta)
        eps=1e-6
        for i in range(len(theta)):
            plus=theta.copy(); minus=theta.copy()
            plus[i]+=eps; minus[i]-=eps
            fp=ProbitProbabilityAdapter._objective_and_gradient(plus,z,signed,penalty)[0]
            fm=ProbitProbabilityAdapter._objective_and_gradient(minus,z,signed,penalty)[0]
            numeric[i]=(fp-fm)/(2*eps)
        np.testing.assert_allclose(analytic,numeric,rtol=2e-5,atol=2e-5)

    def test_fit_predict_probability_contract(self):
        m=ProbitProbabilityAdapter(prior_scale=1.0).fit(self.x[self.train],self.y[self.train])
        p=m.predict_proba(self.x[self.test])
        self.assertTrue(m.converged_)
        self.assertEqual(p.shape,(80,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        np.testing.assert_array_equal(m.predict_class(self.x[self.test]),(p>=.5).astype(int))

    def test_standardization_uses_training_only(self):
        m=ProbitProbabilityAdapter().fit(self.x[self.train],self.y[self.train])
        np.testing.assert_allclose(m.mean_,self.x[self.train].mean(axis=0))
        self.assertFalse(np.allclose(m.mean_,self.x.mean(axis=0)))

    def test_reject_invalid_or_single_class_training(self):
        with self.assertRaisesRegex(ProbitContractError,"BOTH_CLASSES"):
            ProbitProbabilityAdapter().fit(self.x[:40],np.zeros(40))
        with self.assertRaisesRegex(ProbitContractError,"NONFINITE"):
            ProbitProbabilityAdapter().fit(np.where(np.indices((30,2))[0]==0,np.nan,1),np.array([0,1]*15))
        with self.assertRaisesRegex(ProbitContractError,"PRIOR_SCALE"):
            ProbitProbabilityAdapter(prior_scale=0).fit(self.x[self.train],self.y[self.train])

    def test_reject_prediction_before_fit_and_nonfinite(self):
        with self.assertRaisesRegex(ProbitContractError,"MODEL_NOT_FIT"):
            ProbitProbabilityAdapter().predict_proba(self.x[:2])
        m=ProbitProbabilityAdapter().fit(self.x[self.train],self.y[self.train])
        bad=self.x[:2].copy(); bad[0,0]=np.inf
        with self.assertRaisesRegex(ProbitContractError,"NONFINITE"):
            m.predict_proba(bad)

if __name__=="__main__": unittest.main()
