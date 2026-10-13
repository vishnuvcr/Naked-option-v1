"""Synthetic-only tests for margin/distance score adapters."""
import unittest
import numpy as np
from prediction_margin_distance_adapters_r3 import (
    KernelSVMScoreAdapter, NearestCentroidScoreAdapter, KNNDensityRatioScoreAdapter,
    MarginAdapterContractError,
)

class MarginDistanceTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(912)
        self.x=rng.normal(size=(280,4))
        p=1/(1+np.exp(-(.9*self.x[:,0]-.6*self.x[:,1])))
        self.y=(rng.random(280)<p).astype(int)
        self.train=np.arange(210); self.test=np.arange(210,280)

    def assert_scores(self,m):
        scores=m.predict_score(self.x[self.test])
        self.assertEqual(scores.shape,(70,))
        self.assertTrue(np.isfinite(scores).all())
        return scores

    def test_svm_returns_raw_decision_scores_not_internal_cv_probabilities(self):
        m=KernelSVMScoreAdapter(c=1,kernel="rbf",gamma="scale").fit(self.x[self.train],self.y[self.train])
        self.assert_scores(m)
        self.assertFalse(m.model.named_steps["svm"].probability)

    def test_centroid_and_knn_scores(self):
        self.assert_scores(NearestCentroidScoreAdapter(shrink_threshold=.1).fit(self.x[self.train],self.y[self.train]))
        self.assert_scores(KNNDensityRatioScoreAdapter(n_neighbors=15,weights="distance").fit(self.x[self.train],self.y[self.train]))

    def test_invalid_parameters_and_support(self):
        with self.assertRaisesRegex(MarginAdapterContractError,"SVM_KERNEL"):
            KernelSVMScoreAdapter(kernel="bad").fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(MarginAdapterContractError,"CENTROID_SHRINK"):
            NearestCentroidScoreAdapter(shrink_threshold=-1).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(MarginAdapterContractError,"KNN_NEIGHBORS"):
            KNNDensityRatioScoreAdapter(n_neighbors=999).fit(self.x[self.train],self.y[self.train])
        with self.assertRaisesRegex(MarginAdapterContractError,"BOTH_CLASSES"):
            KernelSVMScoreAdapter().fit(self.x[:30],np.zeros(30))

    def test_fail_closed_for_unfitted_and_nonfinite_features(self):
        with self.assertRaisesRegex(MarginAdapterContractError,"MODEL_NOT_FIT"):
            KernelSVMScoreAdapter().predict_score(self.x[:2])
        m=NearestCentroidScoreAdapter().fit(self.x[self.train],self.y[self.train])
        bad=self.x[:2].copy(); bad[0,0]=np.nan
        with self.assertRaisesRegex(MarginAdapterContractError,"NONFINITE"):
            m.predict_score(bad)

if __name__=="__main__": unittest.main()
