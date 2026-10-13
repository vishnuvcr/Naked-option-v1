"""Developer-tested PM0001 fold fitter; array-only and fail-closed.

This component does not load market data, select configurations, access holdout,
or authorize fitting. A caller must pass an explicitly eligible config/fold and
verified, source-pinned feature samples. All preprocessing is fit within each
training fold; calibration uses only chronological inner OOF predictions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.metrics import average_precision_score, balanced_accuracy_score, brier_score_loss, log_loss, roc_auc_score

from prediction_logistic_adapter_r3 import LogisticProbabilityAdapter
from prediction_logistic_calibration_r3 import PlattCalibrator, chronological_inner_oof


class PM0001ExecutionError(ValueError):
    """Frozen PM0001 execution contract failed."""


@dataclass(frozen=True)
class PM0001FoldResult:
    fold_id: str
    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    y_validation: tuple[int, ...]
    probabilities: tuple[float, ...]
    baseline_log_loss: float
    candidate_log_loss: float
    log_loss_improvement: float
    brier_score: float
    balanced_accuracy: float
    roc_auc: float
    average_precision: float
    train_positive_support: int
    train_negative_support: int
    validation_positive_support: int
    validation_negative_support: int
    oof_rows: int
    model_fitting_performed: bool = True
    holdout_accessed: bool = False


def _array_inputs(x, y, decision_positions, endpoint_positions):
    X = np.asarray(x, dtype=float)
    labels = np.asarray(y)
    decision = np.asarray(decision_positions)
    endpoint = np.asarray(endpoint_positions)
    if (X.ndim != 2 or labels.ndim != 1 or decision.ndim != 1 or endpoint.ndim != 1
            or not (len(X) == len(labels) == len(decision) == len(endpoint))):
        raise PM0001ExecutionError("INPUT_SHAPE_MISMATCH")
    if len(labels) == 0 or not np.isfinite(X).all():
        raise PM0001ExecutionError("EMPTY_OR_NONFINITE_FEATURE_MATRIX")
    if not np.isfinite(labels.astype(float)).all() or not np.isin(labels, [0, 1]).all():
        raise PM0001ExecutionError("BINARY_LABELS_REQUIRED")
    if not np.isfinite(decision.astype(float)).all() or not np.isfinite(endpoint.astype(float)).all():
        raise PM0001ExecutionError("SESSION_INDICES_NONFINITE")
    if np.any(decision != decision.astype(int)) or np.any(endpoint != endpoint.astype(int)):
        raise PM0001ExecutionError("SESSION_INDICES_MUST_BE_INTEGERS")
    decision, endpoint = decision.astype(int), endpoint.astype(int)
    if np.any(endpoint < decision):
        raise PM0001ExecutionError("TARGET_ENDPOINT_PRECEDES_DECISION")
    if np.any(np.diff(decision) < 0):
        raise PM0001ExecutionError("DECISION_ROWS_NOT_CHRONOLOGICAL")
    return X, labels.astype(int), decision, endpoint


def fit_pm0001_outer_fold(
    x: Sequence[Sequence[float]],
    y: Sequence[int],
    decision_session_positions: Sequence[int],
    target_endpoint_session_positions: Sequence[int],
    *,
    fold_id: str,
    validation_start_session: int,
    validation_end_session_exclusive: int,
    purge_sessions: int,
    embargo_sessions: int,
    c: float,
    min_outer_train_rows: int,
    min_outer_validation_rows: int,
    min_inner_train_rows: int,
    min_inner_validation_rows: int,
) -> PM0001FoldResult:
    """Fit one registered PM0001 fold after its caller has passed all gates.

    The input arrays must contain only the frozen label/config sample rows in
    decision-time order. No random split or test-fold-driven tuning is performed.
    """
    X, labels, decision, endpoint = _array_inputs(
        x, y, decision_session_positions, target_endpoint_session_positions
    )
    if not fold_id or not fold_id.startswith("F"):
        raise PM0001ExecutionError("FOLD_ID_REQUIRED")
    if validation_start_session < 1 or validation_end_session_exclusive <= validation_start_session:
        raise PM0001ExecutionError("VALIDATION_BOUNDARY_INVALID")
    if purge_sessions < 0 or embargo_sessions < 0:
        raise PM0001ExecutionError("PURGE_OR_EMBARGO_INVALID")
    if not np.isfinite(c) or c <= 0:
        raise PM0001ExecutionError("C_MUST_BE_FINITE_POSITIVE")

    train_mask = (
        (decision < validation_start_session - purge_sessions)
        & (endpoint < validation_start_session)
    )
    valid_mask = (
        (decision >= validation_start_session + embargo_sessions)
        & (decision < validation_end_session_exclusive)
        & (endpoint < validation_end_session_exclusive)
        & (endpoint >= decision)
    )
    train_idx = np.flatnonzero(train_mask)
    valid_idx = np.flatnonzero(valid_mask)
    if len(train_idx) < min_outer_train_rows:
        raise PM0001ExecutionError("OUTER_TRAIN_ROW_MINIMUM_FAILED")
    if len(valid_idx) < min_outer_validation_rows:
        raise PM0001ExecutionError("OUTER_VALIDATION_ROW_MINIMUM_FAILED")
    if set(np.unique(labels[train_idx]).tolist()) != {0, 1}:
        raise PM0001ExecutionError("OUTER_TRAIN_CLASS_SUPPORT_FAILED")
    if set(np.unique(labels[valid_idx]).tolist()) != {0, 1}:
        raise PM0001ExecutionError("OUTER_VALIDATION_CLASS_SUPPORT_FAILED")
    if np.any(endpoint[train_idx] >= validation_start_session):
        raise PM0001ExecutionError("OUTER_TRAIN_TARGET_NOT_MATURE")
    if np.any(endpoint[valid_idx] >= validation_end_session_exclusive):
        raise PM0001ExecutionError("VALIDATION_TARGET_ESCAPES_FOLD")
    if np.any(decision[train_idx] >= decision[valid_idx].min() - purge_sessions):
        raise PM0001ExecutionError("OUTER_PURGE_FAILED")

    x_train = X[train_idx]
    y_train = labels[train_idx]
    d_train = decision[train_idx]
    e_train = endpoint[train_idx]
    oof = chronological_inner_oof(
        lambda: LogisticProbabilityAdapter(c=float(c), random_state=2026101208),
        x_train, y_train, d_train, purge_sessions, min_inner_train_rows,
        min_inner_validation_rows,
        target_endpoint_session_positions=e_train,
        embargo_sessions=embargo_sessions,
    )
    oof_prob = np.concatenate([np.asarray(f["probabilities"], dtype=float) for f in oof])
    oof_y = np.concatenate([np.asarray(f["labels"], dtype=int) for f in oof])
    if len(oof_prob) < 20 or set(np.unique(oof_y).tolist()) != {0, 1}:
        raise PM0001ExecutionError("INNER_OOF_CALIBRATION_SUPPORT_FAILED")
    calibrator = PlattCalibrator().fit(oof_prob, oof_y)

    final_model = LogisticProbabilityAdapter(c=float(c), random_state=2026101208)
    final_model.fit(x_train, y_train)
    raw_probability = final_model.predict_proba(X[valid_idx])
    probability = calibrator.predict(raw_probability)
    if len(probability) != len(valid_idx) or not np.isfinite(probability).all():
        raise PM0001ExecutionError("FINAL_CALIBRATED_PROBABILITY_INVALID")
    probability = np.clip(probability, 1e-15, 1 - 1e-15)
    validation_y = labels[valid_idx]
    prevalence = (float(y_train.sum()) + 0.5) / (len(y_train) + 1.0)
    baseline = np.full(len(valid_idx), prevalence, dtype=float)
    candidate_loss = float(log_loss(validation_y, probability, labels=[0, 1]))
    baseline_loss = float(log_loss(validation_y, baseline, labels=[0, 1]))
    return PM0001FoldResult(
        fold_id=fold_id,
        train_indices=tuple(map(int, train_idx)),
        validation_indices=tuple(map(int, valid_idx)),
        y_validation=tuple(map(int, validation_y)),
        probabilities=tuple(map(float, probability)),
        baseline_log_loss=baseline_loss,
        candidate_log_loss=candidate_loss,
        log_loss_improvement=baseline_loss - candidate_loss,
        brier_score=float(brier_score_loss(validation_y, probability)),
        balanced_accuracy=float(balanced_accuracy_score(validation_y, probability >= 0.5)),
        roc_auc=float(roc_auc_score(validation_y, probability)),
        average_precision=float(average_precision_score(validation_y, probability)),
        train_positive_support=int(y_train.sum()),
        train_negative_support=int(len(y_train) - y_train.sum()),
        validation_positive_support=int(validation_y.sum()),
        validation_negative_support=int(len(validation_y) - validation_y.sum()),
        oof_rows=int(len(oof_prob)),
    )
