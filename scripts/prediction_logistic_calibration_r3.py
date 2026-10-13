"""Chronological inner-OOF probability calibration utilities (no data loading)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss


class CalibrationContractError(ValueError):
    pass


@dataclass
class PlattCalibrator:
    """Logistic calibration trained only on already-generated inner OOF scores."""
    model: LogisticRegression | None = None

    def fit(self, oof_probabilities: Sequence[float], oof_labels: Sequence[int]):
        p = np.asarray(oof_probabilities, dtype=float)
        y = np.asarray(oof_labels)
        if p.ndim != 1 or y.ndim != 1 or len(p) != len(y) or len(p) < 20:
            raise CalibrationContractError("OOF_CALIBRATION_SHAPE_OR_SAMPLE_SIZE_INVALID")
        if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
            raise CalibrationContractError("OOF_CALIBRATION_PROBABILITIES_INVALID")
        if not np.isfinite(y.astype(float)).all() or set(np.unique(y).tolist()) != {0, 1}:
            raise CalibrationContractError("OOF_CALIBRATION_LABELS_MUST_HAVE_BOTH_CLASSES")
        z = np.log(np.clip(p, 1e-6, 1-1e-6) / (1 - np.clip(p, 1e-6, 1-1e-6))).reshape(-1, 1)
        self.model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000, random_state=42)
        self.model.fit(z, y.astype(int))
        return self

    def predict(self, probabilities: Sequence[float]) -> np.ndarray:
        if self.model is None:
            raise CalibrationContractError("CALIBRATOR_NOT_FIT")
        p = np.asarray(probabilities, dtype=float)
        if p.ndim != 1 or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
            raise CalibrationContractError("CALIBRATION_INPUT_PROBABILITIES_INVALID")
        z = np.log(np.clip(p, 1e-6, 1-1e-6) / (1 - np.clip(p, 1e-6, 1-1e-6))).reshape(-1, 1)
        out = self.model.predict_proba(z)[:, 1]
        if not np.isfinite(out).all() or np.any((out < 0) | (out > 1)):
            raise CalibrationContractError("CALIBRATED_PROBABILITIES_INVALID")
        return out


def chronological_inner_oof(estimator_factory, x, y, session_positions, purge_sessions: int,
                            min_train_rows: int, min_validation_rows: int, *,
                            target_endpoint_session_positions=None, embargo_sessions: int = 0):
    """Create three expanding OOF folds with frozen session quantiles.

    Rows must be ordered by decision session. Every training target must have matured
    strictly before the validation boundary. Purge is applied to training decisions;
    embargo removes the initial validation sessions. Callers must supply endpoint
    session indices for a fail-closed maturity check; omission is rejected.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y)
    s = np.asarray(session_positions)
    if target_endpoint_session_positions is None:
        raise CalibrationContractError("TARGET_ENDPOINT_SESSION_POSITIONS_REQUIRED")
    endpoint = np.asarray(target_endpoint_session_positions)
    if (x.ndim != 2 or y.ndim != 1 or s.ndim != 1 or endpoint.ndim != 1
            or len(x) != len(y) or len(y) != len(s) or len(s) != len(endpoint)):
        raise CalibrationContractError("INNER_OOF_INPUT_SHAPE_INVALID")
    if (not np.isfinite(x).all() or not np.isfinite(y.astype(float)).all()
            or not np.isfinite(s.astype(float)).all() or not np.isfinite(endpoint.astype(float)).all()):
        raise CalibrationContractError("INNER_OOF_INPUT_NONFINITE")
    if (not np.isin(y, [0, 1]).all() or set(np.unique(y).tolist()) != {0, 1}
            or np.any(s != s.astype(int)) or np.any(endpoint != endpoint.astype(int))):
        raise CalibrationContractError("INNER_OOF_LABEL_OR_SESSION_INDEX_INVALID")
    s = s.astype(int)
    endpoint = endpoint.astype(int)
    if np.any(endpoint < s):
        raise CalibrationContractError("TARGET_ENDPOINT_PRECEDES_DECISION")
    if (purge_sessions < 0 or embargo_sessions < 0
            or min_train_rows < 1 or min_validation_rows < 1):
        raise CalibrationContractError("INNER_OOF_GATE_ARGUMENT_INVALID")
    if np.any(np.diff(s) < 0):
        raise CalibrationContractError("INNER_OOF_DECISION_SESSIONS_NOT_CHRONOLOGICAL")
    unique = np.unique(s)
    if len(unique) < 10:
        raise CalibrationContractError("INNER_OOF_TOO_FEW_UNIQUE_SESSIONS")
    n = len(unique)
    intervals = [(int(n*.40), int(n*.60)), (int(n*.60), int(n*.80)), (int(n*.80), n)]
    outputs = []
    for fold, (start, end) in enumerate(intervals, 1):
        if end <= start:
            raise CalibrationContractError("INNER_OOF_EMPTY_VALIDATION_INTERVAL")
        valid_sessions = unique[start:end]
        first_valid = int(valid_sessions[0])
        last_valid_exclusive = int(valid_sessions[-1]) + 1
        train_mask = (s < (first_valid - purge_sessions)) & (endpoint < first_valid)
        valid_mask = np.isin(s, valid_sessions) & (s >= first_valid + embargo_sessions) & (endpoint < last_valid_exclusive)
        tr = np.flatnonzero(train_mask)
        va = np.flatnonzero(valid_mask)
        if len(tr) < min_train_rows or len(va) < min_validation_rows:
            raise CalibrationContractError(f"INNER_OOF_FOLD_{fold}_MINIMUM_ROWS_FAILED")
        if len(tr) and len(va):
            if not (s[tr].max() < s[va].min() - purge_sessions):
                raise CalibrationContractError(f"INNER_OOF_FOLD_{fold}_PURGE_FAILED")
            if np.any(endpoint[tr] >= first_valid):
                raise CalibrationContractError(f"INNER_OOF_FOLD_{fold}_IMMATURE_TRAINING_TARGET")
        if set(np.unique(y[tr]).tolist()) != {0, 1}:
            raise CalibrationContractError(f"INNER_OOF_FOLD_{fold}_TRAINING_CLASS_SUPPORT_FAILED")
        model = estimator_factory()
        model.fit(x[tr], y[tr].astype(int))
        prob = model.predict_proba(x[va])[:, 1]
        if not np.isfinite(prob).all() or np.any((prob < 0) | (prob > 1)):
            raise CalibrationContractError(f"INNER_OOF_FOLD_{fold}_PROBABILITY_INVALID")
        outputs.append({"fold": fold, "train_indices": tr, "validation_indices": va,
                        "probabilities": prob, "labels": y[va].astype(int),
                        "validation_start_session": first_valid,
                        "validation_end_session_exclusive": last_valid_exclusive,
                        "training_target_maturity_max_session": int(endpoint[tr].max())})
    return outputs


def oof_log_loss(folds):
    y = np.concatenate([np.asarray(f["labels"], dtype=int) for f in folds])
    p = np.concatenate([np.asarray(f["probabilities"], dtype=float) for f in folds])
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise CalibrationContractError("OOF_LOGLOSS_PROBABILITIES_INVALID")
    return float(log_loss(y, np.clip(p, 1e-15, 1-1e-15), labels=[0, 1]))
