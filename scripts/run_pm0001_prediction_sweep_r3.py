#!/usr/bin/env python3
"""Run the authorized PM0001 prediction subset, preserving all 320 terminal rows.

This runner never reads an untouched holdout, emits raw bars, or saves per-observation
predictions. It fits only after an exact run-scoped gate, immutable data/precheck hashes,
and the full 40-configuration by 8-fold precheck are verified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import sys
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from create_pm0001_execution_gate_r3 import (  # noqa: E402
    FOLD_IDS, EXPECTED_DATA_SHA256, git_blob_sha1, read_json, validate_precheck,
)
from prediction_features_r3 import build_feature_batch, load_eligible_session_dates, verify_source_pins  # noqa: E402
from prediction_pm0001_executor_r3 import fit_pm0001_outer_fold  # noqa: E402
from prediction_statistics import (  # noqa: E402
    balanced_accuracy, benjamini_yekutieli, binary_log_loss, brier_score,
    paired_moving_block_bootstrap,
)
from prediction_walkforward_r3 import terminal_result_row, validate_result_rows  # noqa: E402
from run_pm0001_data_execution_precheck_r3 import (  # noqa: E402
    config_rows, fold_positions, read_spot_records,
)

PREREG_PATH = ROOT / "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
LABEL_PATH = ROOT / "research/registry/PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json"
ELIGIBILITY_PATH = ROOT / "research/gates/PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json"
PREFLIGHT_PATH = ROOT / "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
IMPLEMENTATION_PATH = ROOT / "research/gates/PREDICTION_PM0001_IMPLEMENTATION_GATE_R3_2026-10-14.json"
DATA_PIN_PATH = ROOT / "research/data/PREDICTION_DATA_ARTIFACT_PIN_R3_2026-10-13.json"
SOURCE_MANIFEST_SHA_PATH = DATA_PIN_PATH
EPSILON = 1e-6
BOOTSTRAP_BLOCK_LENGTH = 10
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 2026101209
VALID_PRECHECK_STATES = {"PRECHECK_PASS", "BLOCKED_DATA", "BLOCKED_SAMPLE_ELIGIBILITY", "FAILED_PRECHECK"}
RESULT_TERMINAL_STATES = {"EXECUTED_AUDITED", "BLOCKED_DATA", "BLOCKED_GATE", "FAILED_TECHNICAL"}


class SweepError(ValueError):
    """Fail-closed PM0001 sweep contract violation."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def append_error(path: Path, *, config_id: str | None, fold_id: str | None,
                 step: str, error: BaseException, tb: str | None = None) -> dict[str, Any]:
    trace = tb if tb is not None else traceback.format_exc()
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config_id": config_id,
        "fold_id": fold_id,
        "step": step,
        "exception_type": type(error).__name__,
        "exception_message": str(error)[:500],
        "traceback_sha256": sha256_bytes(trace.encode("utf-8")),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def _expected_config_ids(configs: Sequence[Mapping[str, Any]]) -> list[str]:
    ids = sorted(str(x["config_id"]) for x in configs)
    if len(ids) != 40 or len(set(ids)) != 40:
        raise SweepError(f"EXPECTED_40_UNIQUE_PM0001_CONFIGS:{len(ids)}")
    if any(x.get("method_id") != "PM0001" for x in configs):
        raise SweepError("NON_PM0001_CONFIG_IN_SWEEP")
    return ids


def load_precheck_map(path: Path, config_ids: Sequence[str]) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    obj = read_json(path)
    counts = validate_precheck(obj, list(config_ids))
    rows = obj["rows"]
    out = {(str(row["config_id"]), str(row["fold_id"])): row for row in rows}
    if len(out) != 320 or len(counts) < 1:
        raise SweepError("PRECHECK_MAP_DIMENSION_INVALID")
    return out, obj


def expected_pair_list(config_ids: Sequence[str]) -> list[tuple[str, str]]:
    return [(cfg, fold) for cfg in config_ids for fold in FOLD_IDS]


