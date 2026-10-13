"""Train-only standardized LDA/QDA probability adapters."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

class DiscriminantContractError(ValueError):
    pass

def _validate_xy(x_train,y_train):
    x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
    if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<20 or x.shape[1]<1:
        raise DiscriminantContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
    if not np.isfinite(x).all(): raise DiscriminantContractError("TRAINING_FEATURES_NONFINITE")
    if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}):
        raise DiscriminantContractError("TRAINING_LABELS_INVALID")
    if set(np.unique(y).tolist())!={0,1}: raise DiscriminantContractError("TRAINING_REQUIRES_BOTH_CLASSES")
    return x,y.astype(int)

@dataclass
class LDAProbabilityAdapter:
    shrinkage: float | str = "auto"
    model: Pipeline | None = None

    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_validate_xy(x_train,y_train)
        if self.shrinkage != "auto" and (isinstance(self.shrinkage,bool) or not isinstance(self.shrinkage,(int,float)) or not np.isfinite(self.shrinkage) or not 0<=self.shrinkage<=1):
            raise DiscriminantContractError("LDA_SHRINKAGE_INVALID")
        estimator=LinearDiscriminantAnalysis(solver="lsqr",shrinkage=self.shrinkage)
        self.model=Pipeline([("scale",StandardScaler()),("lda",estimator)])
        self.model.fit(x,y); return self

    def predict_proba(self,x_test):
        if self.model is None: raise DiscriminantContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.model.named_steps["scale"].n_features_in_: raise DiscriminantContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise DiscriminantContractError("PREDICTION_FEATURES_NONFINITE")
        p=self.model.predict_proba(x)[:,1]
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise DiscriminantContractError("PREDICTION_PROBABILITY_INVALID")
        return p

@dataclass
class QDAProbabilityAdapter:
    reg_param: float = 0.0
    model: Pipeline | None = None

    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_validate_xy(x_train,y_train)
        if isinstance(self.reg_param,bool) or not isinstance(self.reg_param,(int,float)) or not np.isfinite(self.reg_param) or not 0<=self.reg_param<=1:
            raise DiscriminantContractError("QDA_REG_PARAM_INVALID")
        self.model=Pipeline([("scale",StandardScaler()),("qda",QuadraticDiscriminantAnalysis(reg_param=float(self.reg_param)))])
        self.model.fit(x,y); return self

    def predict_proba(self,x_test):
        if self.model is None: raise DiscriminantContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.model.named_steps["scale"].n_features_in_: raise DiscriminantContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise DiscriminantContractError("PREDICTION_FEATURES_NONFINITE")
        p=self.model.predict_proba(x)[:,1]
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise DiscriminantContractError("PREDICTION_PROBABILITY_INVALID")
        return p
