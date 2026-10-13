"""Developer-tested PM0001 rolling-refit fold fitter; array-only and fail-closed.

This component does not load market data, select configurations, access holdout,
or authorize fitting. A caller must pass explicitly eligible config/fold samples
and verified source pins. It refits every 20 exchange sessions as the frozen
configuration requires. Scaling and probability calibration are rebuilt using
only observations and target labels available at each refit cutoff.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.metrics import average_precision_score, balanced_accuracy_score, brier_score_loss, log_loss, roc_auc_score

from prediction_logistic_adapter_r3 import LogisticProbabilityAdapter
from prediction_logistic_calibration_r3 import PlattCalibrator, chronological_inner_oof
from prediction_statistics import calibration_intercept_slope


class PM0001ExecutionError(ValueError):
    """Frozen PM0001 execution contract failed."""


@dataclass(frozen=True)
class PM0001FoldResult:
    fold_id: str
    train_indices: tuple[int, ...]  # first refit's training rows
    final_train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    y_validation: tuple[int, ...]
    probabilities: tuple[float, ...]
    baseline_probabilities: tuple[float, ...]
    baseline_log_loss: float
    candidate_log_loss: float
    log_loss_improvement: float
    brier_score: float
    balanced_accuracy: float
    roc_auc: float
    average_precision: float
    calibration_intercept: float | None
    calibration_slope: float | None
    calibration_status: str
    train_positive_support: int
    train_negative_support: int
    validation_positive_support: int
    validation_negative_support: int
    oof_rows: int
    refit_count: int
    refit_cutoff_sessions: tuple[int, ...]
    refit_training_indices: tuple[tuple[int, ...], ...]
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


def _require_class_support(labels: np.ndarray, indices: Sequence[int], minimum_each: int, code: str) -> None:
    selected = labels[np.asarray(indices, dtype=int)]
    positive = int(np.sum(selected == 1))
    negative = int(np.sum(selected == 0))
    if positive < minimum_each or negative < minimum_each:
        raise PM0001ExecutionError(f"{code}:positive={positive}:negative={negative}:minimum_each={minimum_each}")


def _precheck_inner_oof_support(
    labels: np.ndarray, decision: np.ndarray, endpoint: np.ndarray, *,
    purge_sessions: int, embargo_sessions: int, min_train_rows: int,
    min_validation_rows: int, min_class_support_each: int,
) -> None:
    """Preflight every frozen inner fold before fitting any estimator."""
    unique = np.unique(decision)
    if len(unique) < 10:
        raise PM0001ExecutionError("INNER_OOF_TOO_FEW_UNIQUE_SESSIONS")
    n = len(unique)
    intervals = [(int(n * .40), int(n * .60)), (int(n * .60), int(n * .80)), (int(n * .80), n)]
    for fold_number, (start, end) in enumerate(intervals, 1):
        if end <= start:
            raise PM0001ExecutionError(f"INNER_OOF_FOLD_{fold_number}_EMPTY")
        valid_sessions = unique[start:end]
        first_valid = int(valid_sessions[0])
        last_valid_exclusive = int(valid_sessions[-1]) + 1
        train_mask = (decision < first_valid - purge_sessions) & (endpoint < first_valid)
        valid_mask = (
            np.isin(decision, valid_sessions)
            & (decision >= first_valid + embargo_sessions)
            & (endpoint < last_valid_exclusive)
        )
        tr = np.flatnonzero(train_mask)
        va = np.flatnonzero(valid_mask)
        if len(tr) < min_train_rows:
            raise PM0001ExecutionError(f"INNER_OOF_FOLD_{fold_number}_MIN_TRAIN_ROWS_FAILED")
        if len(va) < min_validation_rows:
            raise PM0001ExecutionError(f"INNER_OOF_FOLD_{fold_number}_MIN_VALIDATION_ROWS_FAILED")
        _require_class_support(labels, tr, min_class_support_each, f"INNER_OOF_FOLD_{fold_number}_TRAIN_CLASS_SUPPORT_FAILED")
        _require_class_support(labels, va, min_class_support_each, f"INNER_OOF_FOLD_{fold_number}_VALIDATION_CLASS_SUPPORT_FAILED")
        if np.any(endpoint[tr] >= first_valid):
            raise PM0001ExecutionError(f"INNER_OOF_FOLD_{fold_number}_IMMATURE_TRAINING_TARGET")


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
    min_outer_train_class_support: int,
    min_outer_validation_class_support: int,
    min_inner_class_support: int,
    refit_cadence_sessions: int = 20,
) -> PM0001FoldResult:
    """Fit one registered fold with rolling refits every 20 exchange sessions.

    The first refit trains only on targets mature before the outer validation start.
    Later refits may use prior validation-period observations only after their labels
    mature, and refit every transformation/calibrator from scratch. The outer fold
    is never used to tune C, calibration, thresholds, or other hyperparameters.
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
    if isinstance(refit_cadence_sessions, bool) or refit_cadence_sessions < 1:
        raise PM0001ExecutionError("REFIT_CADENCE_INVALID")
    if not np.isfinite(c) or c <= 0:
        raise PM0001ExecutionError("C_MUST_BE_FINITE_POSITIVE")

    all_validation_mask = (
        (decision >= validation_start_session + embargo_sessions)
        & (decision < validation_end_session_exclusive)
        & (endpoint < validation_end_session_exclusive)
        & (endpoint >= decision)
    )
    eligible_validation_indices = np.flatnonzero(all_validation_mask)
    if len(eligible_validation_indices) < min_outer_validation_rows:
        raise PM0001ExecutionError("OUTER_VALIDATION_ROW_MINIMUM_FAILED")
    _require_class_support(labels, eligible_validation_indices, min_outer_validation_class_support,
                          "OUTER_VALIDATION_CLASS_SUPPORT_FAILED")

    scored_indices: list[int] = []
    scored_probabilities: list[float] = []
    scored_baselines: list[float] = []
    refit_cutoffs: list[int] = []
    refit_training_indices: list[tuple[int, ...]] = []
    total_oof_rows = 0

    first_cutoff = validation_start_session
    last_cutoff = validation_end_session_exclusive
    # Preflight every refit cutoff before fitting the first estimator. If a later
    # cutoff lacks support, the entire config/fold is blocked without partial fitting.
    for block_start in range(first_cutoff, last_cutoff, refit_cadence_sessions):
        block_end = min(block_start + refit_cadence_sessions, last_cutoff)
        train_mask = (decision < block_start - purge_sessions) & (endpoint < block_start)
        block_mask = (
            (decision >= block_start) & (decision < block_end)
            & (endpoint < validation_end_session_exclusive) & (endpoint >= decision)
        )
        if block_start == validation_start_session:
            block_mask &= decision >= validation_start_session + embargo_sessions
        train_idx = np.flatnonzero(train_mask)
        block_idx = np.flatnonzero(block_mask)
        if not len(block_idx):
            continue
        if len(train_idx) < min_outer_train_rows:
            raise PM0001ExecutionError(f"REFIT_{block_start}_OUTER_TRAIN_ROW_MINIMUM_FAILED")
        _require_class_support(labels, train_idx, min_outer_train_class_support,
                              f"REFIT_{block_start}_OUTER_TRAIN_CLASS_SUPPORT_FAILED")
        if np.any(endpoint[train_idx] >= block_start):
            raise PM0001ExecutionError(f"REFIT_{block_start}_TRAIN_TARGET_NOT_MATURE")
        if np.any(decision[train_idx] >= block_start - purge_sessions):
            raise PM0001ExecutionError(f"REFIT_{block_start}_PURGE_FAILED")
        _precheck_inner_oof_support(
            labels[train_idx], decision[train_idx], endpoint[train_idx],
            purge_sessions=purge_sessions, embargo_sessions=embargo_sessions,
            min_train_rows=min_inner_train_rows,
            min_validation_rows=min_inner_validation_rows,
            min_class_support_each=min_inner_class_support,
        )

    for block_start in range(first_cutoff, last_cutoff, refit_cadence_sessions):
        block_end = min(block_start + refit_cadence_sessions, last_cutoff)
        train_mask = (
            (decision < block_start - purge_sessions)
            & (endpoint < block_start)
        )
        block_mask = (
            (decision >= block_start)
            & (decision < block_end)
            & (endpoint < validation_end_session_exclusive)
            & (endpoint >= decision)
        )
        if block_start == validation_start_session:
            block_mask &= decision >= validation_start_session + embargo_sessions
        train_idx = np.flatnonzero(train_mask)
        block_idx = np.flatnonzero(block_mask)
        if not len(block_idx):
            continue
        if len(train_idx) < min_outer_train_rows:
            raise PM0001ExecutionError(f"REFIT_{block_start}_OUTER_TRAIN_ROW_MINIMUM_FAILED")
        _require_class_support(labels, train_idx, min_outer_train_class_support,
                              f"REFIT_{block_start}_OUTER_TRAIN_CLASS_SUPPORT_FAILED")
        if np.any(endpoint[train_idx] >= block_start):
            raise PM0001ExecutionError(f"REFIT_{block_start}_TRAIN_TARGET_NOT_MATURE")
        if np.any(decision[train_idx] >= block_start - purge_sessions):
            raise PM0001ExecutionError(f"REFIT_{block_start}_PURGE_FAILED")
        if np.any(endpoint[block_idx] >= validation_end_session_exclusive):
            raise PM0001ExecutionError("VALIDATION_TARGET_ESCAPES_FOLD")

        x_train = X[train_idx]
        y_train = labels[train_idx]
        d_train = decision[train_idx]
        e_train = endpoint[train_idx]
        _precheck_inner_oof_support(
            y_train, d_train, e_train, purge_sessions=purge_sessions,
            embargo_sessions=embargo_sessions, min_train_rows=min_inner_train_rows,
            min_validation_rows=min_inner_validation_rows,
            min_class_support_each=min_inner_class_support,
        )
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
            raise PM0001ExecutionError(f"REFIT_{block_start}_INNER_OOF_CALIBRATION_SUPPORT_FAILED")
        calibrator = PlattCalibrator().fit(oof_prob, oof_y)

        final_model = LogisticProbabilityAdapter(c=float(c), random_state=2026101208)
        final_model.fit(x_train, y_train)
        raw_probability = final_model.predict_proba(X[block_idx])
        probability = calibrator.predict(raw_probability)
        if len(probability) != len(block_idx) or not np.isfinite(probability).all():
            raise PM0001ExecutionError("FINAL_CALIBRATED_PROBABILITY_INVALID")
        probability = np.clip(probability, 1e-15, 1 - 1e-15)
        prevalence = (float(y_train.sum()) + 0.5) / (len(y_train) + 1.0)
        scored_indices.extend(map(int, block_idx))
        scored_probabilities.extend(map(float, probability))
        scored_baselines.extend([float(prevalence)] * len(block_idx))
        refit_cutoffs.append(int(block_start))
        refit_training_indices.append(tuple(map(int, train_idx)))
        total_oof_rows += int(len(oof_prob))

    if set(scored_indices) != set(map(int, eligible_validation_indices)):
        raise PM0001ExecutionError("OUTER_VALIDATION_ROW_ACCOUNTING_MISMATCH")
    if len(set(scored_indices)) != len(scored_indices):
        raise PM0001ExecutionError("DUPLICATE_VALIDATION_PREDICTION")
    order = np.argsort(np.asarray(scored_indices), kind="stable")
    scored_indices_arr = np.asarray(scored_indices, dtype=int)[order]
    probability_arr = np.asarray(scored_probabilities, dtype=float)[order]
    baseline_arr = np.asarray(scored_baselines, dtype=float)[order]
    validation_y = labels[scored_indices_arr]
    if set(np.unique(validation_y).tolist()) != {0, 1}:
        raise PM0001ExecutionError("OUTER_VALIDATION_CLASS_SUPPORT_FAILED")
    if np.any(endpoint[scored_indices_arr] >= validation_end_session_exclusive):
        raise PM0001ExecutionError("VALIDATION_TARGET_ESCAPES_FOLD")

    baseline_loss = float(log_loss(validation_y, baseline_arr, labels=[0, 1]))
    candidate_loss = float(log_loss(validation_y, probability_arr, labels=[0, 1]))
    calibration = calibration_intercept_slope(validation_y.tolist(), probability_arr.tolist())
    calibration_status = str(calibration.get("status", "UNKNOWN"))
    calibration_intercept = float(calibration["intercept"]) if calibration_status == "CONVERGED" else None
    calibration_slope = float(calibration["slope"]) if calibration_status == "CONVERGED" else None
    first_train = refit_training_indices[0]
    final_train = refit_training_indices[-1]
    final_y = labels[np.asarray(final_train, dtype=int)]
    return PM0001FoldResult(
        fold_id=fold_id,
        train_indices=first_train,
        final_train_indices=final_train,
        validation_indices=tuple(map(int, scored_indices_arr)),
        y_validation=tuple(map(int, validation_y)),
        probabilities=tuple(map(float, probability_arr)),
        baseline_probabilities=tuple(map(float, baseline_arr)),
        baseline_log_loss=baseline_loss,
        candidate_log_loss=candidate_loss,
        log_loss_improvement=baseline_loss - candidate_loss,
        brier_score=float(brier_score_loss(validation_y, probability_arr)),
        balanced_accuracy=float(balanced_accuracy_score(validation_y, probability_arr >= 0.5)),
        roc_auc=float(roc_auc_score(validation_y, probability_arr)),
        average_precision=float(average_precision_score(validation_y, probability_arr)),
        calibration_intercept=calibration_intercept,
        calibration_slope=calibration_slope,
        calibration_status=calibration_status,
        train_positive_support=int(final_y.sum()),
        train_negative_support=int(len(final_y) - final_y.sum()),
        validation_positive_support=int(validation_y.sum()),
        validation_negative_support=int(len(validation_y) - validation_y.sum()),
        oof_rows=total_oof_rows,
        refit_count=len(refit_cutoffs),
        refit_cutoff_sessions=tuple(refit_cutoffs),
        refit_training_indices=tuple(refit_training_indices),
    )
