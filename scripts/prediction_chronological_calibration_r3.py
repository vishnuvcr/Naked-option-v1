"""Chronological inner-OOF Platt calibration for Phase 8P R3.

This module accepts only an explicitly supplied inner out-of-fold probability vector.
It cannot create folds or access market data. Callers must construct OOF predictions
using expanding/rolling chronological splits with the registered purge and embargo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression

from prediction_logistic_adapter_r3 import AdapterContractError


@dataclass
class ChronologicalOOFPlattCalibrator:
    model: LogisticRegression | None = None
    fitted_start: str | None = None
    fitted_end: str | None = None

    @staticmethod
    def _validate(p: Sequence[float], y: Sequence[int], timestamps: Sequence[object]):
        p = np.asarray(p, dtype=float)
        y = np.asarray(y)
        t = np.asarray(timestamps)
        if p.ndim != 1 or y.ndim != 1 or t.ndim != 1 or not (len(p) == len(y) == len(t)) or len(p) < 20:
            raise AdapterContractError("OOF_CALIBRATION_VECTOR_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(p).all() or np.any((p <= 0) | (p >= 1)):
            raise AdapterContractError("OOF_CALIBRATION_PROBABILITIES_MUST_BE_FINITE_AND_STRICTLY_INTERIOR")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0, 1}):
            raise AdapterContractError("OOF_CALIBRATION_LABELS_INVALID")
        if set(np.unique(y).tolist()) != {0, 1}:
            raise AdapterContractError("OOF_CALIBRATION_REQUIRES_BOTH_CLASSES")
        try:
            order = np.argsort(t, kind="stable")
            if not np.array_equal(order, np.arange(len(t))):
                raise AdapterContractError("OOF_CALIBRATION_TIMESTAMPS_NOT_STRICTLY_CHRONOLOGICAL")
            if len(np.unique(t)) != len(t):
                raise AdapterContractError("OOF_CALIBRATION_TIMESTAMPS_DUPLICATED")
        except TypeError as exc:
            raise AdapterContractError("OOF_CALIBRATION_TIMESTAMPS_INVALID") from exc
        return p, y.astype(int), t

    @staticmethod
    def _logit(p: np.ndarray) -> np.ndarray:
        return np.log(p / (1.0 - p)).reshape(-1, 1)

    def fit(self, inner_oof_probabilities: Sequence[float], inner_oof_labels: Sequence[int],
            inner_oof_timestamps: Sequence[object]):
        p, y, t = self._validate(inner_oof_probabilities, inner_oof_labels, inner_oof_timestamps)
        self.model = LogisticRegression(
            penalty="l2", C=1.0, solver="lbfgs", max_iter=2000, random_state=42
        )
        self.model.fit(self._logit(p), y)
        self.fitted_start = str(t[0])
        self.fitted_end = str(t[-1])
        return self

    def predict(self, raw_probabilities: Sequence[float]) -> np.ndarray:
        if self.model is None:
            raise AdapterContractError("OOF_CALIBRATOR_NOT_FIT")
        p = np.asarray(raw_probabilities, dtype=float)
        if p.ndim != 1 or not np.isfinite(p).all() or np.any((p <= 0) | (p >= 1)):
            raise AdapterContractError("CALIBRATION_INPUT_PROBABILITIES_INVALID")
        calibrated = self.model.predict_proba(self._logit(p))[:, 1]
        if not np.isfinite(calibrated).all() or np.any((calibrated < 0) | (calibrated > 1)):
            raise AdapterContractError("CALIBRATED_PROBABILITIES_INVALID")
        return calibrated


@dataclass
class ChronologicalScorePlattCalibrator:
    """Platt calibrator for raw decision scores from inner chronological OOF rows only."""
    model: Pipeline | None = None
    fitted_start: str | None = None
    fitted_end: str | None = None

    def fit(self, scores: Sequence[float], y: Sequence[int], timestamps: Sequence[object], c: float = 1.0):
        s=np.asarray(scores,dtype=float); labels=np.asarray(y); t=np.asarray(timestamps)
        if s.ndim!=1 or labels.ndim!=1 or t.ndim!=1 or not (len(s)==len(labels)==len(t)) or len(s)<20:
            raise AdapterContractError("OOF_SCORE_CALIBRATION_VECTOR_SHAPE_OR_SIZE_INVALID")
        if not np.isfinite(s).all(): raise AdapterContractError("OOF_DECISION_SCORES_NONFINITE")
        if not np.isfinite(labels.astype(float)).all() or not set(np.unique(labels).tolist()).issubset({0,1}):
            raise AdapterContractError("OOF_SCORE_CALIBRATION_LABELS_INVALID")
        if set(np.unique(labels).tolist())!={0,1}: raise AdapterContractError("OOF_SCORE_CALIBRATION_REQUIRES_BOTH_CLASSES")
        if not np.isfinite(c) or c<=0: raise AdapterContractError("OOF_SCORE_CALIBRATION_C_INVALID")
        try:
            order=np.argsort(t,kind="stable")
            if not np.array_equal(order,np.arange(len(t))): raise AdapterContractError("OOF_SCORE_TIMESTAMPS_NOT_STRICTLY_CHRONOLOGICAL")
            if len(np.unique(t))!=len(t): raise AdapterContractError("OOF_SCORE_TIMESTAMPS_DUPLICATED")
        except TypeError as exc:
            raise AdapterContractError("OOF_SCORE_TIMESTAMPS_NOT_COMPARABLE") from exc
        self.model=Pipeline([("scale",StandardScaler()),("platt",LogisticRegression(C=float(c),solver="lbfgs",max_iter=2000,random_state=42))])
        self.model.fit(s.reshape(-1,1),labels.astype(int))
        self.fitted_start=str(t[0]); self.fitted_end=str(t[-1])
        return self

    def predict(self, scores: Sequence[float]) -> np.ndarray:
        if self.model is None: raise AdapterContractError("SCORE_CALIBRATOR_NOT_FIT")
        s=np.asarray(scores,dtype=float)
        if s.ndim!=1 or not np.isfinite(s).all(): raise AdapterContractError("PREDICTION_SCORES_INVALID")
        p=self.model.predict_proba(s.reshape(-1,1))[:,1]
        if not np.isfinite(p).all() or np.any((p<0)|(p>1)): raise AdapterContractError("CALIBRATED_PROBABILITIES_INVALID")
        return p
