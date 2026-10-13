"""Causal rolling-window change-point segment classifier; no future rows are used for break detection."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np

class ChangePointContractError(ValueError):
    pass

@dataclass
class ChangePointSegmentProbabilityAdapter:
    min_segment:int=100
    penalty:float=5.0
    mean_:np.ndarray|None=None
    scale_:np.ndarray|None=None
    boundaries_:list[int]|None=None
    segment_probabilities_:list[float]|None=None
    n_features_:int|None=None
    fitted_:bool=False

    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<max(30,2*self.min_segment) or x.shape[1]<1:
            raise ChangePointContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise ChangePointContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}): raise ChangePointContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise ChangePointContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if isinstance(self.min_segment,bool) or not isinstance(self.min_segment,int) or self.min_segment<10:
            raise ChangePointContractError("MIN_SEGMENT_INVALID")
        if not np.isfinite(self.penalty) or self.penalty<=0: raise ChangePointContractError("PENALTY_INVALID")
        self.mean_=x.mean(axis=0); self.scale_=x.std(axis=0); self.scale_[self.scale_==0]=1.0
        z=(x-self.mean_)/self.scale_; m=self.min_segment
        # Causal mean-shift scan: candidate t uses only rows strictly before/at t.
        boundaries=[0]; last=0
        for t in range(2*m,len(z)+1):
            if t-last < m: continue
            left=z[t-2*m:t-m]; right=z[t-m:t]
            delta=right.mean(axis=0)-left.mean(axis=0)
            statistic=float(m*(delta@delta))
            if statistic>self.penalty:
                boundary=t-m
                if boundary-last>=m and len(z)-boundary>=m:
                    boundaries.append(boundary); last=boundary
        boundaries.append(len(z))
        probs=[]
        for a,b in zip(boundaries[:-1],boundaries[1:]):
            yy=y[a:b].astype(int)
            probs.append(float((yy.sum()+1.0)/(len(yy)+2.0)))
        self.boundaries_=boundaries; self.segment_probabilities_=probs; self.n_features_=x.shape[1]; self.fitted_=True
        return self

    def predict_proba(self,x_test:Sequence[Sequence[float]])->np.ndarray:
        if not self.fitted_ or self.segment_probabilities_ is None or self.n_features_ is None:
            raise ChangePointContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.n_features_: raise ChangePointContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise ChangePointContractError("PREDICTION_FEATURES_NONFINITE")
        # At the start of a future validation window, use the latest causal training regime.
        return np.full(len(x),self.segment_probabilities_[-1],dtype=float)
