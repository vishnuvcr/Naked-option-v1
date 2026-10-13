"""Synthetic-only LDA/QDA adapter tests."""
import unittest
import numpy as np
from prediction_discriminant_adapters_r3 import LDAProbabilityAdapter, QDAProbabilityAdapter, DiscriminantContractError

class DiscriminantAdapterTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(810)
        self.x=rng.normal(size=(320,4))
        p=1/(1+np.exp(-(.9*self.x[:,0]-.5*self.x[:,1]+.2)))
        self.y=(rng.random(320)<p).astype(int)
        self.train=np.arange(240); self.test=np.arange(240,320)

    def assert_probability_contract(self,m):
        p=m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape,(80,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())

    def test_lda_probability_and_train_only_scaling(self):
        m=LDAProbabilityAdapter(shrinkage=.1).fit(self.x[self.train],self.y[self.train])
        self.assert_probability_contract(m)
        np.testing.assert_allclose(m.model.named_steps["scale"].mean_,self.x[self.train].mean(axis=0))
        self.assertFalse(np.allclose(m.model.named_steps["scale"].mean_,self.x.mean(axis=0)))

    def test_lda_auto_shrinkage(self):
        self.assert_probability_contract(LDAProbabilityAdapter(shrinkage="auto").fit(self.x[self.train],self.y[self.train]))

    def test_qda_probability_contract(self):
        self.assert_probability_contract(QDAProbabilityAdapter(reg_param=.1).fit(self.x[self.train],self.y[self.train]))

    def test_reject_bad_parameters_and_single_class(self):
        with self.assertRaisesRegex(DiscriminantContractError,"SHRINKAGE"):
            LDAProbabilityAdapter(shrinkage=2).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(DiscriminantContractError,"REG_PARAM"):
            QDAProbabilityAdapter(reg_param=-.1).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(DiscriminantContractError,"BOTH_CLASSES"):
            QDAProbabilityAdapter().fit(self.x[:40],np.zeros(40))

    def test_reject_prediction_before_fit_and_nonfinite_features(self):
        with self.assertRaisesRegex(DiscriminantContractError,"MODEL_NOT_FIT"):
            LDAProbabilityAdapter().predict_proba(self.x[:3])
        m=QDAProbabilityAdapter().fit(self.x[self.train],self.y[self.train])
        bad=self.x[:3].copy(); bad[0,0]=np.nan
        with self.assertRaisesRegex(DiscriminantContractError,"NONFINITE"):
            m.predict_proba(bad)

if __name__=="__main__": unittest.main()
