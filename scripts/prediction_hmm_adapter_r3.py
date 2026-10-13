"""Diagonal-Gaussian HMM with smoothed state-conditional directional probabilities.

This estimator is for synthetic contract tests only. Caller owns chronological splitting,
feature engineering, and any calibration. No market-data or file I/O occurs here.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

class HMMContractError(ValueError):
    pass

def _logsumexp(a, axis=None):
    m=np.max(a,axis=axis,keepdims=True)
    out=m+np.log(np.sum(np.exp(a-m),axis=axis,keepdims=True))
    return np.squeeze(out,axis=axis) if axis is not None else float(out.squeeze())

@dataclass
class GaussianHMMDirectionalAdapter:
    n_states:int=2
    max_iter:int=100
    tol:float=1e-5
    random_state:int=42
    smoothing:float=1.0
    means_:np.ndarray|None=None
    variances_:np.ndarray|None=None
    transition_:np.ndarray|None=None
    initial_:np.ndarray|None=None
    state_positive_rate_:np.ndarray|None=None
    converged_:bool=False

    def fit(self,x_train,y_train):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<40 or x.shape[1]<1: raise HMMContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise HMMContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}): raise HMMContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise HMMContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if isinstance(self.n_states,bool) or self.n_states<2 or self.n_states>5: raise HMMContractError("N_STATES_OUT_OF_RANGE")
        if self.max_iter<1 or self.tol<=0 or self.smoothing<=0: raise HMMContractError("HMM_PARAMETER_INVALID")
        self.mean_x_=x.mean(0); self.scale_x_=x.std(0); self.scale_x_[self.scale_x_==0]=1
        z=(x-self.mean_x_)/self.scale_x_; n,d=z.shape; k=self.n_states
        rng=np.random.default_rng(self.random_state)
        centers=np.quantile(z,np.linspace(.1,.9,k),axis=0)
        centers=centers+rng.normal(0,.01,centers.shape)
        means=centers.copy(); global_var=np.maximum(z.var(0),1e-3); variances=np.tile(global_var,(k,1))
        trans=np.full((k,k),1.0/k); initial=np.full(k,1.0/k)
        prev=-np.inf
        for iteration in range(self.max_iter):
            log_emit=np.empty((n,k))
            for s in range(k):
                diff=z-means[s]
                log_emit[:,s]=-.5*np.sum(np.log(2*np.pi*variances[s])+diff*diff/variances[s],axis=1)
            la=np.empty((n,k)); la[0]=np.log(initial+1e-15)+log_emit[0]
            for t in range(1,n):
                la[t]=log_emit[t]+np.array([_logsumexp(la[t-1]+np.log(trans[:,s]+1e-15)) for s in range(k)])
            lb=np.zeros((n,k))
            for t in range(n-2,-1,-1):
                for s in range(k): lb[t,s]=_logsumexp(np.log(trans[s]+1e-15)+log_emit[t+1]+lb[t+1])
            ll=_logsumexp(la[-1])
            gamma=np.exp(la+lb-np.array([_logsumexp(la[t]+lb[t]) for t in range(n)])[:,None])
            xi_sum=np.zeros((k,k))
            for t in range(n-1):
                v=la[t,:,None]+np.log(trans+1e-15)+log_emit[t+1,None,:]+lb[t+1,None,:]
                xi_sum+=np.exp(v-_logsumexp(v))
            initial=np.maximum(gamma[0],1e-8); initial/=initial.sum()
            trans=xi_sum+1e-3; trans/=trans.sum(axis=1,keepdims=True)
            for s in range(k):
                w=gamma[:,s]; denom=w.sum()+1e-9
                means[s]=(w[:,None]*z).sum(0)/denom
                variances[s]=np.maximum((w[:,None]*(z-means[s])**2).sum(0)/denom,1e-4)
            if iteration>0 and abs(ll-prev)<=self.tol*(1+abs(prev)):
                self.converged_=True; break
            prev=ll
        # Recompute state posterior using final parameters.
        log_emit=np.empty((n,k))
        for s in range(k):
            diff=z-means[s]; log_emit[:,s]=-.5*np.sum(np.log(2*np.pi*variances[s])+diff*diff/variances[s],axis=1)
        la=np.empty((n,k)); la[0]=np.log(initial+1e-15)+log_emit[0]
        for t in range(1,n): la[t]=log_emit[t]+np.array([_logsumexp(la[t-1]+np.log(trans[:,s]+1e-15)) for s in range(k)])
        post=np.exp(la-np.array([_logsumexp(la[t]) for t in range(n)])[:,None])
        rates=np.empty(k)
        for s in range(k): rates[s]=(float((post[:,s]*y).sum())+self.smoothing)/(float(post[:,s].sum())+2*self.smoothing)
        self.means_=means; self.variances_=variances; self.transition_=trans; self.initial_=initial; self.state_positive_rate_=rates
        return self

    def predict_proba(self,x_test):
        if self.means_ is None: raise HMMContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=len(self.mean_x_): raise HMMContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise HMMContractError("PREDICTION_FEATURES_NONFINITE")
        z=(x-self.mean_x_)/self.scale_x_; k=self.n_states; p_state=self.initial_.copy(); out=[]
        for row in z:
            p_state=p_state@self.transition_
            log_emit=np.array([-.5*np.sum(np.log(2*np.pi*self.variances_[s])+(row-self.means_[s])**2/self.variances_[s]) for s in range(k)])
            logp=np.log(p_state+1e-15)+log_emit
            p_state=np.exp(logp-_logsumexp(logp))
            out.append(float(p_state@self.state_positive_rate_))
        p=np.asarray(out)
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise HMMContractError("PREDICTION_PROBABILITY_INVALID")
        return p