def validate_run_gate(
    gate_path: Path,
    precheck_path: Path,
    precheck: Mapping[str, Any],
    configs: Sequence[Mapping[str, Any]],
    source_commit: str,
    workflow_run_id: str,
) -> dict[str, Any]:
    if not gate_path.is_file():
        raise SweepError("EXECUTION_GATE_FILE_MISSING")
    gate = read_json(gate_path)
    config_ids = _expected_config_ids(configs)
    if gate.get("status") != "PASS_PM0001_EXECUTION_PRECHECK" or gate.get("empirical_fit_authorized") is not True:
        raise SweepError("EXECUTION_GATE_NOT_AUTHORIZED")
    if gate.get("method_id") != "PM0001" or gate.get("configuration_count") != 40:
        raise SweepError("EXECUTION_GATE_SCOPE_INVALID")
    if gate.get("config_ids") != config_ids or gate.get("outer_fold_ids") != list(FOLD_IDS):
        raise SweepError("EXECUTION_GATE_CONFIGURATION_OR_FOLD_PIN_MISMATCH")
    if gate.get("expected_result_rows") != 320:
        raise SweepError("EXECUTION_GATE_EXPECTED_ROW_COUNT_INVALID")
    if gate.get("source_data_sha256") != EXPECTED_DATA_SHA256:
        raise SweepError("EXECUTION_GATE_DATA_HASH_MISMATCH")
    if gate.get("source_commit") != source_commit:
        raise SweepError("EXECUTION_GATE_SOURCE_COMMIT_MISMATCH")
    if str(gate.get("workflow_run_id")) != str(workflow_run_id):
        raise SweepError("EXECUTION_GATE_WORKFLOW_RUN_MISMATCH")
    if gate.get("holdout_accessed") is not False or gate.get("model_fitting_performed_by_precheck") is not False:
        raise SweepError("EXECUTION_GATE_PROVENANCE_FLAGS_INVALID")
    precheck_raw = precheck_path.read_bytes()
    if gate.get("precheck_report_git_blob_sha1") != git_blob_sha1(precheck_raw):
        raise SweepError("EXECUTION_GATE_PRECHECK_BLOB_PIN_MISMATCH")
    if gate.get("precheck_report_sha256") != sha256_bytes(precheck_raw):
        raise SweepError("EXECUTION_GATE_PRECHECK_SHA256_MISMATCH")
    if gate.get("precheck_status_counts") != precheck.get("status_counts"):
        raise SweepError("EXECUTION_GATE_PRECHECK_COUNTS_MISMATCH")
    expected_pins = {
        "eligibility_manifest_git_blob_sha1": ELIGIBILITY_PATH,
        "preflight_report_git_blob_sha1": PREFLIGHT_PATH,
        "implementation_gate_git_blob_sha1": IMPLEMENTATION_PATH,
        "preregistration_git_blob_sha1": PREREG_PATH,
        "runner_git_blob_sha1": Path(__file__).resolve().relative_to(ROOT).as_posix(),
    }
    for field, rel in expected_pins.items():
        p = ROOT / rel if isinstance(rel, str) else rel
        if not p.is_file() or gate.get(field) != git_blob_sha1(p.read_bytes()):
            raise SweepError(f"EXECUTION_GATE_SOURCE_PIN_MISMATCH:{field}")
    if gate.get("eligibility_manifest_git_blob_sha1") != git_blob_sha1(ELIGIBILITY_PATH.read_bytes()):
        raise SweepError("EXECUTION_GATE_ELIGIBILITY_PIN_MISMATCH")
    pin = read_json(DATA_PIN_PATH)
    current = pin.get("current_derived_artifact", {})
    if current.get("artifact_id") != 11698879857:
        raise SweepError("DATA_ARTIFACT_ID_PIN_MISMATCH")
    if current.get("archive_sha256") != "40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b":
        raise SweepError("DATA_ARTIFACT_ARCHIVE_PIN_MISMATCH")
    return gate


def _loss(y: int, p: float) -> float:
    pp = min(1.0 - EPSILON, max(EPSILON, float(p)))
    return -(int(y) * math.log(pp) + (1 - int(y)) * math.log1p(-pp))


def session_loss_deltas(
    result: Any,
    samples: Sequence[Any],
    session_dates: Sequence[str],
) -> tuple[list[int], list[float], dict[str, float]]:
    """Return contiguous session-index deltas; positive is class-prior minus candidate loss."""
    buckets: dict[int, list[float]] = defaultdict(list)
    base_losses: dict[int, list[float]] = defaultdict(list)
    candidate_losses: dict[int, list[float]] = defaultdict(list)
    if not (len(result.validation_indices) == len(result.y_validation) ==
            len(result.probabilities) == len(result.baseline_probabilities)):
        raise SweepError("PREDICTION_VECTOR_LENGTH_MISMATCH")
    for index, y, candidate, baseline in zip(
        result.validation_indices, result.y_validation, result.probabilities, result.baseline_probabilities
    ):
        sample = samples[int(index)]
        pos = int(sample.decision_session_index)
        if pos < 0 or pos >= len(session_dates):
            raise SweepError("DECISION_SESSION_INDEX_OUT_OF_RANGE")
        closs = _loss(int(y), float(candidate))
        bloss = _loss(int(y), float(baseline))
        buckets[pos].append(bloss - closs)
        base_losses[pos].append(bloss)
        candidate_losses[pos].append(closs)
    positions = sorted(buckets)
    if len(positions) < 1:
        raise SweepError("NO_SCORABLE_VALIDATION_SESSIONS")
    deltas = [statistics.fmean(buckets[p]) for p in positions]
    summary = {
        "baseline_log_loss": statistics.fmean(statistics.fmean(base_losses[p]) for p in positions),
        "candidate_log_loss": statistics.fmean(statistics.fmean(candidate_losses[p]) for p in positions),
    }
    if positions != list(range(positions[0], positions[-1] + 1)):
        raise SweepError("BOOTSTRAP_SESSION_SEQUENCE_NOT_CONTIGUOUS")
    return positions, deltas, summary


