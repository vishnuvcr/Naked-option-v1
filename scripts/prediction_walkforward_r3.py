"""Deterministic R3 expanding-window fold planning and result-row contracts.

This module performs no model fitting. It converts frozen exchange-session and target-endpoint
indices into leakage-safe split indices, enforces support minima, and validates result rows.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = ROOT / "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
LABEL_PATH = ROOT / "research/registry/PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json"
PREFLIGHT_PATH = ROOT / "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
DATASET_MANIFEST_SHA256_EXPECTED = None  # Caller must provide the full source-manifest SHA-256.

TERMINAL_STATUSES = {
    "EXECUTED_AUDITED",
    "BLOCKED_DATA",
    "BLOCKED_GATE",
    "FAILED_TECHNICAL",
    "REJECTED_EMPIRICAL",
}
METRIC_FIELDS = {
    "baseline_log_loss", "candidate_log_loss", "log_loss_improvement",
    "bootstrap_ci_lower", "bootstrap_ci_upper", "raw_p_value",
    "by_adjusted_p_value", "class_prior_baseline_log_loss",
    "previous_sign_baseline_log_loss", "brier_score", "balanced_accuracy",
    "roc_auc", "average_precision", "calibration_intercept", "calibration_slope",
}


class WalkForwardContractError(ValueError):
    """Frozen chronological execution contract failed."""


@dataclass(frozen=True)
class FoldIndices:
    fold_id: str
    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    validation_start_index: int
    validation_end_index_exclusive: int
    purge_sessions: int
    embargo_sessions: int
    counts: dict[str, int]


@dataclass(frozen=True)
class InnerFoldDescriptor:
    fold_id: str
    validation_start_position: int
    validation_end_position_exclusive: int
    validation_start_session_index: int
    validation_end_session_index_exclusive: int
    validation_start_date: str
    validation_end_date: str


def _get(row: Any, key: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(key)
    return getattr(row, key, None)


def _as_index(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise WalkForwardContractError(f"INVALID_NONNEGATIVE_INDEX:{name}:{value}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise WalkForwardContractError(f"REQUIRED_FILE_MISSING:{path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WalkForwardContractError(f"INVALID_JSON:{path.relative_to(ROOT)}") from exc
    if not isinstance(value, dict):
        raise WalkForwardContractError(f"JSON_TOP_LEVEL_NOT_OBJECT:{path.relative_to(ROOT)}")
    return value


def validate_session_calendar(session_dates: Sequence[str]) -> list[str]:
    dates = list(session_dates)
    if not dates:
        raise WalkForwardContractError("EMPTY_SESSION_CALENDAR")
    for i, value in enumerate(dates):
        try:
            date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise WalkForwardContractError(f"INVALID_SESSION_DATE:{value}") from exc
        if i and dates[i - 1] >= value:
            raise WalkForwardContractError("SESSION_DATES_MUST_BE_STRICTLY_INCREASING_AND_UNIQUE")
    return dates


def validate_outer_windows(windows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    if len(windows) != 8:
        raise WalkForwardContractError(f"EXPECTED_EIGHT_OUTER_WINDOWS:{len(windows)}")
    out: list[dict[str, str]] = []
    expected_ids = [f"F{i:02d}" for i in range(1, 9)]
    for expected_id, row in zip(expected_ids, windows):
        fold_id = row.get("id")
        start = row.get("start")
        end = row.get("end_inclusive")
        if fold_id != expected_id:
            raise WalkForwardContractError(f"OUTER_FOLD_ID_OR_ORDER_CHANGED:{expected_id}:{fold_id}")
        try:
            start_day = date.fromisoformat(str(start))
            end_day = date.fromisoformat(str(end))
        except ValueError as exc:
            raise WalkForwardContractError(f"INVALID_OUTER_WINDOW_DATE:{fold_id}") from exc
        if start_day > end_day:
            raise WalkForwardContractError(f"OUTER_WINDOW_START_AFTER_END:{fold_id}")
        if out and date.fromisoformat(out[-1]["end_inclusive"]) >= start_day:
            raise WalkForwardContractError(f"OUTER_WINDOWS_OVERLAP_OR_UNSORTED:{fold_id}")
        out.append({"id": fold_id, "start": str(start), "end_inclusive": str(end)})
    return out


def session_window_positions(session_dates: Sequence[str], start_date: str, end_date: str) -> tuple[int, int]:
    """Return [start, end-exclusive) positions on the frozen session index."""
    sessions = validate_session_calendar(session_dates)
    start_pos = next((i for i, d in enumerate(sessions) if d >= start_date), None)
    eligible = [i for i, d in enumerate(sessions) if start_date <= d <= end_date]
    if start_pos is None or not eligible:
        raise WalkForwardContractError(f"OUTER_WINDOW_HAS_NO_ELIGIBLE_SESSIONS:{start_date}:{end_date}")
    start_pos, end_pos_exclusive = eligible[0], eligible[-1] + 1
    if sessions[start_pos] > end_date or sessions[end_pos_exclusive - 1] < start_date:
        raise WalkForwardContractError("OUTER_WINDOW_SESSION_BOUNDARY_INVALID")
    return start_pos, end_pos_exclusive


def build_fold_indices(
    samples: Sequence[Any],
    session_dates: Sequence[str],
    *,
    fold_id: str,
    validation_start_position: int,
    validation_end_position_exclusive: int,
    purge_sessions: int,
    embargo_sessions: int,
) -> FoldIndices:
    """Build leakage-safe train/validation indices for a session-index window.

    Validation excludes the first embargo sessions and scores only labels whose endpoints
    remain inside the same window. Training requires target maturity strictly before the
    window and excludes the last purge sessions before validation.
    """
    sessions = validate_session_calendar(session_dates)
    if not re.fullmatch(r"F0[1-8]", fold_id):
        raise WalkForwardContractError(f"INVALID_FOLD_ID:{fold_id}")
    start = _as_index(validation_start_position, "validation_start_position")
    end = _as_index(validation_end_position_exclusive, "validation_end_position_exclusive")
    purge = _as_index(purge_sessions, "purge_sessions")
    embargo = _as_index(embargo_sessions, "embargo_sessions")
    if start >= end or end > len(sessions):
        raise WalkForwardContractError(f"VALIDATION_WINDOW_BOUNDS_INVALID:{start}:{end}:{len(sessions)}")
    if start + embargo >= end:
        raise WalkForwardContractError(f"EMBARGO_CONSUMES_VALIDATION_WINDOW:{fold_id}")

    train: list[int] = []
    validation: list[int] = []
    candidate_train = 0
    immature_train = 0
    purged_train = 0
    embargoed_validation = 0
    endpoint_after_validation = 0
    candidate_validation = 0

    for i, sample in enumerate(samples):
        decision_idx = _as_index(_get(sample, "decision_session_index"), "decision_session_index")
        endpoint_idx = _as_index(_get(sample, "target_endpoint_session_index"), "target_endpoint_session_index")
        if decision_idx >= len(sessions) or endpoint_idx >= len(sessions):
            raise WalkForwardContractError(f"SAMPLE_SESSION_INDEX_OUT_OF_RANGE:{i}:{decision_idx}:{endpoint_idx}")
        if endpoint_idx < decision_idx:
            raise WalkForwardContractError(f"TARGET_ENDPOINT_PRECEDES_DECISION:{i}")
        if decision_idx < start:
            candidate_train += 1
            # Endpoint maturity is a separate necessary condition; no validation target is usable for fitting.
            if endpoint_idx >= start:
                immature_train += 1
                continue
            # Purge label windows and rows within the frozen number of sessions before validation.
            if decision_idx >= start - purge:
                purged_train += 1
                continue
            train.append(i)
            continue
        if start <= decision_idx < end:
            candidate_validation += 1
            if decision_idx < start + embargo:
                embargoed_validation += 1
                continue
            if endpoint_idx < start:
                raise WalkForwardContractError(f"VALIDATION_TARGET_ENDPOINT_BEFORE_WINDOW:{i}")
            if endpoint_idx >= end:
                endpoint_after_validation += 1
                continue
            validation.append(i)

    counts = {
        "candidate_train_rows": candidate_train,
        "eligible_train_rows": len(train),
        "immature_training_targets_excluded": immature_train,
        "purged_training_rows": purged_train,
        "candidate_validation_rows": candidate_validation,
        "eligible_validation_rows": len(validation),
        "embargoed_validation_rows": embargoed_validation,
        "validation_targets_outside_window": endpoint_after_validation,
    }
    return FoldIndices(
        fold_id=fold_id,
        train_indices=tuple(train),
        validation_indices=tuple(validation),
        validation_start_index=start,
        validation_end_index_exclusive=end,
        purge_sessions=purge,
        embargo_sessions=embargo,
        counts=counts,
    )


def build_inner_fold_descriptors(
    session_dates: Sequence[str],
    *,
    outer_validation_start_position: int,
) -> tuple[InnerFoldDescriptor, ...]:
    """Frozen inner quantile splits [0.40,0.60), [0.60,0.80), [0.80,1.00)."""
    sessions = validate_session_calendar(session_dates)
    cutoff = _as_index(outer_validation_start_position, "outer_validation_start_position")
    if cutoff > len(sessions):
        raise WalkForwardContractError("OUTER_START_POSITION_OUT_OF_RANGE")
    outer_train_sessions = sessions[:cutoff]
    n = len(outer_train_sessions)
    cutpoints = [math.floor(q * n) for q in (0.40, 0.60, 0.80, 1.00)]
    folds = []
    for fold_number, (start_pos, end_pos) in enumerate(zip(cutpoints[:-1], cutpoints[1:]), start=1):
        if start_pos < 0 or end_pos <= start_pos or end_pos > n:
            raise WalkForwardContractError(f"INNER_QUANTILE_SPLIT_EMPTY_OR_INVALID:{fold_number}:{start_pos}:{end_pos}:{n}")
        global_start = start_pos
        global_end_exclusive = end_pos
        folds.append(InnerFoldDescriptor(
            fold_id=f"I{fold_number:02d}",
            validation_start_position=global_start,
            validation_end_position_exclusive=global_end_exclusive,
            validation_start_session_index=global_start,
            validation_end_session_index_exclusive=global_end_exclusive,
            validation_start_date=outer_train_sessions[start_pos],
            validation_end_date=outer_train_sessions[end_pos - 1],
        ))
    if len(folds) != 3:
        raise WalkForwardContractError("INNER_FOLD_COUNT_NOT_THREE")
    if folds[-1].validation_end_session_index_exclusive != cutoff:
        raise WalkForwardContractError("INNER_LAST_FOLD_DOES_NOT_END_AT_OUTER_CUTOFF")
    return tuple(folds)


def sample_support(
    y: Sequence[int],
    indices: Sequence[int],
    label_id: str,
    role: str,
    prereg: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the exact preregistered row and two-class support minima."""
    if label_id not in prereg.get("labels", {}):
        raise WalkForwardContractError(f"LABEL_MINIMA_NOT_REGISTERED:{label_id}")
    sample_rules = prereg.get("sample_eligibility", {})
    fitting = prereg.get("fitting_and_calibration", {})
    inner = prereg.get("chronological_validation", {}).get("inner_validation", {})
    class_rules = {
        "OUTER_TRAIN": (
            sample_rules.get("minimum_train_rows", {}).get(label_id),
            sample_rules.get("minimum_class_support_each_direction_training", {}).get(label_id),
        ),
        "OUTER_VALIDATION": (
            sample_rules.get("minimum_validation_rows", {}).get(label_id),
            sample_rules.get("minimum_class_support_each_direction_per_validation_fold", {}).get(label_id),
        ),
        "INNER_TRAIN": (
            fitting.get("minimum_inner_training_rows", {}).get(label_id),
            inner.get("class_support_each_direction_minimum", {}).get(label_id),
        ),
        "INNER_VALIDATION": (
            fitting.get("minimum_inner_validation_rows", {}).get(label_id),
            inner.get("class_support_each_direction_minimum", {}).get(label_id),
        ),
    }
    if role not in class_rules:
        raise WalkForwardContractError(f"UNKNOWN_SUPPORT_ROLE:{role}")
    min_rows, min_each_class = class_rules[role]
    if not isinstance(min_rows, int) or not isinstance(min_each_class, int):
        raise WalkForwardContractError(f"FROZEN_SUPPORT_MINIMUM_MISSING:{label_id}:{role}")
    if any(i < 0 or i >= len(y) for i in indices):
        raise WalkForwardContractError("SUPPORT_INDEX_OUT_OF_RANGE")
    selected = [y[i] for i in indices]
    if any(isinstance(v, bool) or v not in (0, 1) for v in selected):
        raise WalkForwardContractError(f"BINARY_LABELS_REQUIRED:{label_id}:{role}")
    up = sum(v == 1 for v in selected)
    down = sum(v == 0 for v in selected)
    reasons = []
    if len(selected) < min_rows:
        reasons.append("ROW_COUNT_BELOW_FROZEN_MINIMUM")
    if up < min_each_class or down < min_each_class:
        reasons.append("DIRECTION_CLASS_SUPPORT_BELOW_FROZEN_MINIMUM")
    return {
        "label_id": label_id,
        "role": role,
        "row_count": len(selected),
        "up_support": up,
        "down_support": down,
        "minimum_rows": min_rows,
        "minimum_each_direction": min_each_class,
        "passes": not reasons,
        "block_reasons": reasons,
    }


