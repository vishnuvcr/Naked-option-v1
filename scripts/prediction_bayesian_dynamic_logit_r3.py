"""Dynamic Bayesian logistic regression via sequential Laplace/EKF-style updates.

Coefficients evolve as a Gaussian random walk; each training label updates the current
Gaussian approximation. Prediction propagates the state without observing test labels.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
class BayesianDynamicLogitContractError(ValueError): pass

@dataclass
class BayesianDynamicLogitAdapter:
    process_variance:float=0.01
    prior_variance:float=4.0
    observation_ridge:float=1e-6
    mean_:np.ndarray|None=None
    scale_:np.ndarray|None=None
    beta_:np.ndarray|None=None
    covariance_:np.ndarray|None=None
    feature_count_:int|None=None

    def fit(self,x_train,y_train):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<30 or x.shape[1]<1: raise BayesianDynamicLogitContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise BayesianDynamicLogitContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}): raise BayesianDynamicLogitContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise BayesianDynamicLogitContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if not np.isfinite(self.process_variance) or self.process_variance<0 or not np.isfinite(self.prior_variance) or self.prior_variance<=0 or self.observation_ridge<=0: raise BayesianDynamicLogitContractError("BAYESIAN_PARAMETER_INVALID")
        self.mean_=x.mean(0); self.scale_=x.std(0); self.scale_[self.scale_==0]=1
        z=(x-self.mean_)/self.scale_; n,d=z.shape
        beta=np.zeros(d+1); cov=np.eye(d+1)*self.prior_variance
        for i in range(n):
            cov=cov+np.eye(d+1)*self.process_variance
            v=np.r_[1.0,z[i]]
            p=float(np.clip(expit(v@beta),1e-6,1-1e-6))
            innovation=float(y[i]-p)
            r=max(p*(1-p),self.observation_ridge)
            s=float(v@cov@v+r)
            gain=(cov@v)/s
            beta=beta+gain*innovation
            # Symmetric covariance update with Joseph-like stabilization.
            ident=np.eye(d+1)-np.outer(gain,v)
            cov=ident@cov@ident.T+np.outer(gain,gain)*r
            cov=(cov+cov.T)/2
            eigmin=float(np.linalg.eigvalsh(cov).min())
            if eigmin<1e-10: cov+=np.eye(d+1)*(1e-10-eigmin)
        self.beta_=beta; self.covariance_=cov; self.feature_count_=d
        return self

    def predict_proba(self,x_test):
        if self.beta_ is None: raise BayesianDynamicLogitContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.feature_count_: raise BayesianDynamicLogitContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise BayesianDynamicLogitContractError("PREDICTION_FEATURES_NONFINITE")
        z=(x-self.mean_)/self.scale_; out=[]; cov=self.covariance_.copy()
        for row in z:
            cov=cov+np.eye(len(self.beta_))*self.process_variance
            v=np.r_[1.0,row]; mu=float(v@self.beta_); var=max(float(v@cov@v),0)
            # Logistic-normal moment approximation.
            out.append(float(expit(mu/np.sqrt(1+np.pi*var/8))))
        p=np.asarray(out)
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise BayesianDynamicLogitContractError("PREDICTION_PROBABILITY_INVALID")
        return p
