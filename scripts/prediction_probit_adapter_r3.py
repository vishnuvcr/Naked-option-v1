"""Train-only standardized probit probability adapter; synthetic-testable, no data I/O."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from scipy.optimize import minimize
from scipy.special import log_ndtr, ndtr

class ProbitContractError(ValueError):
    pass

@dataclass
class ProbitProbabilityAdapter:
    prior_scale: float = 1.0
    max_iter: int = 2000
    mean_: np.ndarray | None = None
    scale_: np.ndarray | None = None
    coef_: np.ndarray | None = None
    intercept_: float | None = None
    converged_: bool = False

    def fit(self, x_train: Sequence[Sequence[float]], y_train: Sequence[int]):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<20 or x.shape[1]<1:
            raise ProbitContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise ProbitContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}):
            raise ProbitContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise ProbitContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if not np.isfinite(self.prior_scale) or self.prior_scale<=0: raise ProbitContractError("PRIOR_SCALE_MUST_BE_FINITE_POSITIVE")
        if isinstance(self.max_iter,bool) or not isinstance(self.max_iter,int) or self.max_iter<1: raise ProbitContractError("MAX_ITER_INVALID")
        self.mean_=x.mean(axis=0); self.scale_=x.std(axis=0); self.scale_[self.scale_==0]=1.0
        z=(x-self.mean_)/self.scale_; signed=np.where(y.astype(int)==1,1.0,-1.0)
        penalty=1.0/(float(self.prior_scale)**2)
        init=np.zeros(z.shape[1]+1)
        result=minimize(lambda theta: self._objective_and_gradient(theta,z,signed,penalty),init,jac=True,method="L-BFGS-B",options={"maxiter":self.max_iter,"ftol":1e-12})
        if not np.isfinite(result.fun) or not np.isfinite(result.x).all(): raise ProbitContractError("OPTIMIZER_RETURNED_NONFINITE")
        self.intercept_=float(result.x[0]); self.coef_=result.x[1:].copy(); self.converged_=bool(result.success)
        if not self.converged_: raise ProbitContractError("OPTIMIZER_DID_NOT_CONVERGE:"+str(result.message))
        return self

    @staticmethod
    def _objective_and_gradient(theta: np.ndarray, z: np.ndarray, signed: np.ndarray, penalty: float):
        eta=theta[0]+z@theta[1:]
        loss=-float(np.sum(log_ndtr(signed*eta)))+0.5*penalty*float(theta[1:]@theta[1:])
        log_ratio=-0.5*eta*eta-0.5*np.log(2*np.pi)-log_ndtr(signed*eta)
        grad_eta=-signed*np.exp(np.minimum(log_ratio,700))
        grad=np.empty_like(theta)
        grad[0]=grad_eta.sum()
        grad[1:]=z.T@grad_eta+penalty*theta[1:]
        return loss,grad

    def predict_proba(self,x_test: Sequence[Sequence[float]]) -> np.ndarray:
        if self.mean_ is None or self.scale_ is None or self.coef_ is None or self.intercept_ is None:
            raise ProbitContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=len(self.mean_): raise ProbitContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise ProbitContractError("PREDICTION_FEATURES_NONFINITE")
        p=ndtr(self.intercept_+((x-self.mean_)/self.scale_)@self.coef_)
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise ProbitContractError("PREDICTION_PROBABILITY_INVALID")
        return p

    def predict_class(self,x_test: Sequence[Sequence[float]]) -> np.ndarray:
        return (self.predict_proba(x_test)>=0.5).astype(int)
