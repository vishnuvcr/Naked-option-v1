"""Train-only elastic-net logistic probability adapter."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

class ElasticNetLogisticContractError(ValueError):
    pass

@dataclass
class ElasticNetLogisticProbabilityAdapter:
    c: float = 1.0
    l1_ratio: float = 0.5
    max_iter: int = 5000
    random_state: int = 42
    model: Pipeline | None = None

    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<20 or x.shape[1]<1:
            raise ElasticNetLogisticContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise ElasticNetLogisticContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}):
            raise ElasticNetLogisticContractError("TRAINING_LABELS_INVALID")
        if set(np.unique(y).tolist())!={0,1}: raise ElasticNetLogisticContractError("TRAINING_REQUIRES_BOTH_CLASSES")
        if isinstance(self.c,bool) or not np.isfinite(self.c) or self.c<=0: raise ElasticNetLogisticContractError("C_MUST_BE_FINITE_POSITIVE")
        if isinstance(self.l1_ratio,bool) or not np.isfinite(self.l1_ratio) or not 0<=self.l1_ratio<=1:
            raise ElasticNetLogisticContractError("L1_RATIO_MUST_BE_IN_ZERO_ONE")
        self.model=Pipeline([
            ("scale",StandardScaler()),
            ("logit",LogisticRegression(penalty="elasticnet",solver="saga",C=float(self.c),l1_ratio=float(self.l1_ratio),max_iter=int(self.max_iter),random_state=int(self.random_state))),
        ])
        self.model.fit(x,y.astype(int))
        return self

    def predict_proba(self,x_test:Sequence[Sequence[float]])->np.ndarray:
        if self.model is None: raise ElasticNetLogisticContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.model.named_steps["scale"].n_features_in_:
            raise ElasticNetLogisticContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise ElasticNetLogisticContractError("PREDICTION_FEATURES_NONFINITE")
        p=self.model.predict_proba(x)[:,1]
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise ElasticNetLogisticContractError("PREDICTION_PROBABILITY_INVALID")
        return p
