"""Synthetic-only tests for the trainable temporal convolution adapter."""
import unittest
import numpy as np
from prediction_temporal_convolution_adapter_r3 import TemporalConvolutionAdapter,TemporalConvContractError
class TemporalConvTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(2026); n=180; seq=8; feat=2
        self.x=rng.normal(size=(n,seq,feat))
        signal=self.x[:,-3:,0].mean(axis=1)+.3*self.x[:,-1,1]
        self.y=(signal>np.median(signal)).astype(int)
    def test_fit_predict_and_training_loss(self):
        m=TemporalConvolutionAdapter(channels=4,kernel_size=3,epochs=40,random_state=7).fit(self.x[:130],self.y[:130])
        p=m.predict_proba(self.x[130:])
        self.assertEqual(p.shape,(50,)); self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        self.assertLess(m.loss_history_[-1],m.loss_history_[0])
    def test_scaling_is_training_only_and_deterministic(self):
        a=TemporalConvolutionAdapter(channels=3,epochs=8,random_state=3).fit(self.x[:130],self.y[:130])
        b=TemporalConvolutionAdapter(channels=3,epochs=8,random_state=3).fit(self.x[:130],self.y[:130])
        np.testing.assert_allclose(a.mean_,self.x[:130].mean(axis=(0,1)))
        np.testing.assert_allclose(a.predict_proba(self.x[130:]),b.predict_proba(self.x[130:]))
    def test_dropout_is_validated_and_deterministic(self):
        a=TemporalConvolutionAdapter(channels=3,kernel_size=3,epochs=10,dropout=.2,random_state=9).fit(self.x[:130],self.y[:130])
        b=TemporalConvolutionAdapter(channels=3,kernel_size=3,epochs=10,dropout=.2,random_state=9).fit(self.x[:130],self.y[:130])
        np.testing.assert_allclose(a.predict_proba(self.x[130:]),b.predict_proba(self.x[130:]))
        with self.assertRaisesRegex(TemporalConvContractError,"MODEL_PARAMETER"):
            TemporalConvolutionAdapter(dropout=1.0).fit(self.x[:130],self.y[:130])

    def test_fail_closed(self):
        with self.assertRaisesRegex(TemporalConvContractError,"BOTH_CLASSES"):
            TemporalConvolutionAdapter().fit(self.x[:50],np.zeros(50))
        with self.assertRaisesRegex(TemporalConvContractError,"MODEL_NOT_FIT"):
            TemporalConvolutionAdapter().predict_proba(self.x[:2])
        bad=self.x[:50].copy(); bad[0,0,0]=np.nan
        with self.assertRaisesRegex(TemporalConvContractError,"NONFINITE"):
            TemporalConvolutionAdapter().fit(bad,self.y[:50])
if __name__=="__main__": unittest.main()
