"""Deterministic one-layer causal temporal convolutional binary classifier (NumPy).

Input shape: samples x sequence_length x features. Train-only feature scaling, ReLU
causal convolution, global average pooling, sigmoid output, and Adam optimization.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
class TemporalConvContractError(ValueError): pass

@dataclass
class TemporalConvolutionAdapter:
    channels:int=8
    kernel_size:int=3
    learning_rate:float=0.01
    epochs:int=120
    l2:float=1e-3
    random_state:int=42
    mean_:np.ndarray|None=None
    scale_:np.ndarray|None=None
    conv_weights_:np.ndarray|None=None
    conv_bias_:np.ndarray|None=None
    head_weights_:np.ndarray|None=None
    head_bias_:float=0.0
    loss_history_:list|None=None

    def _forward(self,x):
        n,t,d=x.shape; k=self.kernel_size; c=self.channels
        out=np.zeros((n,t-k+1,c))
        for j in range(k):
            out[:,j:t-k+j+1,:]+=np.einsum("ntd,dc->ntc",x[:,j:t-k+j+1,:],self.conv_weights_[j])
        out+=self.conv_bias_[None,None,:]
        act=np.maximum(out,0)
        pooled=act.mean(axis=1)
        logits=pooled@self.head_weights_+self.head_bias_
        return expit(logits),out,act,pooled

    def fit(self,x_train,y_train):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train,dtype=float)
        if x.ndim!=3 or y.ndim!=1 or x.shape[0]!=len(y) or len(y)<40 or x.shape[1]<self.kernel_size or x.shape[2]<1:
            raise TemporalConvContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise TemporalConvContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y).all() or not set(np.unique(y).tolist()).issubset({0.0,1.0}): raise TemporalConvContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0.0,1.0}: raise TemporalConvContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if self.channels<1 or self.kernel_size<1 or self.epochs<1 or self.learning_rate<=0 or self.l2<0: raise TemporalConvContractError("MODEL_PARAMETER_INVALID")
        self.mean_=x.mean(axis=(0,1)); self.scale_=x.std(axis=(0,1)); self.scale_[self.scale_==0]=1.0
        z=(x-self.mean_[None,None,:])/self.scale_[None,None,:]
        rng=np.random.default_rng(self.random_state); d=x.shape[2]; c=self.channels; k=self.kernel_size
        self.conv_weights_=rng.normal(0,np.sqrt(2/(k*d)),size=(k,d,c)); self.conv_bias_=np.zeros(c)
        self.head_weights_=rng.normal(0,.05,size=c); self.head_bias_=0.0
        params=[self.conv_weights_,self.conv_bias_,self.head_weights_,np.array([self.head_bias_])]
        m=[np.zeros_like(p) for p in params]; v=[np.zeros_like(p) for p in params]; self.loss_history_=[]
        for epoch in range(1,self.epochs+1):
            p,pre,act,pooled=self._forward(z); p=np.clip(p,1e-8,1-1e-8)
            loss=-np.mean(y*np.log(p)+(1-y)*np.log(1-p))+.5*self.l2*(np.sum(self.conv_weights_**2)+np.sum(self.head_weights_**2))
            self.loss_history_.append(float(loss))
            dl=(p-y)/len(y)
            gh=pooled.T@dl+self.l2*self.head_weights_; gb=np.array([dl.sum()])
            gpool=dl[:,None]*self.head_weights_[None,:]
            gact=np.broadcast_to(gpool[:,None,:]/act.shape[1],act.shape)*(pre>0)
            gw=np.zeros_like(self.conv_weights_)
            for j in range(k):
                gw[j]=np.einsum("ntd,ntc->dc",z[:,j:z.shape[1]-k+j+1,:],gact)
            gw+=self.l2*self.conv_weights_; gcb=gact.sum(axis=(0,1))
            grads=[gw,gcb,gh,gb]
            for q,(param,grad) in enumerate(zip(params,grads)):
                m[q]=.9*m[q]+.1*grad; v[q]=.999*v[q]+.001*grad*grad
                mh=m[q]/(1-.9**epoch); vh=v[q]/(1-.999**epoch)
                param-=self.learning_rate*mh/(np.sqrt(vh)+1e-8)
            self.head_bias_=float(params[3][0])
        return self

    def predict_proba(self,x_test):
        if self.conv_weights_ is None: raise TemporalConvContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=3 or x.shape[1]<self.kernel_size or x.shape[2]!=len(self.mean_): raise TemporalConvContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise TemporalConvContractError("PREDICTION_FEATURES_NONFINITE")
        z=(x-self.mean_[None,None,:])/self.scale_[None,None,:]
        p=self._forward(z)[0]
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise TemporalConvContractError("PREDICTION_PROBABILITY_INVALID")
        return p
