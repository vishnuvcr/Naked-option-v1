"""Synthetic-only tests for the additive spline logistic adapter."""
import unittest
import numpy as np
from prediction_gam_adapter_r3 import GeneralizedAdditiveProbabilityAdapter, GAMContractError

class GAMAdapterTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(213)
        self.x=rng.normal(size=(300,4))
        latent=1.2*np.sin(self.x[:,0])-.5*self.x[:,1]
        p=1/(1+np.exp(-latent))
        self.y=(rng.random(300)<p).astype(int)
        self.train=np.arange(220); self.test=np.arange(220,300)

    def test_probability_contract_and_training_only_spline_knots(self):
        m=GeneralizedAdditiveProbabilityAdapter(max_splines=5).fit(self.x[self.train],self.y[self.train])
        p=m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape,(80,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        np.testing.assert_allclose(m.model.named_steps["scale"].mean_,self.x[self.train].mean(axis=0))
        self.assertEqual(m.model.named_steps["splines"].n_knots,5)

    def test_flexible_knot_count(self):
        self.assertEqual(GeneralizedAdditiveProbabilityAdapter(max_splines=10).fit(self.x[self.train],self.y[self.train]).predict_proba(self.x[self.test]).shape,(80,))

    def test_reject_bad_knots_class_support_and_unfitted(self):
        with self.assertRaisesRegex(GAMContractError,"MAX_SPLINES"):
            GeneralizedAdditiveProbabilityAdapter(max_splines=1).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(GAMContractError,"BOTH_CLASSES"):
            GeneralizedAdditiveProbabilityAdapter().fit(self.x[:40],np.zeros(40))
        with self.assertRaisesRegex(GAMContractError,"MODEL_NOT_FIT"):
            GeneralizedAdditiveProbabilityAdapter().predict_proba(self.x[:2])

if __name__=="__main__": unittest.main()
