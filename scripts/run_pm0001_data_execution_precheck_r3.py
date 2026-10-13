#!/usr/bin/env python3
"""Data-backed PM0001 execution precheck. Aggregate outputs only; never fits a model.

Run only after encrypted-bundle integrity and R3 data preflight pass. It independently
verifies the canonical uncompressed CSV hash, uses the frozen feature contract and
registry, checks all 40 PM0001 configurations across eight outer folds, and emits
one terminal precheck row per config/fold. A failed row is retained and blocked.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prediction_features_r3 import (  # noqa: E402
    build_feature_batch, load_eligible_session_dates, verify_source_pins,
)
from prediction_pm0001_executor_r3 import (  # noqa: E402
    PM0001ExecutionError, _precheck_inner_oof_support,
)

PRE_REG = ROOT / "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
LABEL_MANIFEST = ROOT / "research/registry/PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json"
CONFIG_MANIFEST = ROOT / "research/registry/PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json"
REGISTRY_INDEX = ROOT / "research/registry/PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
ELIGIBILITY = ROOT / "research/gates/PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json"
DATA_PREFLIGHT = ROOT / "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
DATA_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
TERMINAL = {"PRECHECK_PASS", "BLOCKED_DATA", "BLOCKED_SAMPLE_ELIGIBILITY", "FAILED_PRECHECK"}


class PrecheckError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise PrecheckError(f"JSON_OBJECT_REQUIRED:{path}")
    return obj


def canonical_uncompressed_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_spot_records(path: Path) -> list[dict[str, str]]:
    # Retain only the four fields used by the frozen feature builder, not raw option rows.
    records: list[dict[str, str]] = []
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"row_type", "timestamp_ist", "session_date", "nifty_close"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise PrecheckError("CANONICAL_CSV_REQUIRED_FIELDS_MISSING")
        for row in reader:
            if (row.get("row_type") or "").strip().upper() == "SPOT":
                records.append({k: row.get(k, "") for k in required})
    return records


def fold_positions(session_dates: list[str], windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for w in windows:
        eligible = [i for i, d in enumerate(session_dates) if w["start"] <= d <= w["end_inclusive"]]
        if not eligible:
            out.append({"fold_id": w["id"], "start": None, "end_exclusive": None})
        else:
            out.append({"fold_id": w["id"], "start": eligible[0], "end_exclusive": eligible[-1] + 1})
    return out


def config_rows() -> list[dict[str, Any]]:
    index = read_json(REGISTRY_INDEX)
    rows = []
    seen = set()
    for shard in index.get("configuration_shards", index.get("config_shards", [])):
        p = ROOT / shard.get("path", "")
        if not p.is_file():
            raise PrecheckError(f"CONFIG_SHARD_MISSING:{p}")
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != shard.get("sha256"):
            raise PrecheckError(f"CONFIG_SHARD_HASH_MISMATCH:{p}")
        payload = json.loads(raw.decode("utf-8"))
        configs = payload.get("configs", [])
        if len(configs) != shard.get("record_count", shard.get("count")):
            raise PrecheckError(f"CONFIG_SHARD_COUNT_MISMATCH:{p}")
        for row in configs:
            if row.get("config_id") in seen:
                raise PrecheckError("DUPLICATE_CONFIG_ID")
            seen.add(row.get("config_id"))
            if row.get("method_id") == "PM0001":
                rows.append(row)
    if len(rows) != 40:
        raise PrecheckError(f"EXPECTED_40_PM0001_CONFIGS:{len(rows)}")
    return rows


def support_minima(prereg: dict[str, Any], label_id: str) -> dict[str, int]:
    eligibility = prereg["sample_eligibility"]
    inner = prereg["chronological_validation"]["inner_validation"]
    return {
        "min_train_rows": int(eligibility["minimum_train_rows"][label_id]),
        "min_validation_rows": int(eligibility["minimum_validation_rows"][label_id]),
        "min_train_class_each": int(eligibility["minimum_class_support_each_direction_training"][label_id]),
        "min_validation_class_each": int(eligibility["minimum_class_support_each_direction_per_validation_fold"][label_id]),
        "min_inner_train_rows": int(inner["minimum_inner_training_rows"][label_id]),
        "min_inner_validation_rows": int(inner["minimum_inner_validation_rows"][label_id]),
        "min_inner_class_each": int(inner["class_support_each_direction_minimum"][label_id]),
    }


def class_counts(y: np.ndarray) -> tuple[int, int]:
    return int(np.sum(y == 1)), int(np.sum(y == 0))


def precheck_fold(samples, fold, config, minima, label_fold_support):
    label_id = config["configuration"]["label_id"]
    purge = int(config["configuration"]["purge_exchange_sessions"])
    embargo = int(config["configuration"]["embargo_exchange_sessions"])
    if not label_fold_support.get("passes_frozen_data_minima", False):
        return {"status": "BLOCKED_DATA", "reason_codes": label_fold_support.get("block_reasons") or ["DATA_SUPPORT_MINIMUM_FAILED"]}
    if fold["start"] is None:
        return {"status": "BLOCKED_SAMPLE_ELIGIBILITY", "reason_codes": ["FOLD_HAS_NO_ELIGIBLE_SESSIONS"]}
    decision = np.asarray([s.decision_session_index for s in samples], dtype=int)
    endpoint = np.asarray([s.target_endpoint_session_index for s in samples], dtype=int)
    y = np.asarray([s.y for s in samples], dtype=int)
    start, end = int(fold["start"]), int(fold["end_exclusive"])
    train = np.flatnonzero((decision < start - purge) & (endpoint < start))
    valid = np.flatnonzero((decision >= start + embargo) & (decision < end) & (endpoint < end) & (endpoint >= decision))
    yp, yn = class_counts(y[train]) if len(train) else (0, 0)
    vp, vn = class_counts(y[valid]) if len(valid) else (0, 0)
    diagnostics = {
        "train_rows": int(len(train)), "validation_rows": int(len(valid)),
        "train_positive": yp, "train_negative": yn,
        "validation_positive": vp, "validation_negative": vn,
        "purge_sessions": purge, "embargo_sessions": embargo,
    }
    reasons = []
    if len(train) < minima["min_train_rows"]: reasons.append("OUTER_TRAIN_ROWS_BELOW_MINIMUM")
    if min(yp, yn) < minima["min_train_class_each"]: reasons.append("OUTER_TRAIN_CLASS_SUPPORT_BELOW_MINIMUM")
    if len(valid) < minima["min_validation_rows"]: reasons.append("OUTER_VALIDATION_ROWS_BELOW_MINIMUM")
    if min(vp, vn) < minima["min_validation_class_each"]: reasons.append("OUTER_VALIDATION_CLASS_SUPPORT_BELOW_MINIMUM")
    if np.any(endpoint[train] >= start): reasons.append("IMMATURE_TRAINING_TARGET")
    if np.any(endpoint[valid] >= end): reasons.append("VALIDATION_TARGET_ESCAPES_FOLD")
    if reasons:
        return {"status": "BLOCKED_SAMPLE_ELIGIBILITY", "reason_codes": reasons, **diagnostics}

    # Preflight each 20-session rolling refit's training support and all three inner OOF folds.
    unique_validation_sessions = sorted(set(decision[valid].tolist()))
    cutoffs = list(range(start, end, int(20)))
    checked = 0
    for cutoff in cutoffs:
        cutoff_train = np.flatnonzero((decision < cutoff - purge) & (endpoint < cutoff))
        if len(cutoff_train) == 0:
            reasons.append(f"REFIT_{cutoff}_NO_MATURE_TRAINING_ROWS")
            continue
        cp, cn = class_counts(y[cutoff_train])
        if len(cutoff_train) < minima["min_train_rows"]:
            reasons.append(f"REFIT_{cutoff}_TRAIN_ROWS_BELOW_MINIMUM")
            continue
        if min(cp, cn) < minima["min_train_class_each"]:
            reasons.append(f"REFIT_{cutoff}_TRAIN_CLASS_SUPPORT_BELOW_MINIMUM")
            continue
        try:
            _precheck_inner_oof_support(
                y[cutoff_train], decision[cutoff_train], endpoint[cutoff_train],
                purge_sessions=purge, embargo_sessions=embargo,
                min_train_rows=minima["min_inner_train_rows"],
                min_validation_rows=minima["min_inner_validation_rows"],
                min_class_support_each=minima["min_inner_class_each"],
            )
            checked += 1
        except PM0001ExecutionError as exc:
            reasons.append(f"REFIT_{cutoff}_{str(exc).split(':')[0]}")
    if reasons:
        return {"status": "BLOCKED_SAMPLE_ELIGIBILITY", "reason_codes": sorted(set(reasons)), **diagnostics,
                "refit_cutoffs_checked": checked}
    return {"status": "PRECHECK_PASS", "reason_codes": [], **diagnostics, "refit_cutoffs_checked": checked}


def run_precheck(merged_gzip: Path, output_path: Path) -> dict[str, Any]:
    if canonical_uncompressed_sha256(merged_gzip) != DATA_SHA256:
        raise PrecheckError("CANONICAL_UNCOMPRESSED_CSV_SHA256_MISMATCH")
    prereg = read_json(PRE_REG)
    label_manifest = read_json(LABEL_MANIFEST)
    preflight = read_json(DATA_PREFLIGHT)
    eligibility = read_json(ELIGIBILITY)
    if preflight.get("canonical_hash_matches") is not True or preflight.get("holdout_accessed") is not False:
        raise PrecheckError("DATA_PREFLIGHT_NOT_PASS_OR_HOLDOUT_SCOPE_INVALID")
    if eligibility.get("empirical_fit_authorized") is not False:
        raise PrecheckError("ELIGIBILITY_MANIFEST_MUST_NOT_AUTHORIZE_FITTING")
    calendar_path = ROOT / prereg["scope"]["session_calendar_path"]
    calendar = read_json(calendar_path)
    verify_source_pins(DATA_SHA256, calendar_path=calendar_path)
    records = read_spot_records(merged_gzip)
    configs = config_rows()
    support_map = {(x["label_id"], x["fold_id"]): x for x in preflight.get("label_sample_support", [])}
    windows = prereg["chronological_validation"]["fold_calendar_windows"]
    by_key = {}
    rows = []
    status_counts = Counter()
    for config in configs:
        c = config["configuration"]
        label_id, lookback = c["label_id"], int(c["lookback_bars"])
        key = (label_id, lookback)
        if key not in by_key:
            session_dates = load_eligible_session_dates(calendar, label_id)
            batch = build_feature_batch(records, calendar, label_id, lookback,
                                        source_csv_sha256=DATA_SHA256)
            by_key[key] = (batch, fold_positions(session_dates, windows))
        batch, folds = by_key[key]
        samples = batch.samples
        minima = support_minima(prereg, label_id)
        for fold in folds:
            support = support_map.get((label_id, fold["fold_id"]), {})
            try:
                result = precheck_fold(samples, fold, c, minima, support)
            except Exception as exc:
                result = {"status": "FAILED_PRECHECK", "reason_codes": [f"{type(exc).__name__}:{str(exc)[:180]}"]}
            row = {
                "config_id": config["config_id"], "method_id": "PM0001",
                "label_id": label_id, "lookback_bars": lookback,
                "c": float(c["model_parameters"]["C"]), "fold_id": fold["fold_id"],
                **result, "empirical_fit_authorized": False, "model_fitting_performed": False,
                "holdout_accessed": False,
            }
            rows.append(row)
            status_counts[row["status"]] += 1
    if len(rows) != 320 or any(row["status"] not in TERMINAL for row in rows):
        raise PrecheckError("PRECHECK_ROW_ACCOUNTING_OR_TERMINAL_STATUS_FAILED")
    report = {
        "schema_version": "pm0001-data-execution-precheck-r3-v1",
        "status": "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING",
        "source_csv_sha256": DATA_SHA256,
        "configuration_count": 40, "outer_fold_count": 8, "result_row_count": len(rows),
        "status_counts": dict(status_counts), "rows": rows,
        "raw_rows_retained": False, "raw_rows_emitted": False, "samples_persisted": False,
        "model_fitting_performed": False, "holdout_accessed": False,
        "empirical_fit_authorized": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged-gzip", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    report = run_precheck(args.merged_gzip, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
