"""Leakage-conscious logistic probability adapter for prediction research.

This module is code-only until the independent authorization bundle and data
preflight explicitly permit fitting. It never loads market data or accesses holdout.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class AdapterContractError(ValueError):
    pass


@dataclass
class LogisticProbabilityAdapter:
    """Train-only preprocessing and logistic probability estimator.

    Calibration is deliberately not implicit: the caller must supply probabilities
    generated from inner chronological out-of-fold predictions to any separate
    calibration procedure. This adapter itself performs no calibration or splitting.
    """

    c: float = 1.0
    max_iter: int = 2000
    random_state: int = 42
    model: Pipeline | None = None

    def fit(self, x_train: Sequence[Sequence[float]], y_train: Sequence[int]):
        x = np.asarray(x_train, dtype=float)
        y = np.asarray(y_train)
        self._validate_xy(x, y, "training")
        if set(np.unique(y).tolist()) != {0, 1}:
            raise AdapterContractError("TRAINING_LABELS_MUST_CONTAIN_BOTH_CLASSES")
        if self.c <= 0 or not np.isfinite(self.c):
            raise AdapterContractError("C_MUST_BE_FINITE_POSITIVE")
        self.model = Pipeline([
            ("scale", StandardScaler()),
            ("logit", LogisticRegression(
                penalty="l2", C=float(self.c), solver="lbfgs",
                max_iter=int(self.max_iter), random_state=int(self.random_state),
            )),
        ])
        self.model.fit(x, y.astype(int))
        return self

    @staticmethod
    def _validate_xy(x: np.ndarray, y: np.ndarray, label: str) -> None:
        if x.ndim != 2 or y.ndim != 1 or len(x) != len(y) or len(y) == 0:
            raise AdapterContractError(f"{label.upper()}_SHAPE_INVALID")
        if not np.isfinite(x).all():
            raise AdapterContractError(f"{label.upper()}_FEATURES_NONFINITE")
        if not np.isfinite(y.astype(float)).all() or not set(np.unique(y).tolist()).issubset({0, 1}):
            raise AdapterContractError(f"{label.upper()}_LABELS_INVALID")

    def predict_proba(self, x_test: Sequence[Sequence[float]]) -> np.ndarray:
        if self.model is None:
            raise AdapterContractError("MODEL_NOT_FIT")
        x = np.asarray(x_test, dtype=float)
        if x.ndim != 2 or x.shape[1] != self.model.n_features_in_:
            raise AdapterContractError("TEST_FEATURE_SHAPE_INVALID")
        if not np.isfinite(x).all():
            raise AdapterContractError("TEST_FEATURES_NONFINITE")
        p = np.asarray(self.model.predict_proba(x)[:, 1], dtype=float)
        if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
            raise AdapterContractError("PREDICTED_PROBABILITIES_INVALID")
        return p

    def predict_class(self, x_test: Sequence[Sequence[float]], threshold: float = 0.5) -> np.ndarray:
        if not np.isfinite(threshold) or not 0 < threshold < 1:
            raise AdapterContractError("THRESHOLD_MUST_BE_STRICTLY_BETWEEN_ZERO_AND_ONE")
        return (self.predict_proba(x_test) >= threshold).astype(int)


def binary_log_loss(y_true: Sequence[int], probabilities: Sequence[float]) -> float:
    y = np.asarray(y_true)
    p = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or len(y) != len(p) or len(y) == 0:
        raise AdapterContractError("LOGLOSS_SHAPE_INVALID")
    if not set(np.unique(y).tolist()).issubset({0, 1}):
        raise AdapterContractError("LOGLOSS_LABELS_INVALID")
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise AdapterContractError("LOGLOSS_PROBABILITIES_INVALID")
    return float(log_loss(y.astype(int), np.clip(p, 1e-15, 1 - 1e-15), labels=[0, 1]))
