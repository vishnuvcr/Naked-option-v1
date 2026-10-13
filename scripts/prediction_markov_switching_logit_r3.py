"""Two-regime Markov-switching logistic model with EM-like soft regime assignments.

For research contract testing only. All fitted state, logistic parameters and scaling use
training rows. The caller must supply chronologically ordered rows and handle calibration.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
from scipy.optimize import minimize
class MarkovSwitchingLogitContractError(ValueError): pass

@dataclass
class MarkovSwitchingLogitAdapter:
    n_regimes:int=2
    max_iter:int=30
    ridge:float=1.0
    random_state:int=42
    mean_:np.ndarray|None=None
    scale_:np.ndarray|None=None
    coefficients_:np.ndarray|None=None
    intercepts_:np.ndarray|None=None
    transition_:np.ndarray|None=None
    initial_:np.ndarray|None=None
    converged_:bool=False
    last_state_posterior_:np.ndarray|None=None

    def fit(self,x_train,y_train):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<60 or x.shape[1]<1: raise MarkovSwitchingLogitContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise MarkovSwitchingLogitContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}): raise MarkovSwitchingLogitContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise MarkovSwitchingLogitContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if self.n_regimes!=2 or self.max_iter<1 or not np.isfinite(self.ridge) or self.ridge<=0: raise MarkovSwitchingLogitContractError("MODEL_PARAMETER_INVALID")
        self.mean_=x.mean(0); self.scale_=x.std(0); self.scale_[self.scale_==0]=1
        z=(x-self.mean_)/self.scale_; n,d=z.shape; rng=np.random.default_rng(self.random_state)
        # Stable initialization by deterministic split on first standardized feature.
        order=np.argsort(z[:,0],kind="stable"); groups=np.zeros(n,dtype=int); groups[order[n//2:]]=1
        coefs=np.zeros((2,d)); intercepts=np.zeros(2)
        for s in range(2):
            ix=groups==s
            if len(np.unique(y[ix]))<2: ix=np.ones(n,dtype=bool)
            def obj(theta):
                eta=theta[0]+z[ix]@theta[1:]; p=np.clip(expit(eta),1e-9,1-1e-9)
                loss=-np.sum(y[ix]*np.log(p)+(1-y[ix])*np.log(1-p))+.5*self.ridge*np.sum(theta[1:]**2)
                grad_eta=p-y[ix]; grad=np.r_[grad_eta.sum(),z[ix].T@grad_eta+self.ridge*theta[1:]]
                return float(loss),grad
            res=minimize(obj,np.zeros(d+1),jac=True,method="L-BFGS-B")
            intercepts[s]=res.x[0]; coefs[s]=res.x[1:]
        trans=np.array([[.9,.1],[.1,.9]]); prior=np.array([.5,.5]); old=-np.inf
        for it in range(self.max_iter):
            eta=np.column_stack([intercepts[s]+z@coefs[s] for s in range(2)])
            p=np.clip(expit(eta),1e-9,1-1e-9)
            loge=y[:,None]*np.log(p)+(1-y[:,None])*np.log(1-p)
            la=np.empty((n,2)); la[0]=np.log(prior)+loge[0]
            for t in range(1,n):
                for s in range(2): la[t,s]=loge[t,s]+np.logaddexp(la[t-1,0]+np.log(trans[0,s]),la[t-1,1]+np.log(trans[1,s]))
            lb=np.zeros((n,2))
            for t in range(n-2,-1,-1):
                for s in range(2): lb[t,s]=np.logaddexp(np.log(trans[s,0])+loge[t+1,0]+lb[t+1,0],np.log(trans[s,1])+loge[t+1,1]+lb[t+1,1])
            norm=np.logaddexp(la[:,0]+lb[:,0],la[:,1]+lb[:,1]); gamma=np.exp(la+lb-norm[:,None])
            xi=np.zeros((2,2))
            for t in range(n-1):
                v=la[t,:,None]+np.log(trans)+loge[t+1,None,:]+lb[t+1,None,:]
                v-=np.logaddexp(np.logaddexp(v[0,0],v[0,1]),np.logaddexp(v[1,0],v[1,1]))
                xi+=np.exp(v)
            prior=np.maximum(gamma[0],1e-6); prior/=prior.sum()
            trans=xi+.05; trans/=trans.sum(1,keepdims=True)
            for s in range(2):
                w=gamma[:,s]
                def objw(theta):
                    et=theta[0]+z@theta[1:]; pp=np.clip(expit(et),1e-9,1-1e-9)
                    loss=-np.sum(w*(y*np.log(pp)+(1-y)*np.log(1-pp)))+.5*self.ridge*np.sum(theta[1:]**2)
                    ge=w*(pp-y); return float(loss),np.r_[ge.sum(),z.T@ge+self.ridge*theta[1:]]
                res=minimize(objw,np.r_[intercepts[s],coefs[s]],jac=True,method="L-BFGS-B")
                intercepts[s]=res.x[0]; coefs[s]=res.x[1:]
            ll=float(norm.sum())
            if it and abs(ll-old)<1e-5*(1+abs(old)): self.converged_=True; break
            old=ll
        self.coefficients_=coefs; self.intercepts_=intercepts; self.transition_=trans; self.initial_=prior; self.last_state_posterior_=gamma[-1].copy()
        return self

    def predict_proba(self,x_test):
        if self.coefficients_ is None or self.last_state_posterior_ is None: raise MarkovSwitchingLogitContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=len(self.mean_): raise MarkovSwitchingLogitContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise MarkovSwitchingLogitContractError("PREDICTION_FEATURES_NONFINITE")
        z=(x-self.mean_)/self.scale_; state=self.last_state_posterior_.copy(); out=[]
        for row in z:
            state=state@self.transition_
            p=expit(self.intercepts_+self.coefficients_@row)
            out.append(float(state@p))
        result=np.asarray(out)
        if not np.isfinite(result).all() or np.any((result<0)|(result>1)): raise MarkovSwitchingLogitContractError("PREDICTION_PROBABILITY_INVALID")
        return result
