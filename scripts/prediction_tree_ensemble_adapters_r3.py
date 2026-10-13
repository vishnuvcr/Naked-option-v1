"""Deterministic tree-ensemble probability adapters; calibration is external and OOF-only."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier

class TreeAdapterContractError(ValueError):
    pass

def _xy(x_train,y_train):
    x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
    if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<20 or x.shape[1]<1:
        raise TreeAdapterContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
    if not np.isfinite(x).all(): raise TreeAdapterContractError("TRAINING_FEATURES_NONFINITE")
    if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}):
        raise TreeAdapterContractError("TRAINING_LABELS_INVALID")
    if set(np.unique(y).tolist())!={0,1}: raise TreeAdapterContractError("TRAINING_REQUIRES_BOTH_CLASSES")
    return x,y.astype(int)

def _predict(model,x_test,n_features):
    if model is None: raise TreeAdapterContractError("MODEL_NOT_FIT")
    x=np.asarray(x_test,dtype=float)
    if x.ndim!=2 or x.shape[1]!=n_features: raise TreeAdapterContractError("PREDICTION_SHAPE_INVALID")
    if not np.isfinite(x).all(): raise TreeAdapterContractError("PREDICTION_FEATURES_NONFINITE")
    p=model.predict_proba(x)[:,1]
    if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise TreeAdapterContractError("PREDICTION_PROBABILITY_INVALID")
    return p

@dataclass
class RandomForestProbabilityAdapter:
    n_estimators:int=200; max_depth:int|None=4; min_samples_leaf:int=5; random_state:int=42; model:object|None=None; n_features_:int|None=None
    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_xy(x_train,y_train)
        if self.n_estimators<1 or self.min_samples_leaf<1 or (self.max_depth is not None and self.max_depth<1): raise TreeAdapterContractError("TREE_PARAMETERS_INVALID")
        self.model=RandomForestClassifier(n_estimators=self.n_estimators,max_depth=self.max_depth,min_samples_leaf=self.min_samples_leaf,random_state=self.random_state,n_jobs=1)
        self.model.fit(x,y); self.n_features_=x.shape[1]; return self
    def predict_proba(self,x_test): return _predict(self.model,x_test,self.n_features_)

@dataclass
class ExtraTreesProbabilityAdapter:
    n_estimators:int=200; max_depth:int|None=4; min_samples_leaf:int=5; random_state:int=42; model:object|None=None; n_features_:int|None=None
    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_xy(x_train,y_train)
        if self.n_estimators<1 or self.min_samples_leaf<1 or (self.max_depth is not None and self.max_depth<1): raise TreeAdapterContractError("TREE_PARAMETERS_INVALID")
        self.model=ExtraTreesClassifier(n_estimators=self.n_estimators,max_depth=self.max_depth,min_samples_leaf=self.min_samples_leaf,random_state=self.random_state,n_jobs=1)
        self.model.fit(x,y); self.n_features_=x.shape[1]; return self
    def predict_proba(self,x_test): return _predict(self.model,x_test,self.n_features_)

@dataclass
class GradientBoostingProbabilityAdapter:
    n_estimators:int=100; max_depth:int=2; learning_rate:float=0.05; random_state:int=42; model:object|None=None; n_features_:int|None=None
    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_xy(x_train,y_train)
        if self.n_estimators<1 or self.max_depth<1 or not np.isfinite(self.learning_rate) or self.learning_rate<=0: raise TreeAdapterContractError("BOOSTING_PARAMETERS_INVALID")
        self.model=GradientBoostingClassifier(n_estimators=self.n_estimators,max_depth=self.max_depth,learning_rate=self.learning_rate,random_state=self.random_state)
        self.model.fit(x,y); self.n_features_=x.shape[1]; return self
    def predict_proba(self,x_test): return _predict(self.model,x_test,self.n_features_)

@dataclass
class HistGradientBoostingProbabilityAdapter:
    max_iter:int=100; max_leaf_nodes:int=7; l2_regularization:float=1.0; learning_rate:float=0.1; random_state:int=42; model:object|None=None; n_features_:int|None=None
    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_xy(x_train,y_train)
        if self.max_iter<1 or self.max_leaf_nodes<2 or not np.isfinite(self.l2_regularization) or self.l2_regularization<0 or not np.isfinite(self.learning_rate) or self.learning_rate<=0:
            raise TreeAdapterContractError("HIST_BOOSTING_PARAMETERS_INVALID")
        self.model=HistGradientBoostingClassifier(max_iter=self.max_iter,max_leaf_nodes=self.max_leaf_nodes,l2_regularization=self.l2_regularization,learning_rate=self.learning_rate,random_state=self.random_state)
        self.model.fit(x,y); self.n_features_=x.shape[1]; return self
    def predict_proba(self,x_test): return _predict(self.model,x_test,self.n_features_)
