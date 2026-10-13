"""Train-only LDA/QDA probability adapters; no data I/O or empirical authorization."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler

class DiscriminantContractError(ValueError):
    pass

@dataclass
class DiscriminantProbabilityAdapter:
    kind: str = "lda"
    shrinkage: float | str | None = None
    reg_param: float = 0.0
    scaler_: StandardScaler | None = None
    estimator_: object | None = None
    classes_: np.ndarray | None = None

    def fit(self, x_train: Sequence[Sequence[float]], y_train: Sequence[int]):
        x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
        if self.kind not in {"lda","qda"}: raise DiscriminantContractError("KIND_MUST_BE_LDA_OR_QDA")
        if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<20 or x.shape[1]<1:
            raise DiscriminantContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(x).all(): raise DiscriminantContractError("TRAINING_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or set(np.unique(y).tolist())!={0,1}:
            raise DiscriminantContractError("TRAINING_REQUIRES_BINARY_BOTH_CLASSES")
        if self.kind=="lda":
            if self.shrinkage not in {None,"auto"} and (isinstance(self.shrinkage,bool) or not isinstance(self.shrinkage,(int,float)) or not 0<=self.shrinkage<=1):
                raise DiscriminantContractError("LDA_SHRINKAGE_INVALID")
            if self.shrinkage is not None and self.shrinkage!="auto":
                self.estimator_=LinearDiscriminantAnalysis(solver="lsqr",shrinkage=float(self.shrinkage))
            else:
                self.estimator_=LinearDiscriminantAnalysis(solver="lsqr",shrinkage=self.shrinkage)
        else:
            if not np.isfinite(self.reg_param) or not 0<=self.reg_param<=1:
                raise DiscriminantContractError("QDA_REG_PARAM_INVALID")
            self.estimator_=QuadraticDiscriminantAnalysis(reg_param=float(self.reg_param))
        self.scaler_=StandardScaler().fit(x)
        z=self.scaler_.transform(x)
        self.estimator_.fit(z,y.astype(int))
        self.classes_=self.estimator_.classes_.copy()
        if set(self.classes_.tolist())!={0,1}: raise DiscriminantContractError("FITTED_CLASS_SET_INVALID")
        return self

    def predict_proba(self, x_test: Sequence[Sequence[float]]) -> np.ndarray:
        if self.scaler_ is None or self.estimator_ is None: raise DiscriminantContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.scaler_.n_features_in_: raise DiscriminantContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise DiscriminantContractError("PREDICTION_FEATURES_NONFINITE")
        raw=self.estimator_.predict_proba(self.scaler_.transform(x))
        idx=list(self.estimator_.classes_).index(1)
        p=np.asarray(raw[:,idx],dtype=float)
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise DiscriminantContractError("PREDICTION_PROBABILITY_INVALID")
        return p

    def predict_class(self,x_test: Sequence[Sequence[float]]) -> np.ndarray:
        return (self.predict_proba(x_test)>=0.5).astype(int)