def preflight_block_reason(preflight: Mapping[str, Any], label_id: str, fold_id: str) -> str | None:
    rows = preflight.get("label_sample_support")
    if not isinstance(rows, list):
        raise WalkForwardContractError("PREFLIGHT_SAMPLE_SUPPORT_GRID_MISSING")
    matches = [r for r in rows if r.get("label_id") == label_id and r.get("fold_id") == fold_id]
    if len(matches) != 1:
        raise WalkForwardContractError(f"PREFLIGHT_CELL_MISSING_OR_DUPLICATE:{label_id}:{fold_id}:{len(matches)}")
    row = matches[0]
    if row.get("passes_frozen_data_minima") is True:
        if row.get("block_reasons") not in ([], None):
            raise WalkForwardContractError(f"PASS_PREFLIGHT_CELL_HAS_BLOCK_REASON:{label_id}:{fold_id}")
        return None
    reasons = row.get("block_reasons")
    if not isinstance(reasons, list) or not reasons:
        raise WalkForwardContractError(f"BLOCKED_PREFLIGHT_CELL_HAS_NO_REASON:{label_id}:{fold_id}")
    return ",".join(str(x) for x in reasons)


def terminal_result_row(
    *,
    config: Mapping[str, Any],
    fold_id: str,
    train_start: str,
    train_end: str,
    validation_start: str,
    validation_end: str,
    status: str,
    failure_reason: str | None,
    eligible_train_rows: int = 0,
    eligible_validation_rows: int = 0,
    train_positive_support: int = 0,
    train_negative_support: int = 0,
    validation_positive_support: int = 0,
    validation_negative_support: int = 0,
    purge_sessions: int,
    embargo_sessions: int,
    label_exclusion_count: int | None,
    feature_missingness: Mapping[str, Any] | None,
    label_target_endpoint: str | None,
    source_manifest_sha256: str,
    metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a full required row for executed, blocked, failed or rejected outcomes."""
    if status not in TERMINAL_STATUSES:
        raise WalkForwardContractError(f"UNKNOWN_TERMINAL_STATUS:{status}")
    if status == "EXECUTED_AUDITED" and failure_reason not in (None, ""):
        raise WalkForwardContractError("EXECUTED_ROW_CANNOT_HAVE_FAILURE_REASON")
    if status in {"BLOCKED_DATA", "BLOCKED_GATE", "FAILED_TECHNICAL"} and not failure_reason:
        raise WalkForwardContractError("BLOCKED_OR_FAILED_ROW_REQUIRES_FAILURE_REASON")
    if not re.fullmatch(r"[0-9a-f]{64}", source_manifest_sha256):
        raise WalkForwardContractError("SOURCE_MANIFEST_SHA256_MISSING_OR_INVALID")
    config_details = config.get("configuration") if isinstance(config.get("configuration"), Mapping) else config
    config_id = config.get("config_id")
    method_id = config.get("method_id", config_details.get("method_id"))
    label_id = config.get("label_id", config_details.get("label_id"))
    if not all(isinstance(value, str) and value for value in (config_id, method_id, label_id)):
        raise WalkForwardContractError("CONFIG_ID_METHOD_ID_OR_LABEL_ID_MISSING")
    row = {
        "config_id": config_id,
        "method_id": method_id,
        "label_id": label_id,
        "fold_id": fold_id,
        "train_start": train_start,
        "train_end": train_end,
        "validation_start": validation_start,
        "validation_end": validation_end,
        "eligible_train_rows": int(eligible_train_rows),
        "eligible_validation_rows": int(eligible_validation_rows),
        "positive_support": int(validation_positive_support),
        "negative_support": int(validation_negative_support),
        "feature_missingness": dict(feature_missingness) if feature_missingness is not None else None,
        "label_exclusion_count": label_exclusion_count,
        "baseline_log_loss": None,
        "candidate_log_loss": None,
        "log_loss_improvement": None,
        "bootstrap_ci_lower": None,
        "bootstrap_ci_upper": None,
        "raw_p_value": None,
        "by_adjusted_p_value": None,
        "terminal_status": status,
        "failure_reason": failure_reason,
        "label_target_endpoint": label_target_endpoint,
        "purge_sessions": int(purge_sessions),
        "embargo_sessions": int(embargo_sessions),
        "class_prior_baseline_log_loss": None,
        "previous_sign_baseline_log_loss": None,
        "brier_score": None,
        "balanced_accuracy": None,
        "roc_auc": None,
        "average_precision": None,
        "calibration_intercept": None,
        "calibration_slope": None,
        "observed_session_count": 0,
        "bootstrap_status": "NOT_RUN",
        "bootstrap_replicates": 0,
        "by_family_id": str(label_id),
        "source_manifest_sha256": source_manifest_sha256,
        "train_positive_support": int(train_positive_support),
        "train_negative_support": int(train_negative_support),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    if metrics:
        for key, value in metrics.items():
            if key not in row:
                raise WalkForwardContractError(f"UNREGISTERED_RESULT_METRIC:{key}")
            row[key] = value
    if status in {"BLOCKED_DATA", "BLOCKED_GATE", "FAILED_TECHNICAL"} and any(row.get(k) is not None for k in METRIC_FIELDS):
        raise WalkForwardContractError("BLOCKED_OR_FAILED_ROW_MUST_HAVE_NULL_METRICS")
    return row


def validate_result_rows(
    rows: Sequence[Mapping[str, Any]],
    expected_config_fold_pairs: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    """Validate row completeness, uniqueness, terminal states and simple metric arithmetic."""
    prereg = load_json(PREREG_PATH)
    required = set(prereg["output_and_failure_rules"]["mandatory_fields"])
    expected = set(expected_config_fold_pairs)
    if len(expected_config_fold_pairs) != len(expected):
        raise WalkForwardContractError("EXPECTED_CONFIG_FOLD_PAIRS_DUPLICATED")
    got: set[tuple[str, str]] = set()
    terminal_counts: Counter[str] = Counter()
    for position, row in enumerate(rows):
        missing = required - set(row)
        if missing:
            raise WalkForwardContractError(f"RESULT_ROW_REQUIRED_FIELDS_MISSING:{position}:{sorted(missing)}")
        config_id, fold_id = row.get("config_id"), row.get("fold_id")
        pair = (str(config_id), str(fold_id))
        if pair in got:
            raise WalkForwardContractError(f"DUPLICATE_CONFIG_FOLD_RESULT_ROW:{pair}")
        got.add(pair)
        status = row.get("terminal_status")
        if status not in TERMINAL_STATUSES:
            raise WalkForwardContractError(f"INVALID_RESULT_TERMINAL_STATUS:{position}:{status}")
        terminal_counts[str(status)] += 1
        if status in {"BLOCKED_DATA", "BLOCKED_GATE", "FAILED_TECHNICAL"}:
            if any(row.get(key) is not None for key in METRIC_FIELDS):
                raise WalkForwardContractError(f"BLOCKED_RESULT_HAS_NUMERIC_METRICS:{pair}")
            if not row.get("failure_reason"):
                raise WalkForwardContractError(f"BLOCKED_RESULT_MISSING_FAILURE_REASON:{pair}")
        if status in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"}:
            baseline = row.get("baseline_log_loss")
            candidate = row.get("candidate_log_loss")
            improvement = row.get("log_loss_improvement")
            for name, value in (("baseline", baseline), ("candidate", candidate), ("improvement", improvement)):
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise WalkForwardContractError(f"EXECUTED_RESULT_METRIC_NONFINITE:{pair}:{name}")
            if baseline <= 0 or candidate <= 0:
                raise WalkForwardContractError(f"LOG_LOSS_MUST_BE_POSITIVE:{pair}")
            if abs((baseline - candidate) - improvement) > 1e-10:
                raise WalkForwardContractError(f"LOG_LOSS_IMPROVEMENT_ARITHMETIC_MISMATCH:{pair}")
            for key in ("raw_p_value", "by_adjusted_p_value"):
                value = row.get(key)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1):
                    raise WalkForwardContractError(f"P_VALUE_OUT_OF_RANGE:{pair}:{key}")
            lower, upper = row.get("bootstrap_ci_lower"), row.get("bootstrap_ci_upper")
            if (lower is None) != (upper is None):
                raise WalkForwardContractError(f"BOOTSTRAP_CI_ONE_BOUND_MISSING:{pair}")
            if lower is not None:
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (lower, upper)):
                    raise WalkForwardContractError(f"BOOTSTRAP_CI_NONFINITE:{pair}")
                if lower > upper:
                    raise WalkForwardContractError(f"BOOTSTRAP_CI_BOUNDS_REVERSED:{pair}")
            for key in ("brier_score", "balanced_accuracy", "roc_auc", "average_precision"):
                value = row.get(key)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
                    raise WalkForwardContractError(f"SCALAR_METRIC_OUT_OF_RANGE:{pair}:{key}")
            for key in ("calibration_intercept", "calibration_slope"):
                value = row.get(key)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                    raise WalkForwardContractError(f"CALIBRATION_METRIC_NONFINITE:{pair}:{key}")
    if got != expected:
        raise WalkForwardContractError(f"RESULT_ROW_COVERAGE_MISMATCH:missing={len(expected-got)}:unexpected={len(got-expected)}")
    return {
        "row_count": len(rows),
        "unique_config_fold_pairs": len(got),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "complete_expected_coverage": True,
        "metrics_arithmetic_checked": sum(terminal_counts[k] for k in ("EXECUTED_AUDITED", "REJECTED_EMPIRICAL")),
        "model_fitting_performed_by_validator": False,
        "holdout_accessed_by_validator": False,
    }