def precheck_to_terminal_status(precheck_row: Mapping[str, Any] | None, gate_verified: bool) -> tuple[str, str]:
    if precheck_row is None:
        return "BLOCKED_GATE", "PRECHECK_REPORT_OR_CONFIG_FOLD_ROW_MISSING"
    status = precheck_row.get("status")
    if status == "BLOCKED_DATA":
        return "BLOCKED_DATA", ";".join(str(x) for x in precheck_row.get("reason_codes", []) or ["DATA_SUPPORT_BLOCK"])
    if status == "BLOCKED_SAMPLE_ELIGIBILITY":
        return "BLOCKED_DATA", ";".join(str(x) for x in precheck_row.get("reason_codes", []) or ["SAMPLE_ELIGIBILITY_BLOCK"])
    if status == "FAILED_PRECHECK":
        return "FAILED_TECHNICAL", ";".join(str(x) for x in precheck_row.get("reason_codes", []) or ["DATA_PRECHECK_FAILURE"])
    if status == "PRECHECK_PASS" and not gate_verified:
        return "BLOCKED_GATE", "EXECUTION_GATE_MISSING_OR_INVALID;NO_FITTING_PERFORMED"
    if status == "PRECHECK_PASS" and gate_verified:
        return "EXECUTED_AUDITED", ""
    return "BLOCKED_GATE", f"UNKNOWN_PRECHECK_STATUS:{status}"


def _session_bounds(
    label_id: str, fold: Mapping[str, Any], sessions: Sequence[str]
) -> tuple[str, str, str, str]:
    start_idx, end_idx = fold.get("start"), fold.get("end_exclusive")
    if start_idx is None or end_idx is None or not (0 <= int(start_idx) < int(end_idx) <= len(sessions)):
        # A frozen window may have no rows in a particular label-calendar representation.
        return sessions[0], sessions[0], "", ""
    start_idx, end_idx = int(start_idx), int(end_idx)
    train_end = sessions[start_idx - 1] if start_idx > 0 else sessions[0]
    return sessions[0], train_end, sessions[start_idx], sessions[end_idx - 1]


def _diagnostic_feature_missingness(batch: Any) -> dict[str, Any]:
    d = batch.diagnostics
    return {
        "feature_dimension": int(d.get("feature_dimension", 0)),
        "all_emitted_feature_values_finite": True,
        "feature_missingness_rule": "No feature imputation needed for the frozen lag-stack; nonfinite history excluded by feature builder.",
        "sample_count_emitted": int(d.get("samples_emitted", len(batch.samples))),
    }


