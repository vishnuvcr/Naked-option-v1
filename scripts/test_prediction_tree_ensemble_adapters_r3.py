"""Synthetic-only tree ensemble probability adapter tests."""
import unittest
import numpy as np
from prediction_tree_ensemble_adapters_r3 import (
    RandomForestProbabilityAdapter, ExtraTreesProbabilityAdapter,
    GradientBoostingProbabilityAdapter, HistGradientBoostingProbabilityAdapter,
    TreeAdapterContractError,
)

class TreeAdapterTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(911)
        self.x=rng.normal(size=(240,4))
        p=1/(1+np.exp(-(.9*self.x[:,0]-.5*self.x[:,1])))
        self.y=(rng.random(240)<p).astype(int)
        self.train=np.arange(180); self.test=np.arange(180,240)

    def assert_probabilities(self,m):
        p=m.predict_proba(self.x[self.test])
        self.assertEqual(p.shape,(60,))
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())

    def test_random_forest_and_extra_trees(self):
        self.assert_probabilities(RandomForestProbabilityAdapter(n_estimators=25,max_depth=4,min_samples_leaf=3).fit(self.x[self.train],self.y[self.train]))
        self.assert_probabilities(ExtraTreesProbabilityAdapter(n_estimators=25,max_depth=4,min_samples_leaf=3).fit(self.x[self.train],self.y[self.train]))

    def test_gradient_boosting_models(self):
        self.assert_probabilities(GradientBoostingProbabilityAdapter(n_estimators=20,max_depth=2,learning_rate=.05).fit(self.x[self.train],self.y[self.train]))
        self.assert_probabilities(HistGradientBoostingProbabilityAdapter(max_iter=20,max_leaf_nodes=7,l2_regularization=.1).fit(self.x[self.train],self.y[self.train]))

    def test_deterministic_repeat(self):
        a=RandomForestProbabilityAdapter(n_estimators=20,random_state=4).fit(self.x[self.train],self.y[self.train]).predict_proba(self.x[self.test])
        b=RandomForestProbabilityAdapter(n_estimators=20,random_state=4).fit(self.x[self.train],self.y[self.train]).predict_proba(self.x[self.test])
        np.testing.assert_allclose(a,b,rtol=0,atol=0)

    def test_reject_bad_support_parameters_and_features(self):
        with self.assertRaisesRegex(TreeAdapterContractError,"BOTH_CLASSES"):
            RandomForestProbabilityAdapter().fit(self.x[:30],np.zeros(30))
        with self.assertRaisesRegex(TreeAdapterContractError,"TREE_PARAMETERS"):
            ExtraTreesProbabilityAdapter(n_estimators=0).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(TreeAdapterContractError,"MODEL_NOT_FIT"):
            HistGradientBoostingProbabilityAdapter().predict_proba(self.x[:2])
        m=GradientBoostingProbabilityAdapter(n_estimators=10).fit(self.x[self.train],self.y[self.train])
        bad=self.x[:2].copy(); bad[0,0]=np.nan
        with self.assertRaisesRegex(TreeAdapterContractError,"NONFINITE"):
            m.predict_proba(bad)

if __name__=="__main__": unittest.main()
