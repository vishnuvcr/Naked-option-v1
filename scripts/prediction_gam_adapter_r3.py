"""Additive spline logistic probability adapter; spline knots fit on training rows only."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, SplineTransformer

class GAMContractError(ValueError):
    pass

@dataclass
class GeneralizedAdditiveProbabilityAdapter:
    max_splines:int=5
    c:float=1.0
    random_state:int=42
    model:Pipeline|None=None

    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<30 or x.shape[1]<1: raise GAMContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise GAMContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}): raise GAMContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise GAMContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if isinstance(self.max_splines,bool) or not isinstance(self.max_splines,int) or not 2<=self.max_splines<=30: raise GAMContractError("MAX_SPLINES_INVALID")
        if not np.isfinite(self.c) or self.c<=0: raise GAMContractError("C_INVALID")
        self.model=Pipeline([
            ("scale",StandardScaler()),
            ("splines",SplineTransformer(n_knots=self.max_splines,degree=3,knots="quantile",include_bias=False)),
            ("logit",LogisticRegression(C=float(self.c),penalty="l2",solver="lbfgs",max_iter=3000,random_state=self.random_state))
        ])
        self.model.fit(x,y.astype(int)); return self

    def predict_proba(self,x_test:Sequence[Sequence[float]])->np.ndarray:
        if self.model is None: raise GAMContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        n_features=self.model.named_steps["scale"].n_features_in_
        if x.ndim!=2 or x.shape[1]!=n_features: raise GAMContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise GAMContractError("PREDICTION_FEATURES_NONFINITE")
        p=self.model.predict_proba(x)[:,1]
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise GAMContractError("PREDICTION_PROBABILITY_INVALID")
        return p
