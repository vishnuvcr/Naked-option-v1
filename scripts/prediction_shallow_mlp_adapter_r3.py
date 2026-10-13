"""Deterministic one-hidden-layer MLP with dropout and Adam; no data I/O."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np

class MLPContractError(ValueError):
    pass

def _sigmoid(z):
    z=np.clip(z,-35.0,35.0)
    return 1.0/(1.0+np.exp(-z))

@dataclass
class ShallowMLPProbabilityAdapter:
    hidden_units:int=32
    dropout:float=0.2
    weight_decay:float=0.001
    learning_rate:float=0.01
    epochs:int=250
    batch_size:int=64
    random_state:int=42
    mean_:np.ndarray|None=None
    scale_:np.ndarray|None=None
    w1_:np.ndarray|None=None
    b1_:np.ndarray|None=None
    w2_:np.ndarray|None=None
    b2_:float|None=None
    fitted_:bool=False

    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<30 or x.shape[1]<1: raise MLPContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise MLPContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}): raise MLPContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise MLPContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if isinstance(self.hidden_units,bool) or not isinstance(self.hidden_units,int) or self.hidden_units<1: raise MLPContractError("HIDDEN_UNITS_INVALID")
        if not np.isfinite(self.dropout) or not 0<=self.dropout<0.8: raise MLPContractError("DROPOUT_INVALID")
        if not np.isfinite(self.weight_decay) or self.weight_decay<0: raise MLPContractError("WEIGHT_DECAY_INVALID")
        if not np.isfinite(self.learning_rate) or self.learning_rate<=0 or self.epochs<1 or self.batch_size<1: raise MLPContractError("OPTIMIZER_PARAMETERS_INVALID")
        self.mean_=x.mean(axis=0); self.scale_=x.std(axis=0); self.scale_[self.scale_==0]=1.0
        z=(x-self.mean_)/self.scale_; labels=y.astype(float)
        rng=np.random.default_rng(self.random_state)
        fan_in=z.shape[1]; h=self.hidden_units
        self.w1_=rng.normal(0,np.sqrt(2.0/fan_in),size=(fan_in,h))
        self.b1_=np.zeros(h); self.w2_=rng.normal(0,np.sqrt(2.0/h),size=h); self.b2_=0.0
        params=[self.w1_,self.b1_,self.w2_,np.array([self.b2_])]
        m=[np.zeros_like(p) for p in params]; v=[np.zeros_like(p) for p in params]; step=0
        for _ in range(self.epochs):
            order=rng.permutation(len(z))
            for start in range(0,len(z),self.batch_size):
                ix=order[start:start+self.batch_size]; xb=z[ix]; yb=labels[ix]; n=len(ix)
                if self.dropout>0:
                    mask=(rng.random((n,h))>=self.dropout).astype(float)/(1.0-self.dropout)
                else:
                    mask=np.ones((n,h),dtype=float)
                _,grads_tuple=self._batch_loss_and_grad(xb,yb,self.w1_,self.b1_,self.w2_,self.b2_,mask,self.weight_decay)
                gw1,gb1,gw2,gb2=grads_tuple
                grads=[gw1,gb1,gw2,np.array([gb2])]
                current=[self.w1_,self.b1_,self.w2_,np.array([self.b2_])]
                step+=1
                for i,(p,g) in enumerate(zip(current,grads)):
                    m[i]=0.9*m[i]+0.1*g; v[i]=0.999*v[i]+0.001*(g*g)
                    mhat=m[i]/(1-0.9**step); vhat=v[i]/(1-0.999**step)
                    current[i]=p-self.learning_rate*mhat/(np.sqrt(vhat)+1e-8)
                self.w1_,self.b1_,self.w2_=current[0],current[1],current[2]; self.b2_=float(current[3][0])
        self.fitted_=True
        return self

    @staticmethod
    def _batch_loss_and_grad(xb,yb,w1,b1,w2,b2,mask,weight_decay):
        hidden_pre=xb@w1+b1
        hidden=np.maximum(hidden_pre,0.0)
        hidden_drop=hidden*mask
        logits=hidden_drop@w2+b2
        pred=_sigmoid(logits)
        loss=float(np.mean(np.logaddexp(0.0,logits)-yb*logits)+0.5*weight_decay*(np.sum(w1*w1)+np.sum(w2*w2)))
        dlogit=(pred-yb)/len(xb)
        gw2=hidden_drop.T@dlogit+weight_decay*w2
        gb2=float(dlogit.sum())
        dh=(dlogit[:,None]*w2[None,:])*mask
        dpre=dh*(hidden_pre>0)
        gw1=xb.T@dpre+weight_decay*w1
        gb1=dpre.sum(axis=0)
        return loss,(gw1,gb1,gw2,gb2)

    def predict_proba(self,x_test:Sequence[Sequence[float]])->np.ndarray:
        if not self.fitted_ or self.mean_ is None or self.scale_ is None: raise MLPContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=len(self.mean_): raise MLPContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise MLPContractError("PREDICTION_FEATURES_NONFINITE")
        hidden=np.maximum(((x-self.mean_)/self.scale_)@self.w1_+self.b1_,0.0)
        p=_sigmoid(hidden@self.w2_+self.b2_)
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise MLPContractError("PREDICTION_PROBABILITY_INVALID")
        return p
