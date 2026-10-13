#!/usr/bin/env python3
"""Build a deterministic, fail-closed disposition for the frozen Phase 8P R3 registry.

Registry accounting only: no market rows are loaded and no model is fitted. Standing permission removes repeated manual authorization, but actual fitting remains blocked until method implementation, data, and executor gates pass. Fold-specific data blocks remain fold-specific.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = "research/registry/PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
COMPAT_INDEX_PATH = "research/registry/PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
PREFLIGHT_PATH = "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
CONFIG_MANIFEST_PATH = "research/registry/PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json"
COMPAT_MATRIX_PATH = "research/registry/PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"
OUT_PATH = "research/gates/PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json"
IMPLEMENTATION_GATE_PATH = "research/gates/PREDICTION_PM0001_IMPLEMENTATION_GATE_R3_2026-10-14.json"
FOLD_IDS = tuple(f"F{i:02d}" for i in range(1, 9))

GIT_BLOB_PINS = {
    INDEX_PATH: "8b7e1f1967cd51146573e43cde8462d64980e375",
    COMPAT_INDEX_PATH: "ebe233aca9e3d12fb3a7af1af579261d4c4e872c",
    PREFLIGHT_PATH: "9da9692d67b5fda6271e021c77e429d1b9f32b3c",
    CONFIG_MANIFEST_PATH: "258b789a746186f2b83348a715a9da0d160a1baa",
    COMPAT_MATRIX_PATH: "267f754f2dffbea53f45e4470d5996bfef785971",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def verify_pinned_sources() -> dict:
    for rel_path, expected in GIT_BLOB_PINS.items():
        path = ROOT / rel_path
        if not path.is_file():
            raise ValueError(f"PINNED_SOURCE_MISSING:{rel_path}")
        actual = git_blob_sha1(path.read_bytes())
        if actual != expected:
            raise ValueError(f"PINNED_SOURCE_GIT_BLOB_MISMATCH:{rel_path}:{actual}")
    index = read_json(INDEX_PATH)
    if index.get("config_manifest_path") != CONFIG_MANIFEST_PATH:
        raise ValueError("CONFIG_MANIFEST_PATH_PIN_MISMATCH")
    if index.get("config_manifest_git_blob_sha1") != GIT_BLOB_PINS[CONFIG_MANIFEST_PATH]:
        raise ValueError("CONFIG_MANIFEST_BLOB_PIN_MISMATCH")
    if index.get("compatibility_matrix_path") != COMPAT_MATRIX_PATH:
        raise ValueError("COMPATIBILITY_MATRIX_PATH_PIN_MISMATCH")
    if index.get("compatibility_matrix_git_blob_sha1") != GIT_BLOB_PINS[COMPAT_MATRIX_PATH]:
        raise ValueError("COMPATIBILITY_MATRIX_BLOB_PIN_MISMATCH")
    gate_path = ROOT / IMPLEMENTATION_GATE_PATH
    if not gate_path.is_file():
        raise ValueError("PM0001_IMPLEMENTATION_GATE_MISSING")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("method_id") != "PM0001" or gate.get("status") != "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY":
        raise ValueError("PM0001_IMPLEMENTATION_GATE_STATUS_INVALID")
    verification = gate.get("verification", {})
    if verification.get("conclusion") != "success" or verification.get("source_data_loaded") is not False:
        raise ValueError("PM0001_IMPLEMENTATION_GATE_CI_OR_SCOPE_INVALID")
    if verification.get("empirical_model_fit") is not False or verification.get("holdout_accessed") is not False:
        raise ValueError("PM0001_IMPLEMENTATION_GATE_SCOPE_INVALID")
    for rel_path, expected in gate.get("source_blob_pins", {}).items():
        path = ROOT / rel_path
        if not path.is_file() or git_blob_sha1(path.read_bytes()) != expected:
            raise ValueError(f"PM0001_IMPLEMENTATION_SOURCE_PIN_MISMATCH:{rel_path}")
    if gate.get("empirical_fit_authorized") is not False or gate.get("manual_authorization_required") is not False:
        raise ValueError("PM0001_IMPLEMENTATION_GATE_AUTHORIZATION_FLAGS_INVALID")
    return gate


def load_verified_shards(index: dict, key: str, path_key: str, hash_key: str, count_key: str):
    rows = []
    seen = set()
    for shard in index[key]:
        raw = (ROOT / shard[path_key]).read_bytes()
        if sha256(raw) != shard[hash_key]:
            raise ValueError(f"SHARD_HASH_MISMATCH:{shard[path_key]}")
        payload = json.loads(raw.decode("utf-8"))
        records = payload.get("configs", payload.get("rows"))
        if not isinstance(records, list) or len(records) != shard[count_key]:
            raise ValueError(f"SHARD_COUNT_MISMATCH:{shard[path_key]}")
        for rec in records:
            identity = rec.get("config_id") if "config_id" in rec else rec.get("method_id")
            if not identity or identity in seen:
                raise ValueError(f"DUPLICATE_OR_MISSING_ID:{identity}")
            seen.add(identity)
            rows.append(rec)
    return rows


def validate_fold_support_rows(rows: list[dict], expected_labels: set[str]) -> dict[str, dict[str, dict]]:
    if not isinstance(rows, list):
        raise ValueError("PREFLIGHT_FOLD_SUPPORT_MISSING")
    by_label: dict[str, dict[str, dict]] = {}
    seen = set()
    for row in rows:
        label, fold = row.get("label_id"), row.get("fold_id")
        passed, reasons = row.get("passes_frozen_data_minima"), row.get("block_reasons", [])
        if label not in expected_labels or fold not in FOLD_IDS:
            raise ValueError(f"UNKNOWN_LABEL_OR_FOLD_IN_PREFLIGHT:{label}:{fold}")
        if (label, fold) in seen:
            raise ValueError(f"DUPLICATE_PREFLIGHT_LABEL_FOLD:{label}:{fold}")
        if type(passed) is not bool:
            raise ValueError(f"INVALID_PREFLIGHT_PASS_FLAG:{label}:{fold}")
        if passed and reasons:
            raise ValueError(f"PASSING_FOLD_HAS_BLOCK_REASONS:{label}:{fold}")
        if not passed and (not isinstance(reasons, list) or not reasons):
            raise ValueError(f"BLOCKED_FOLD_MISSING_REASON:{label}:{fold}")
        seen.add((label, fold))
        by_label.setdefault(label, {})[fold] = row
    expected = {(label, fold) for label in expected_labels for fold in FOLD_IDS}
    if seen != expected:
        raise ValueError(
            f"PREFLIGHT_FOLD_GRID_MISMATCH:missing={sorted(expected-seen)}:extra={sorted(seen-expected)}"
        )
    return by_label


def classify(config: dict, method: dict, fold_support_by_label: dict[str, dict[str, dict]], implementation_gate: dict | None = None) -> dict:
    c = config["configuration"]
    label_id = c["label_id"]
    label_support = fold_support_by_label[label_id]
    blocked_folds = sorted(
        fold for fold, item in label_support.items()
        if item["passes_frozen_data_minima"] is False
    )
    supported_folds = [fold for fold in FOLD_IDS if fold not in blocked_folds]

    implementation_passed = (
        implementation_gate is not None
        and method.get("method_id") == implementation_gate.get("method_id") == "PM0001"
        and implementation_gate.get("status") == "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY"
    )
    if method["compatibility_decision"] == "BLOCK":
        disposition = "BLOCKED_METHOD_COMPATIBILITY"
        reason = method.get("decision_code", "COMPATIBILITY_BLOCK")
    elif method.get("eligible_for_empirical_fitting") is not True and not implementation_passed:
        disposition = "BLOCKED_IMPLEMENTATION_NOT_READY"
        reason = method.get("implementation_status", "IMPLEMENTATION_NOT_DEMONSTRATED")
    elif len(blocked_folds) == len(FOLD_IDS):
        disposition = "BLOCKED_DATA_SUPPORT"
        reason = "ALL_REGISTERED_OUTER_FOLDS_BLOCKED_BY_FROZEN_SAMPLE_RULE"
    else:
        disposition = "ELIGIBLE_PENDING_EXECUTOR_GATE"
        reason = "METHOD_AND_REMAINING_FOLD_SUPPORT_PASS_BUT_EXECUTOR_AUTHORIZATION_MUST_STILL_PASS"

    return {
        "config_id": config["config_id"],
        "config_sha256": config["config_sha256"],
        "method_id": config["method_id"],
        "label_id": label_id,
        "stratum": c["stratum"],
        "disposition": disposition,
        "reason_code": reason,
        "blocked_outer_fold_ids": blocked_folds,
        "supported_outer_fold_ids": supported_folds,
        "empirical_fit_authorized": False,
        "manual_authorization_required": False,
    }


def build_manifest(configs: list[dict], methods: list[dict], preflight: dict, source_pins: dict, implementation_gate: dict | None = None) -> dict:
    if preflight.get("canonical_hash_matches") is not True:
        raise ValueError("PREFLIGHT_CANONICAL_DATA_HASH_NOT_VERIFIED")
    if preflight.get("holdout_accessed") is not False:
        raise ValueError("PREFLIGHT_HOLDOUT_STATE_NOT_CLOSED")
    if preflight.get("model_fitting_performed") is not False:
        raise ValueError("PREFLIGHT_MUST_BE_MODEL_FREE")
    method_map = {m["method_id"]: m for m in methods}
    if len(method_map) != len(methods):
        raise ValueError("DUPLICATE_METHOD_ID")
    expected_labels = {cfg["configuration"]["label_id"] for cfg in configs}
    fold_support = validate_fold_support_rows(preflight.get("label_sample_support"), expected_labels)
    out = []
    for cfg in configs:
        mid = cfg.get("method_id")
        if mid not in method_map:
            raise ValueError(f"CONFIG_METHOD_NOT_REGISTERED:{mid}")
        out.append(classify(cfg, method_map[mid], fold_support, implementation_gate))
    if len({row["config_id"] for row in out}) != len(out):
        raise ValueError("DUPLICATE_CONFIG_ID")

    counts = dict(sorted(Counter(row["disposition"] for row in out).items()))
    blocked_cells = []
    for label in sorted(fold_support):
        for fold in FOLD_IDS:
            item = fold_support[label][fold]
            if item["passes_frozen_data_minima"] is False:
                blocked_cells.append({
                    "label_id": label,
                    "fold_id": fold,
                    "block_reasons": item["block_reasons"],
                    "missing_target_pairs": item.get("missing_target_pairs"),
                    "possible_target_pairs": item.get("possible_target_pairs"),
                    "target_pair_missing_fraction": item.get("target_pair_missing_fraction"),
                })
    eligible_cells = sum(
        1 for folds in fold_support.values()
        for item in folds.values() if item["passes_frozen_data_minima"] is True
    )
    return {
        "schema_version": "prediction-eligibility-disposition-r3-v2",
        "research_date": "2026-10-13",
        "source_pins": source_pins,
        "record_count": len(out),
        "unique_config_count": len({row["config_id"] for row in out}),
        "empirical_fit_authorized": False,
        "manual_authorization_required": False,
        "standing_permission_path": "research/governance/STANDING_RESEARCH_EXECUTION_PERMISSION_2026-10-14.md",
        "disposition_counts": counts,
        "fold_ids": list(FOLD_IDS),
        "eligible_fold_label_cell_count": eligible_cells,
        "blocked_fold_label_cell_count": len(blocked_cells),
        "blocked_fold_label_cells": blocked_cells,
        "records": sorted(out, key=lambda row: row["config_id"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=OUT_PATH)
    args = parser.parse_args()
    verify_pinned_sources()
    index = read_json(INDEX_PATH)
    comp_index = read_json(COMPAT_INDEX_PATH)
    preflight = read_json(PREFLIGHT_PATH)
    configs = load_verified_shards(index, "config_shards", "path", "sha256", "record_count")
    methods = load_verified_shards(comp_index, "shards", "path", "sha256", "record_count")
    if len(configs) != index.get("config_count", 40000):
        raise ValueError(f"CONFIG_TOTAL_MISMATCH:{len(configs)}")
    if len(methods) != comp_index.get("record_count", 1000):
        raise ValueError(f"METHOD_TOTAL_MISMATCH:{len(methods)}")
    pins = {
        "registry_index_git_blob_sha1": GIT_BLOB_PINS[INDEX_PATH],
        "registry_index_path": INDEX_PATH,
        "compatibility_index_git_blob_sha1": GIT_BLOB_PINS[COMPAT_INDEX_PATH],
        "compatibility_index_path": COMPAT_INDEX_PATH,
        "compatibility_matrix_git_blob_sha1": GIT_BLOB_PINS[COMPAT_MATRIX_PATH],
        "compatibility_matrix_path": COMPAT_MATRIX_PATH,
        "preflight_git_blob_sha1": GIT_BLOB_PINS[PREFLIGHT_PATH],
        "preflight_path": PREFLIGHT_PATH,
        "config_manifest_git_blob_sha1": GIT_BLOB_PINS[CONFIG_MANIFEST_PATH],
        "config_manifest_path": CONFIG_MANIFEST_PATH,
        "canonical_uncompressed_csv_sha256": preflight["canonical_uncompressed_csv_sha256"],
        "preflight_status": preflight["status"],
    }
    manifest = build_manifest(configs, methods, preflight, pins)
    if manifest["record_count"] != 40000 or manifest["unique_config_count"] != 40000:
        raise ValueError("EXPECTED_40000_UNIQUE_CONFIGURATIONS")
    if manifest["eligible_fold_label_cell_count"] != 75 or manifest["blocked_fold_label_cell_count"] != 5:
        raise ValueError("PREFLIGHT_FOLD_SUPPORT_COUNTS_CHANGED_REQUIRES_REVIEW")
    pending = [row for row in manifest["records"] if row["disposition"] == "ELIGIBLE_PENDING_EXECUTOR_GATE"]
    if len(pending) != 40 or any(row["method_id"] != "PM0001" for row in pending):
        raise ValueError(f"EXPECTED_ONLY_40_PM0001_CONFIGS_PENDING_EXECUTOR_GATE:{len(pending)}")
    if any(row["empirical_fit_authorized"] for row in pending):
        raise ValueError("IMPLEMENTATION_GATE_MUST_NOT_AUTHORIZE_EMPIRICAL_FITTING")
    if sum(manifest["disposition_counts"].values()) != 40000:
        raise ValueError("DISPOSITION_ACCOUNTING_MISMATCH")
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS_REGISTRY_DISPOSITION_ONLY",
        "output": args.output,
        "record_count": manifest["record_count"],
        "unique_config_count": manifest["unique_config_count"],
        "disposition_counts": manifest["disposition_counts"],
        "eligible_fold_label_cell_count": manifest["eligible_fold_label_cell_count"],
        "blocked_fold_label_cell_count": manifest["blocked_fold_label_cell_count"],
        "empirical_fit_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
