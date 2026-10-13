"""Raw decision-score adapters; scores require chronological inner-OOF calibration before log-loss."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from sklearn.svm import SVC
from sklearn.neighbors import NearestCentroid, KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

class MarginAdapterContractError(ValueError):
    pass

def _xy(x_train,y_train):
    x=np.asarray(x_train,dtype=float); y=np.asarray(y_train)
    if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or len(x)<20 or x.shape[1]<1: raise MarginAdapterContractError("TRAINING_SHAPE_OR_SIZE_INVALID")
    if not np.isfinite(x).all(): raise MarginAdapterContractError("TRAINING_FEATURES_NONFINITE")
    if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0,1}): raise MarginAdapterContractError("TRAINING_LABELS_INVALID")
    if set(np.unique(y).tolist())!={0,1}: raise MarginAdapterContractError("TRAINING_REQUIRES_BOTH_CLASSES")
    return x,y.astype(int)

def _scores(model,x_test,n_features,kind):
    if model is None: raise MarginAdapterContractError("MODEL_NOT_FIT")
    x=np.asarray(x_test,dtype=float)
    if x.ndim!=2 or x.shape[1]!=n_features: raise MarginAdapterContractError("PREDICTION_SHAPE_INVALID")
    if not np.isfinite(x).all(): raise MarginAdapterContractError("PREDICTION_FEATURES_NONFINITE")
    if kind=="svm": out=model.decision_function(x)
    elif kind=="centroid":
        z=model.named_steps["scale"].transform(x)
        centers=model.named_steps["centroid"].centroids_
        distances=np.linalg.norm(z[:,None,:]-centers[None,:,:],axis=2)
        # Positive score favors class 1: distance to class 0 minus distance to class 1.
        out=distances[:,0]-distances[:,1]
    else:
        # Smoothed log odds of neighbor class-1 mass; calibrate this score on chronological OOF.
        probabilities=model.predict_proba(x)[:,1]
        probabilities=np.clip(probabilities,1e-6,1-1e-6)
        out=np.log(probabilities/(1-probabilities))
    if out.ndim!=1 or not np.isfinite(out).all(): raise MarginAdapterContractError("DECISION_SCORE_INVALID")
    return out

@dataclass
class KernelSVMScoreAdapter:
    c:float=1.0; kernel:str="rbf"; gamma:str|float="scale"; random_state:int=42
    model:Pipeline|None=None; n_features_:int|None=None
    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_xy(x_train,y_train)
        if not np.isfinite(self.c) or self.c<=0: raise MarginAdapterContractError("SVM_C_INVALID")
        if self.kernel not in {"linear","poly","rbf","sigmoid"}: raise MarginAdapterContractError("SVM_KERNEL_INVALID")
        if not (self.gamma in {"scale","auto"} if isinstance(self.gamma,str) else isinstance(self.gamma,(int,float)) and np.isfinite(self.gamma) and self.gamma>0): raise MarginAdapterContractError("SVM_GAMMA_INVALID")
        self.model=Pipeline([("scale",StandardScaler()),("svm",SVC(C=float(self.c),kernel=self.kernel,gamma=self.gamma,probability=False,random_state=self.random_state))])
        self.model.fit(x,y); self.n_features_=x.shape[1]; return self
    def predict_score(self,x_test): return _scores(self.model,x_test,self.n_features_,"svm")

@dataclass
class NearestCentroidScoreAdapter:
    shrink_threshold:float=0.0; model:Pipeline|None=None; n_features_:int|None=None
    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_xy(x_train,y_train)
        if not np.isfinite(self.shrink_threshold) or self.shrink_threshold<0: raise MarginAdapterContractError("CENTROID_SHRINK_THRESHOLD_INVALID")
        threshold=None if self.shrink_threshold==0 else float(self.shrink_threshold)
        self.model=Pipeline([("scale",StandardScaler()),("centroid",NearestCentroid(shrink_threshold=threshold))])
        self.model.fit(x,y); self.n_features_=x.shape[1]; return self
    def predict_score(self,x_test): return _scores(self.model,x_test,self.n_features_,"centroid")

@dataclass
class KNNDensityRatioScoreAdapter:
    n_neighbors:int=15; weights:str="distance"; model:Pipeline|None=None; n_features_:int|None=None; y_train_:np.ndarray|None=None; class_counts_:dict|None=None
    def fit(self,x_train:Sequence[Sequence[float]],y_train:Sequence[int]):
        x,y=_xy(x_train,y_train)
        if isinstance(self.n_neighbors,bool) or not isinstance(self.n_neighbors,int) or not 1<=self.n_neighbors<len(x): raise MarginAdapterContractError("KNN_NEIGHBORS_INVALID")
        if self.weights not in {"uniform","distance"}: raise MarginAdapterContractError("KNN_WEIGHTS_INVALID")
        self.model=Pipeline([("scale",StandardScaler()),("knn",KNeighborsClassifier(n_neighbors=self.n_neighbors,weights=self.weights))])
        self.model.fit(x,y); self.n_features_=x.shape[1]; self.y_train_=y.copy()
        self.class_counts_={0:int(np.sum(y==0)),1:int(np.sum(y==1))}
        return self
    def predict_score(self,x_test):
        if self.model is None or self.y_train_ is None or self.class_counts_ is None: raise MarginAdapterContractError("MODEL_NOT_FIT")
        x=np.asarray(x_test,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.n_features_: raise MarginAdapterContractError("PREDICTION_SHAPE_INVALID")
        if not np.isfinite(x).all(): raise MarginAdapterContractError("PREDICTION_FEATURES_NONFINITE")
        z=self.model.named_steps["scale"].transform(x)
        distances,indices=self.model.named_steps["knn"].kneighbors(z,return_distance=True)
        scores=[]
        for d,ix in zip(distances,indices):
            if self.weights=="uniform":
                w=np.ones_like(d)
            else:
                zero=(d==0)
                w=zero.astype(float) if zero.any() else 1.0/np.maximum(d,np.finfo(float).tiny)
            y_near=self.y_train_[ix]
            mass0=float(w[y_near==0].sum()); mass1=float(w[y_near==1].sum())
            density0=(mass0+0.5)/self.class_counts_[0]
            density1=(mass1+0.5)/self.class_counts_[1]
            scores.append(float(np.log(density1)-np.log(density0)))
        out=np.asarray(scores,dtype=float)
        if not np.isfinite(out).all(): raise MarginAdapterContractError("DECISION_SCORE_INVALID")
        return out
