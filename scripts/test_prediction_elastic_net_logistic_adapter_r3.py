"""Synthetic-only elastic-net logistic adapter tests."""
import unittest
import numpy as np
from prediction_elastic_net_logistic_adapter_r3 import ElasticNetLogisticContractError, ElasticNetLogisticProbabilityAdapter

class ElasticNetLogisticTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(510)
        self.x=rng.normal(size=(300,5))
        p=1/(1+np.exp(-(.8*self.x[:,0]-.4*self.x[:,1]+.2)))
        self.y=(rng.random(300)<p).astype(int)
        self.train=np.arange(220); self.test=np.arange(220,300)

    def test_probability_contract_and_train_only_scaling(self):
        m=ElasticNetLogisticProbabilityAdapter(c=.5,l1_ratio=.75).fit(self.x[self.train],self.y[self.train])
        p=m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape,(80,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        np.testing.assert_allclose(m.model.named_steps["scale"].mean_,self.x[self.train].mean(axis=0))
        self.assertFalse(np.allclose(m.model.named_steps["scale"].mean_,self.x.mean(axis=0)))

    def test_extreme_ratios_and_invalid_parameters(self):
        for ratio in (0.0,1.0):
            self.assertEqual(ElasticNetLogisticProbabilityAdapter(l1_ratio=ratio).fit(self.x[self.train],self.y[self.train]).predict_proba(self.x[self.test]).shape,(80,))
        with self.assertRaisesRegex(ElasticNetLogisticContractError,"L1_RATIO"):
            ElasticNetLogisticProbabilityAdapter(l1_ratio=1.2).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(ElasticNetLogisticContractError,"C_MUST"):
            ElasticNetLogisticProbabilityAdapter(c=0).fit(self.x[self.train],self.y[self.train])

    def test_fail_closed_for_bad_labels_features_and_unfitted(self):
        with self.assertRaisesRegex(ElasticNetLogisticContractError,"BOTH_CLASSES"):
            ElasticNetLogisticProbabilityAdapter().fit(self.x[:30],np.zeros(30))
        with self.assertRaisesRegex(ElasticNetLogisticContractError,"NONFINITE"):
            ElasticNetLogisticProbabilityAdapter().fit(np.where(np.indices((30,2))[0]==0,np.nan,1),np.array([0,1]*15))
        with self.assertRaisesRegex(ElasticNetLogisticContractError,"MODEL_NOT_FIT"):
            ElasticNetLogisticProbabilityAdapter().predict_proba(self.x[:2])

if __name__=="__main__": unittest.main()