def _base_row(
    *, config: Mapping[str, Any], fold_id: str, bounds: tuple[str, str, str, str],
    status: str, reason: str | None, precheck_row: Mapping[str, Any] | None,
    label_target: str, purge: int, embargo: int, source_manifest_sha256: str,
    feature_missingness: Mapping[str, Any] | None = None,
    metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pr = precheck_row or {}
    row = terminal_result_row(
        config=config, fold_id=fold_id,
        train_start=bounds[0] or "NOT_AVAILABLE", train_end=bounds[1] or "NOT_AVAILABLE",
        validation_start=bounds[2] or "NOT_AVAILABLE", validation_end=bounds[3] or "NOT_AVAILABLE",
        status=status, failure_reason=reason,
        eligible_train_rows=int(pr.get("train_rows", 0)),
        eligible_validation_rows=int(pr.get("validation_rows", 0)),
        train_positive_support=int(pr.get("train_positive", 0)),
        train_negative_support=int(pr.get("train_negative", 0)),
        validation_positive_support=int(pr.get("validation_positive", 0)),
        validation_negative_support=int(pr.get("validation_negative", 0)),
        purge_sessions=int(purge), embargo_sessions=int(embargo),
        label_exclusion_count=None,
        feature_missingness=feature_missingness,
        label_target_endpoint=label_target,
        source_manifest_sha256=source_manifest_sha256,
        metrics=metrics,
    )
    row["precheck_status"] = pr.get("status", "MISSING")
    row["precheck_reason_codes"] = pr.get("reason_codes", [])
    row["label_exclusion_count_status"] = "FOLD_SPECIFIC_COUNT_NOT_EMITTED_BY_FROZEN_FEATURE_BUILDER"
    row["previous_sign_baseline_status"] = "NOT_DEFINED_IN_FROZEN_PREREGISTRATION"
    row["inference_scope"] = "configuration-level paired moving-block bootstrap across available outer validation sessions"
    return row


def _get_label_minima(prereg: Mapping[str, Any], label_id: str) -> dict[str, int]:
    sample = prereg["sample_eligibility"]
    inner = prereg["chronological_validation"]["inner_validation"]
    fcal = prereg["fitting_and_calibration"]
    return {
        "min_outer_train_rows": int(sample["minimum_train_rows"][label_id]),
        "min_outer_validation_rows": int(sample["minimum_validation_rows"][label_id]),
        "min_outer_train_class_support": int(sample["minimum_class_support_each_direction_training"][label_id]),
        "min_outer_validation_class_support": int(sample["minimum_class_support_each_direction_per_validation_fold"][label_id]),
        "min_inner_train_rows": int(inner["minimum_inner_training_rows"][label_id]),
        "min_inner_validation_rows": int(inner["minimum_inner_validation_rows"][label_id]),
        "min_inner_class_support": int(inner["class_support_each_direction_minimum"][label_id]),
    }


def _add_bootstrap_to_rows(
    rows: list[dict[str, Any]],
    configs: Sequence[Mapping[str, Any]],
    inference_by_config: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    by_label: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for cfg in configs:
        by_label[str(cfg["configuration"]["label_id"])].append(cfg)
    label_summaries: dict[str, Any] = {}
    for label_id, label_configs in sorted(by_label.items()):
        p_family: dict[str, float] = {}
        for cfg in label_configs:
            cid = str(cfg["config_id"])
            infer = inference_by_config.get(cid, {})
            raw_p = infer.get("raw_p_value")
            # Conservative family accounting: non-identifiable/incomplete empirical tests count as p=1.
            p_family[cid] = float(raw_p) if isinstance(raw_p, (int, float)) and math.isfinite(float(raw_p)) else 1.0
        adjusted = benjamini_yekutieli(p_family, q=0.05)
        for row in rows:
            cid = str(row["config_id"])
            infer = inference_by_config.get(cid)
            if row["label_id"] != label_id or row["terminal_status"] not in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"}:
                continue
            if not infer:
                continue
            row["bootstrap_ci_lower"] = infer.get("ci_low")
            row["bootstrap_ci_upper"] = infer.get("ci_high")
            row["raw_p_value"] = infer.get("raw_p_value")
            row["by_adjusted_p_value"] = (
                adjusted[cid]["by_adjusted_p_value"]
                if infer.get("raw_p_value") is not None else None
            )
            row["bootstrap_status"] = infer.get("inferential_status", "NOT_IDENTIFIABLE")
            row["bootstrap_replicates"] = int(infer.get("replicates", 0))
            row["by_family_size"] = len(label_configs)
            row["by_reject_at_q_0_05"] = (
                adjusted[cid]["reject_at_q"] if infer.get("raw_p_value") is not None else False
            )
        label_summaries[label_id] = {
            "family_size_pm0001_configurations": len(label_configs),
            "q": 0.05,
            "procedure": "Benjamini-Yekutieli within label stratum",
            "p_family_includes_nonidentifiable_as_one": True,
            "configurations": {
                cfg["config_id"]: {
                    "observed_mean_session_improvement": inference_by_config.get(cfg["config_id"], {}).get("observed_mean_improvement"),
                    "ci_low": inference_by_config.get(cfg["config_id"], {}).get("ci_low"),
                    "ci_high": inference_by_config.get(cfg["config_id"], {}).get("ci_high"),
                    "raw_p_value": inference_by_config.get(cfg["config_id"], {}).get("raw_p_value"),
                    "by_adjusted_p_value": adjusted[str(cfg["config_id"])]["by_adjusted_p_value"],
                    "reject_at_q_0_05": adjusted[str(cfg["config_id"])]["reject_at_q"],
                    "inferential_status": inference_by_config.get(cfg["config_id"], {}).get("inferential_status", "NO_EMPIRICAL_FIT"),
                } for cfg in label_configs
            },
        }
    return label_summaries


def run_sweep(
    *, merged_gzip: Path | None, precheck_path: Path, gate_path: Path,
    output_path: Path, summary_path: Path, errors_path: Path,
    source_commit: str, workflow_run_id: str,
) -> dict[str, Any]:
    errors_path.parent.mkdir(parents=True, exist_ok=True)
    errors_path.write_text("", encoding="utf-8")
    prereg = read_json(PREREG_PATH)
    label_manifest = read_json(LABEL_PATH)
    configs = sorted(config_rows(), key=lambda x: str(x["config_id"]))
    config_ids = _expected_config_ids(configs)
    config_by_id = {str(x["config_id"]): x for x in configs}
    if len(config_by_id) != 40:
        raise SweepError("PM0001_CONFIG_MAPPING_NOT_UNIQUE")
    windows = prereg["chronological_validation"]["fold_calendar_windows"]
    windows_by_id = {str(x["id"]): x for x in windows}
    label_targets = {
        str(k): str(v.get("target", v.get("definition", k)))
        for k, v in prereg["labels"].items()
    }
    dataset_pin_sha256 = sha256_bytes(SOURCE_MANIFEST_SHA_PATH.read_bytes())
    source_commit = source_commit or "unknown"
    workflow_run_id = str(workflow_run_id or "unknown")

    precheck_map: dict[tuple[str, str], dict[str, Any]] = {}
    precheck: dict[str, Any] | None = None
    global_gate_reason = ""
    if precheck_path.is_file():
        try:
            precheck_map, precheck = load_precheck_map(precheck_path, config_ids)
        except Exception as exc:
            global_gate_reason = f"PRECHECK_REPORT_INVALID:{type(exc).__name__}:{str(exc)[:220]}"
            append_error(errors_path, config_id=None, fold_id=None, step="load_precheck", error=exc)
            precheck_map = {}
            precheck = None
    else:
        global_gate_reason = "PRECHECK_REPORT_MISSING"

    gate: dict[str, Any] | None = None
    gate_verified = False
    if not global_gate_reason and precheck is not None and merged_gzip is not None and merged_gzip.is_file():
        try:
            gate = validate_run_gate(gate_path, precheck_path, precheck, configs, source_commit, workflow_run_id)
            if precheck.get("status") != "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING":
                raise SweepError("PRECHECK_REPORT_STATUS_NOT_FITTING_AUTHORIZED")
            verify_source_pins(EXPECTED_DATA_SHA256)
            gate_verified = True
        except Exception as exc:
            global_gate_reason = f"EXECUTION_GATE_REJECTED:{type(exc).__name__}:{str(exc)[:220]}"
            append_error(errors_path, config_id=None, fold_id=None, step="validate_execution_gate", error=exc)
    elif not global_gate_reason:
        global_gate_reason = "CANONICAL_MERGED_DATASET_MISSING_OR_NOT_AVAILABLE"

    rows: list[dict[str, Any]] = []
    fold_delta_by_config: dict[str, dict[str, list[float]]] = defaultdict(dict)
    inference_by_config: dict[str, dict[str, Any]] = {}
    feature_cache: dict[tuple[str, int], tuple[Any, list[str], list[dict[str, Any]]]] = {}
    fitting_any = False
    precheck_status_counts = Counter((precheck or {}).get("status_counts", {}))
    all_config_fold_rows = 0

    records = None
    calendar = None
    if gate_verified:
        try:
            records = read_spot_records(merged_gzip)
            calendar = read_json(ROOT / prereg["scope"]["session_calendar_path"])
        except Exception as exc:
            gate_verified = False
            global_gate_reason = f"DATASET_READ_FAILED:{type(exc).__name__}:{str(exc)[:220]}"
            append_error(errors_path, config_id=None, fold_id=None, step="read_verified_data", error=exc)

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for item in configs:
        spec = item["configuration"]
        grouped[(str(spec["label_id"]), int(spec["lookback_bars"]))].append(item)
    # Process one label/lookback representation at a time. Retaining all feature batches
    # would duplicate the 40/120-column lag matrices and risk exhausting the hosted runner.
    ordered_groups = sorted(grouped.items(), key=lambda kv: min(str(x["config_id"]) for x in kv[1]))
    for cache_key, group_configs in ordered_groups:
        label_id, lookback = cache_key
        batch = None
        session_dates: list[str] = []
        folds: list[dict[str, Any]] = []
        X = y = decision = endpoint = None
        if gate_verified and records is not None and calendar is not None:
            try:
                session_dates = load_eligible_session_dates(calendar, label_id)
                batch = build_feature_batch(records, calendar, label_id, lookback,
                                            source_csv_sha256=EXPECTED_DATA_SHA256)
                folds = fold_positions(session_dates, windows)
                X = np.asarray([s.features for s in batch.samples], dtype=float)
                y = np.asarray([s.y for s in batch.samples], dtype=int)
                decision = np.asarray([s.decision_session_index for s in batch.samples], dtype=int)
                endpoint = np.asarray([s.target_endpoint_session_index for s in batch.samples], dtype=int)
            except Exception as exc:
                gate_verified = False
                global_gate_reason = f"FEATURE_BUILD_FAILED:{type(exc).__name__}:{str(exc)[:220]}"
                append_error(errors_path, config_id=str(group_configs[0]["config_id"]), fold_id=None,
                             step="build_feature_batch", error=exc)
                batch = None
                X = y = decision = endpoint = None

        group_configs = sorted(group_configs, key=lambda x: str(x["config_id"]))
        for config in group_configs:
            cid = str(config["config_id"])
            spec = config["configuration"]
            label_id = str(spec["label_id"])
            purge = int(spec["purge_exchange_sessions"])
            embargo = int(spec["embargo_exchange_sessions"])
            minima = _get_label_minima(prereg, label_id)
            target_definition = label_targets.get(label_id, label_id)
            for fold_id in FOLD_IDS:
                all_config_fold_rows += 1
                pre_row = precheck_map.get((cid, fold_id))
                if batch is not None:
                    fold = next(x for x in folds if x["fold_id"] == fold_id)
                    bounds = _session_bounds(label_id, fold, session_dates)
                    feature_missingness = _diagnostic_feature_missingness(batch)
                else:
                    bounds = (
                        str(prereg.get("scope", {}).get("calendar_range", ["2021-10-11"])[0]),
                        "NOT_AVAILABLE",
                        str(windows_by_id[fold_id]["start"]),
                        str(windows_by_id[fold_id]["end_inclusive"]),
                    )
                    feature_missingness = None
                    fold = {"fold_id": fold_id, "start": None, "end_exclusive": None}
                status, reason = precheck_to_terminal_status(pre_row, gate_verified)
                if global_gate_reason and pre_row is not None and pre_row.get("status") == "PRECHECK_PASS":
                    status, reason = "BLOCKED_GATE", global_gate_reason
                if status != "EXECUTED_AUDITED":
                    row = _base_row(
                        config=config, fold_id=fold_id, bounds=bounds, status=status,
                        reason=reason or None, precheck_row=pre_row,
                        label_target=target_definition, purge=purge, embargo=embargo,
                        source_manifest_sha256=dataset_pin_sha256,
                        feature_missingness=feature_missingness,
                    )
                    rows.append(row)
                    write_json_atomic(output_path, {"schema_version": "pm0001-result-bundle-r3-v1", "partial": True, "rows": rows})
                    continue

                try:
                    assert batch is not None and X is not None and y is not None
                    assert decision is not None and endpoint is not None
                    start_pos, end_pos = int(fold["start"]), int(fold["end_exclusive"])
                    result = fit_pm0001_outer_fold(
                        X, y, decision, endpoint,
                        fold_id=fold_id,
                        validation_start_session=start_pos,
                        validation_end_session_exclusive=end_pos,
                        purge_sessions=purge,
                        embargo_sessions=embargo,
                        c=float(spec["model_parameters"]["C"]),
                        min_outer_train_rows=minima["min_outer_train_rows"],
                        min_outer_validation_rows=minima["min_outer_validation_rows"],
                        min_inner_train_rows=minima["min_inner_train_rows"],
                        min_inner_validation_rows=minima["min_inner_validation_rows"],
                        min_outer_train_class_support=minima["min_outer_train_class_support"],
                        min_outer_validation_class_support=minima["min_outer_validation_class_support"],
                        min_inner_class_support=minima["min_inner_class_support"],
                        refit_cadence_sessions=20,
                    )
                    positions, deltas, session_metrics = session_loss_deltas(result, batch.samples, session_dates)
                    y_true = list(map(int, result.y_validation))
                    candidate_probabilities = [min(1.0 - EPSILON, max(EPSILON, float(p))) for p in result.probabilities]
                    baseline_probabilities = [min(1.0 - EPSILON, max(EPSILON, float(p))) for p in result.baseline_probabilities]
                    baseline_ll = float(session_metrics["baseline_log_loss"])
                    candidate_ll = float(session_metrics["candidate_log_loss"])
                    improvement = baseline_ll - candidate_ll
                    if not (math.isfinite(baseline_ll) and math.isfinite(candidate_ll) and baseline_ll > 0 and candidate_ll > 0):
                        raise SweepError("NONFINITE_OR_NONPOSITIVE_LOGLOSS")
                    if abs(improvement - statistics.fmean(deltas)) > 1e-10:
                        raise SweepError("SESSION_LOSS_IMPROVEMENT_ARITHMETIC_MISMATCH")
                    metrics = {
                        "baseline_log_loss": baseline_ll,
                        "candidate_log_loss": candidate_ll,
                        "log_loss_improvement": improvement,
                        "class_prior_baseline_log_loss": baseline_ll,
                        "previous_sign_baseline_log_loss": None,
                        "brier_score": float(brier_score(y_true, candidate_probabilities)),
                        "balanced_accuracy": float(balanced_accuracy(y_true, candidate_probabilities)),
                        "roc_auc": float(roc_auc_score(y_true, candidate_probabilities)),
                        "average_precision": float(average_precision_score(y_true, candidate_probabilities)),
                        "calibration_intercept": result.calibration_intercept,
                        "calibration_slope": result.calibration_slope,
                        "observed_session_count": len(positions),
                        "bootstrap_status": "PENDING_CONFIGURATION_INFERENCE",
                        "bootstrap_replicates": 0,
                    }
                    train_rows = len(result.final_train_indices)
                    final_train_y = y[np.asarray(result.final_train_indices, dtype=int)]
                    row_pre = dict(pre_row or {})
                    row_pre["train_rows"] = train_rows
                    row_pre["train_positive"] = int(np.sum(final_train_y == 1))
                    row_pre["train_negative"] = int(np.sum(final_train_y == 0))
                    row_pre["validation_rows"] = len(result.validation_indices)
                    row_pre["validation_positive"] = int(np.sum(np.asarray(y_true) == 1))
                    row_pre["validation_negative"] = int(np.sum(np.asarray(y_true) == 0))
                    row = _base_row(
                        config=config, fold_id=fold_id, bounds=bounds, status="EXECUTED_AUDITED",
                        reason=None, precheck_row=row_pre, label_target=target_definition,
                        purge=purge, embargo=embargo, source_manifest_sha256=dataset_pin_sha256,
                        feature_missingness=feature_missingness, metrics=metrics,
                    )
                    row["precheck_status"] = "PRECHECK_PASS"
                    row["feature_rows_scored"] = len(result.validation_indices)
                    row["rolling_refit_count"] = int(result.refit_count)
                    row["rolling_refit_cadence_exchange_sessions"] = 20
                    row["oof_calibration_rows"] = int(result.oof_rows)
                    rows.append(row)
                    fold_delta_by_config[cid][fold_id] = deltas
                    fitting_any = True
                except Exception as exc:
                    tb = traceback.format_exc()
                    append_error(errors_path, config_id=cid, fold_id=fold_id,
                                 step="fit_pm0001_outer_fold", error=exc, tb=tb)
                    row = _base_row(
                        config=config, fold_id=fold_id, bounds=bounds, status="FAILED_TECHNICAL",
                        reason=f"FIT_OR_METRIC_FAILURE:{type(exc).__name__}:{str(exc)[:200]}",
                        precheck_row=pre_row, label_target=target_definition,
                        purge=purge, embargo=embargo, source_manifest_sha256=dataset_pin_sha256,
                        feature_missingness=feature_missingness,
                    )
                    row["failure_traceback_sha256"] = sha256_bytes(tb.encode("utf-8"))
                    rows.append(row)
                write_json_atomic(output_path, {"schema_version": "pm0001-result-bundle-r3-v1", "partial": True, "rows": rows})
        # Release feature objects before constructing the next representation.
        del batch, X, y, decision, endpoint, session_dates, folds
        import gc
        gc.collect()

    rows.sort(key=lambda r: (str(r["config_id"]), str(r["fold_id"])))
    if all_config_fold_rows != 320 or len(rows) != 320:
        exc = SweepError(f"RESULT_TERMINAL_ROW_ACCOUNTING_FAILED:attempted={all_config_fold_rows}:rows={len(rows)}")
        append_error(errors_path, config_id=None, fold_id=None, step="terminal_accounting", error=exc)
        raise exc

    inference_by_config: dict[str, dict[str, Any]] = {}
    prereg_boot = prereg["metrics_and_inference"]["bootstrap"]
    if prereg_boot.get("block_length_exchange_sessions") != BOOTSTRAP_BLOCK_LENGTH or prereg_boot.get("replicates") != BOOTSTRAP_REPLICATES or prereg_boot.get("seed") != BOOTSTRAP_SEED:
        raise SweepError("PREREGISTERED_BOOTSTRAP_SETTINGS_MISMATCH")
    for config in configs:
        cid = str(config["config_id"])
        folds_deltas = [fold_delta_by_config[cid][f] for f in FOLD_IDS if f in fold_delta_by_config[cid]]
        infer: dict[str, Any] = {"inferential_status": "NO_EMPIRICAL_FIT", "raw_p_value": None, "ci_low": None, "ci_high": None}
        if folds_deltas:
            try:
                if any(len(d) < BOOTSTRAP_BLOCK_LENGTH for d in folds_deltas):
                    raise SweepError("BOOTSTRAP_FOLD_HAS_FEWER_THAN_TEN_SESSIONS")
                result = paired_moving_block_bootstrap(
                    folds_deltas,
                    block_length=BOOTSTRAP_BLOCK_LENGTH,
                    replicates=BOOTSTRAP_REPLICATES,
                    seed=BOOTSTRAP_SEED,
                    confidence_level=float(prereg_boot["confidence_level"]),
                )
                infer = dict(result)
            except Exception as exc:
                append_error(errors_path, config_id=cid, fold_id=None, step="paired_moving_block_bootstrap", error=exc)
                infer = {
                    "inferential_status": f"INFERENCE_UNAVAILABLE:{type(exc).__name__}:{str(exc)[:160]}",
                    "raw_p_value": None, "ci_low": None, "ci_high": None,
                    "replicates": 0,
                }
        inference_by_config[cid] = infer

    label_inference = _add_bootstrap_to_rows(rows, configs, inference_by_config)
    validation = validate_result_rows(rows, expected_pair_list(config_ids))
    terminal_counts = Counter(str(row["terminal_status"]) for row in rows)
    executed_count = terminal_counts.get("EXECUTED_AUDITED", 0)
    failed_count = terminal_counts.get("FAILED_TECHNICAL", 0)
    blocked_count = terminal_counts.get("BLOCKED_DATA", 0) + terminal_counts.get("BLOCKED_GATE", 0)
    results_acquired = bool(fitting_any and len(rows) == 320 and validation.get("complete_expected_coverage") is True)
    if results_acquired and failed_count:
        result_status = "COMPLETE_EMPIRICAL_RESULTS_WITH_TECHNICAL_FAILURES"
    elif results_acquired:
        result_status = "COMPLETE_EMPIRICAL_RESULTS"
    else:
        result_status = "BLOCKED_GATE_NO_EMPIRICAL_FITS"

    result_doc = {
        "schema_version": "pm0001-result-bundle-r3-v1",
        "research_date": datetime.now(timezone.utc).date().isoformat(),
        "status": result_status,
        "results_acquired": results_acquired,
        "scope": "PM0001 only; 40 preregistered configurations x 8 chronological outer folds; prediction research only",
        "source_commit": source_commit,
        "workflow_run_id": workflow_run_id,
        "source_data_sha256": EXPECTED_DATA_SHA256,
        "source_manifest_path": SOURCE_MANIFEST_SHA_PATH.relative_to(ROOT).as_posix(),
        "source_manifest_sha256": dataset_pin_sha256,
        "precheck_report_sha256": sha256_bytes(precheck_path.read_bytes()) if precheck_path.is_file() else None,
        "execution_gate_sha256": sha256_bytes(gate_path.read_bytes()) if gate_path.is_file() else None,
        "configuration_count": 40,
        "outer_fold_count": 8,
        "expected_terminal_rows": 320,
        "terminal_rows_written": len(rows),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "empirical_fits_performed": int(executed_count),
        "blocked_or_failed_rows": int(blocked_count + failed_count),
        "model_fitting_performed": bool(fitting_any),
        "holdout_accessed": False,
        "raw_market_rows_emitted": False,
        "per_observation_predictions_persisted": False,
        "primary_metric": "session-weighted out-of-sample log loss",
        "primary_effect": "class-prior baseline log loss minus PM0001 log loss; positive favors PM0001",
        "previous_sign_baseline": "NOT_COMPUTED: no definition exists in the frozen preregistration; field kept null rather than inventing a comparator",
        "bootstrap": {
            "method": "paired moving-block bootstrap on mean per-session class-prior-minus-candidate log-loss",
            "block_length_exchange_sessions": BOOTSTRAP_BLOCK_LENGTH,
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": BOOTSTRAP_SEED,
            "confidence_level": float(prereg_boot["confidence_level"]),
        },
        "multiplicity": {
            "procedure": "Benjamini-Yekutieli FDR",
            "q": 0.05,
            "family": "PM0001 configurations with the same frozen label stratum; non-identifiable p-values count as 1 for family accounting",
            "label_families": label_inference,
        },
        "validation": validation,
        "errors_jsonl_sha256": sha256_bytes(errors_path.read_bytes()),
        "rows": rows,
    }
    write_json_atomic(output_path, result_doc)
    summary = {k: v for k, v in result_doc.items() if k != "rows"}
    summary["result_file_sha256"] = sha256_bytes(output_path.read_bytes())
    summary["errors_jsonl_path"] = errors_path.relative_to(ROOT).as_posix() if errors_path.is_relative_to(ROOT) else str(errors_path)
    write_json_atomic(summary_path, summary)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged-gzip", type=Path, default=None)
    ap.add_argument("--precheck-report", type=Path, required=True)
    ap.add_argument("--execution-gate", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--errors", type=Path, required=True)
    ap.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", "unknown"))
    ap.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID", "unknown"))
    args = ap.parse_args()
    try:
        result = run_sweep(
            merged_gzip=args.merged_gzip,
            precheck_path=args.precheck_report,
            gate_path=args.execution_gate,
            output_path=args.output,
            summary_path=args.summary,
            errors_path=args.errors,
            source_commit=args.source_commit,
            workflow_run_id=args.workflow_run_id,
        )
        print(json.dumps({k: v for k, v in result.items() if k not in {"multiplicity"}}, sort_keys=True, indent=2))
        return 0 if result.get("terminal_rows_written") == 320 else 2
    except Exception as exc:
        tb = traceback.format_exc()
        append_error(args.errors, config_id=None, fold_id=None, step="runner_fatal", error=exc, tb=tb)
        print(json.dumps({
            "status": "RUNNER_FATAL",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:500],
            "traceback_sha256": sha256_bytes(tb.encode("utf-8")),
            "holdout_accessed": False,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
