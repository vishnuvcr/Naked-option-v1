#!/usr/bin/env python3
"""Fail-closed Phase 8P R3 pre-fit audit.

Checks frozen inputs, ten-horizon registry integrity, data preflight support,
fold-block propagation, and eligibility accounting. This audit never fits models,
does not access the protected holdout, and never grants fitting authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "research" / "registry"
DATA = ROOT / "research" / "data"
GATES = ROOT / "research" / "gates"

PREREG_PATH = REG / "PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
LABEL_PATH = REG / "PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json"
CONFIG_PATH = REG / "PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json"
INDEX_PATH = REG / "PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
COMPAT_INDEX_PATH = REG / "PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
COMPAT_MATRIX_PATH = REG / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"
METHOD_MASTER_PATH = REG / "METHOD_REGISTRY_V2_R2.json"
DATA_MANIFEST_PATH = DATA / "DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json"
DATA_PIN_PATH = DATA / "PREDICTION_DATA_ARTIFACT_PIN_R3_2026-10-13.json"
PREPROCESS_PATH = DATA / "PREDICTION_DATA_PREPROCESSING_RULES_R3_2026-10-13.json"
CALENDAR_PATH = DATA / "NSE_CAPITAL_MARKET_SESSION_CALENDAR_R3_2026-10-13.json"
CALENDAR_SOURCE_PATH = DATA / "NSE_EQUITY_TRADING_CALENDAR_2021_2026_R3.json"
PREFLIGHT_PATH = GATES / "PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
DISPOSITION_PATH = GATES / "PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json"
DEFAULT_REPORT = GATES / "PREDICTION_R3_PREREQUISITE_AUDIT_2026-10-13.json"

FOLD_IDS = tuple(f"F{i:02d}" for i in range(1, 9))
INTRADAY_LABELS = (
    "INTRA_5M_UP_DOWN", "INTRA_15M_UP_DOWN", "INTRA_30M_UP_DOWN",
    "INTRA_60M_UP_DOWN", "INTRA_120M_UP_DOWN",
)
POSITIONAL_LABELS = (
    "POS_1D_UP_DOWN", "POS_2D_UP_DOWN", "POS_3D_UP_DOWN",
    "POS_5D_UP_DOWN", "POS_10D_UP_DOWN",
)
ALL_LABELS = INTRADAY_LABELS + POSITIONAL_LABELS
EXPECTED_BLOCKED_CELLS = {(label, "F01") for label in POSITIONAL_LABELS}


class GateError(ValueError):
    """A frozen research gate failed; do not continue to empirical fitting."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_json(path: Path) -> Any:
    if not path.is_file():
        raise GateError(f"REQUIRED_FILE_MISSING:{path.relative_to(ROOT).as_posix()}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GateError(f"INVALID_JSON:{path.relative_to(ROOT).as_posix()}:{type(exc).__name__}") from exc


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_repo_file(relative_path: str) -> Path:
    p = Path(relative_path)
    if p.is_absolute() or ".." in p.parts:
        raise GateError(f"UNSAFE_REPOSITORY_PATH:{relative_path}")
    return ROOT / p


def verify_source_pins(prereg: dict) -> dict:
    scope = prereg.get("scope")
    if not isinstance(scope, dict):
        raise GateError("PREREG_SCOPE_MISSING")
    source_paths = {
        "data_manifest_git_blob_sha1": DATA_MANIFEST_PATH,
        "label_manifest_git_blob_sha1": LABEL_PATH,
        "config_manifest_git_blob_sha1": CONFIG_PATH,
        "registry_index_git_blob_sha1": INDEX_PATH,
        "compatibility_matrix_git_blob_sha1": COMPAT_MATRIX_PATH,
        "method_registry_git_blob_sha1": METHOD_MASTER_PATH,
        "derived_encrypted_artifact_pin_git_blob_sha1": DATA_PIN_PATH,
        "data_preprocessing_rules_git_blob_sha1": PREPROCESS_PATH,
        "session_calendar_git_blob_sha1": CALENDAR_PATH,
        "session_calendar_source_git_blob_sha1": CALENDAR_SOURCE_PATH,
    }
    verified = {}
    for key, path in source_paths.items():
        raw = path.read_bytes() if path.is_file() else None
        expected = scope.get(key)
        actual = git_blob_sha1(raw) if raw is not None else None
        if not expected or actual != expected:
            raise GateError(f"SOURCE_GIT_BLOB_PIN_MISMATCH:{key}:expected={expected}:actual={actual}")
        verified[rel(path)] = {
            "git_blob_sha1": actual,
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
        }
    # The registry index and configuration manifest cross-pin each other and the labels.
    index = read_json(INDEX_PATH)
    config = read_json(CONFIG_PATH)
    labels = read_json(LABEL_PATH)
    if index.get("config_manifest_path") != rel(CONFIG_PATH):
        raise GateError("REGISTRY_INDEX_CONFIG_PATH_MISMATCH")
    if index.get("config_manifest_git_blob_sha1") != verified[rel(CONFIG_PATH)]["git_blob_sha1"]:
        raise GateError("REGISTRY_INDEX_CONFIG_BLOB_MISMATCH")
    if index.get("label_manifest_path") != rel(LABEL_PATH):
        raise GateError("REGISTRY_INDEX_LABEL_PATH_MISMATCH")
    if index.get("label_manifest_git_blob_sha1") != verified[rel(LABEL_PATH)]["git_blob_sha1"]:
        raise GateError("REGISTRY_INDEX_LABEL_BLOB_MISMATCH")
    if config.get("label_manifest_git_blob_sha1") != verified[rel(LABEL_PATH)]["git_blob_sha1"]:
        raise GateError("CONFIG_MANIFEST_LABEL_BLOB_MISMATCH")
    if prereg.get("scope", {}).get("registry_index_git_blob_sha1") != verified[rel(INDEX_PATH)]["git_blob_sha1"]:
        raise GateError("PREREG_REGISTRY_INDEX_BLOB_MISMATCH")
    return {"verified": verified, "index": index, "config": config, "labels": labels}


def validate_registry(prereg: dict, indexed: dict) -> dict:
    index, config, label_manifest = indexed["index"], indexed["config"], indexed["labels"]
    label_rows = label_manifest.get("labels")
    if not isinstance(label_rows, list):
        raise GateError("LABEL_MANIFEST_LABEL_ARRAY_MISSING")
    label_ids = [row.get("id") for row in label_rows if isinstance(row, dict)]
    if label_ids != list(ALL_LABELS) or len(set(label_ids)) != 10:
        raise GateError(f"TEN_HORIZON_LABEL_ORDER_OR_ID_MISMATCH:{label_ids}")
    if label_manifest.get("status") != "FROZEN_TEN_HORIZONS_DEVELOPER_VALIDATION_PENDING_NO_EMPIRICAL_RUNS":
        raise GateError("LABEL_MANIFEST_STATUS_UNEXPECTED")
    if config.get("configuration_count") != 40000 or config.get("shard_count") != 400:
        raise GateError("CONFIG_MANIFEST_TOTAL_OR_SHARD_COUNT_MISMATCH")
    if config.get("configurations_per_method") != 40 or config.get("configurations_per_shard") != 100:
        raise GateError("CONFIG_MANIFEST_SHARD_OR_METHOD_ACCOUNTING_MISMATCH")
    if index.get("configuration_record_count") != 40000 or index.get("method_record_count") != 1000:
        raise GateError("REGISTRY_INDEX_RECORD_COUNTS_MISMATCH")
    if index.get("configuration_shard_count") != 400 or len(config.get("config_shards", [])) != 400:
        raise GateError("REGISTRY_INDEX_CONFIG_SHARD_COUNT_MISMATCH")
    if config.get("label_manifest_git_blob_sha1") != git_blob_sha1(LABEL_PATH.read_bytes()):
        raise GateError("CONFIG_MANIFEST_LABEL_PIN_MISMATCH")

    configs_by_id = set()
    per_label = Counter()
    per_method = Counter()
    shard_summaries = []
    for entry in config["config_shards"]:
        rel_path = entry.get("path")
        if not isinstance(rel_path, str):
            raise GateError("CONFIG_SHARD_PATH_MISSING")
        path = safe_repo_file(rel_path)
        if not path.is_file():
            raise GateError(f"CONFIG_SHARD_MISSING:{rel_path}")
        raw = path.read_bytes()
        actual = sha256_bytes(raw)
        if actual != entry.get("sha256") or len(raw) != entry.get("byte_count"):
            raise GateError(f"CONFIG_SHARD_HASH_OR_BYTE_COUNT_MISMATCH:{rel_path}")
        payload = json.loads(raw.decode("utf-8"))
        rows = payload.get("configs")
        expected_count = entry.get("count")
        if not isinstance(rows, list) or len(rows) != expected_count or expected_count != 100:
            raise GateError(f"CONFIG_SHARD_ROW_COUNT_MISMATCH:{rel_path}")
        if rows[0].get("config_id") != entry.get("first_id") or rows[-1].get("config_id") != entry.get("last_id"):
            raise GateError(f"CONFIG_SHARD_ID_RANGE_MISMATCH:{rel_path}")
        for row in rows:
            cid, mid = row.get("config_id"), row.get("method_id")
            cfg = row.get("configuration")
            if not isinstance(cid, str) or cid in configs_by_id:
                raise GateError(f"CONFIG_ID_MISSING_OR_DUPLICATE:{cid}")
            if not isinstance(mid, str) or not isinstance(cfg, dict) or cfg.get("method_id") != mid:
                raise GateError(f"CONFIG_METHOD_LINKAGE_INVALID:{cid}")
            label = cfg.get("label_id")
            if label not in ALL_LABELS:
                raise GateError(f"CONFIG_LABEL_UNKNOWN:{cid}:{label}")
            if row.get("config_sha256") != sha256_bytes(canonical_json_bytes(cfg)):
                raise GateError(f"CONFIG_RECORD_DIGEST_MISMATCH:{cid}")
            if cfg.get("score_only_matured_targets") is not True:
                raise GateError(f"CONFIG_TARGET_MATURITY_FLAG_NOT_TRUE:{cid}")
            configs_by_id.add(cid)
            per_label[label] += 1
            per_method[mid] += 1
        shard_summaries.append({"path": rel_path, "sha256": actual, "records": len(rows)})

    if len(configs_by_id) != 40000:
        raise GateError(f"CONFIG_UNIQUE_COUNT_MISMATCH:{len(configs_by_id)}")
    if per_label != Counter({label: 4000 for label in ALL_LABELS}):
        raise GateError(f"CONFIG_PER_LABEL_ACCOUNTING_MISMATCH:{dict(per_label)}")
    if len(per_method) != 1000 or set(per_method.values()) != {40}:
        raise GateError("CONFIG_PER_METHOD_ACCOUNTING_MISMATCH")
    if prereg.get("scope", {}).get("configuration_count") != 40000:
        raise GateError("PREREG_CONFIG_COUNT_MISMATCH")
    if prereg.get("scope", {}).get("method_count") != 1000:
        raise GateError("PREREG_METHOD_COUNT_MISMATCH")
    if prereg.get("scope", {}).get("r2_pilot_only") is not False:
        raise GateError("PREREG_R2_PILOT_ONLY_FLAG_NOT_CLOSED")

    return {
        "label_count": len(label_ids),
        "labels": list(label_ids),
        "configuration_count": len(configs_by_id),
        "unique_configurations": len(configs_by_id),
        "configurations_per_label": dict(sorted(per_label.items())),
        "method_count": len(per_method),
        "configurations_per_method": 40,
        "verified_config_shards": len(shard_summaries),
        "config_shard_hashes": shard_summaries,
    }


def validate_compatibility() -> dict:
    idx = read_json(COMPAT_INDEX_PATH)
    if idx.get("record_count") != 1000 or idx.get("allow_in_principle_count") != 426 or idx.get("blocked_count") != 574:
        raise GateError("COMPATIBILITY_INDEX_COUNTS_MISMATCH")
    if idx.get("empirically_eligible_count") != 0:
        raise GateError("COMPATIBILITY_INDEX_IMPROPERLY_AUTHORIZES_FITTING")
    all_ids = set()
    decision_counts = Counter()
    implementation_counts = Counter()
    empirically_eligible = 0
    verified = []
    shards = idx.get("shards")
    if not isinstance(shards, list) or len(shards) != 40:
        raise GateError("COMPATIBILITY_SHARD_COUNT_MISMATCH")
    for entry in shards:
        p = safe_repo_file(entry["path"])
        if not p.is_file():
            raise GateError(f"COMPATIBILITY_SHARD_MISSING:{entry['path']}")
        raw = p.read_bytes()
        if sha256_bytes(raw) != entry.get("sha256") or len(raw) != entry.get("bytes"):
            raise GateError(f"COMPATIBILITY_SHARD_HASH_OR_BYTE_COUNT_MISMATCH:{entry['path']}")
        rows = json.loads(raw.decode("utf-8")).get("rows")
        if not isinstance(rows, list) or len(rows) != entry.get("record_count") or len(rows) != 25:
            raise GateError(f"COMPATIBILITY_SHARD_COUNT_MISMATCH:{entry['path']}")
        if rows[0].get("method_id") != entry.get("first_method_id") or rows[-1].get("method_id") != entry.get("last_method_id"):
            raise GateError(f"COMPATIBILITY_SHARD_RANGE_MISMATCH:{entry['path']}")
        for row in rows:
            mid = row.get("method_id")
            if not isinstance(mid, str) or mid in all_ids:
                raise GateError(f"METHOD_ID_MISSING_OR_DUPLICATE:{mid}")
            if row.get("eligible_for_empirical_fitting") is not False:
                empirically_eligible += 1
            all_ids.add(mid)
            decision_counts[row.get("compatibility_decision", "MISSING")] += 1
            implementation_counts[row.get("implementation_status", "MISSING")] += 1
        verified.append({"path": entry["path"], "sha256": sha256_bytes(raw), "records": len(rows)})
    if len(all_ids) != 1000:
        raise GateError(f"METHOD_UNIQUE_COUNT_MISMATCH:{len(all_ids)}")
    if decision_counts != Counter({"ALLOW_IN_PRINCIPLE": 426, "BLOCK": 574}):
        raise GateError(f"METHOD_COMPATIBILITY_DECISION_COUNTS_MISMATCH:{dict(decision_counts)}")
    if empirically_eligible != 0:
        raise GateError(f"METHOD_FLAGS_IMPROPERLY_ENABLE_FIT_COUNT:{empirically_eligible}")
    if implementation_counts != Counter({"NOT_IMPLEMENTED_OR_TESTER_APPROVED": 1000}):
        raise GateError(f"METHOD_IMPLEMENTATION_STATUS_CHANGED_UNEXPECTEDLY:{dict(implementation_counts)}")
    return {
        "method_count": len(all_ids),
        "allow_in_principle": decision_counts["ALLOW_IN_PRINCIPLE"],
        "blocked": decision_counts["BLOCK"],
        "implementation_status_counts": dict(implementation_counts),
        "empirically_eligible_methods": empirically_eligible,
        "verified_compatibility_shards": len(verified),
        "shard_hashes": verified,
    }


def validate_preflight(preflight: dict, label_ids: tuple[str, ...] = ALL_LABELS) -> dict:
    if preflight.get("status") != "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS":
        raise GateError(f"DATA_PREFLIGHT_STATUS_NOT_ACCEPTABLE:{preflight.get('status')}")
    for key in ("canonical_hash_matches",):
        if preflight.get(key) is not True:
            raise GateError(f"DATA_PREFLIGHT_{key.upper()}_NOT_TRUE")
    for key in ("holdout_accessed", "model_fitting_performed", "plaintext_uploaded", "raw_rows_emitted", "raw_rows_retained"):
        if preflight.get(key) is not False:
            raise GateError(f"DATA_PREFLIGHT_SAFETY_FLAG_NOT_FALSE:{key}")
    if preflight.get("expected_rows") != 8999865 or preflight.get("rows_read") != 8999865:
        raise GateError("DATA_PREFLIGHT_ROW_COUNT_MISMATCH")
    if preflight.get("rows_by_type") != {"OPTION": 8490723, "SPOT": 509142}:
        raise GateError("DATA_PREFLIGHT_ROW_TYPE_COUNTS_MISMATCH")
    if preflight.get("timestamp_min_local", "")[:10] != "2021-10-11":
        raise GateError("DATA_PREFLIGHT_START_DATE_MISMATCH")
    if not str(preflight.get("timestamp_max_local", "")).startswith("2026-10-09"):
        raise GateError("DATA_PREFLIGHT_END_DATE_COVERAGE_MISMATCH")
    if preflight.get("canonical_uncompressed_csv_sha256") != preflight.get("expected_canonical_csv_sha256"):
        raise GateError("DATA_PREFLIGHT_CANONICAL_SHA_MISMATCH")

    rows = preflight.get("label_sample_support")
    if not isinstance(rows, list):
        raise GateError("DATA_PREFLIGHT_LABEL_SUPPORT_MISSING")
    seen = set()
    blocked = set()
    counts = Counter()
    for row in rows:
        label, fold = row.get("label_id"), row.get("fold_id")
        if label not in label_ids or fold not in FOLD_IDS:
            raise GateError(f"DATA_PREFLIGHT_UNKNOWN_LABEL_FOLD:{label}:{fold}")
        cell = (label, fold)
        if cell in seen:
            raise GateError(f"DATA_PREFLIGHT_DUPLICATE_CELL:{label}:{fold}")
        seen.add(cell)
        passed = row.get("passes_frozen_data_minima")
        reasons = row.get("block_reasons", [])
        if type(passed) is not bool:
            raise GateError(f"DATA_PREFLIGHT_INVALID_PASS_FLAG:{label}:{fold}")
        if passed:
            if reasons:
                raise GateError(f"DATA_PREFLIGHT_PASS_CELL_HAS_BLOCK_REASON:{label}:{fold}")
            counts["pass"] += 1
        else:
            if not isinstance(reasons, list) or not reasons:
                raise GateError(f"DATA_PREFLIGHT_BLOCKED_CELL_NO_REASON:{label}:{fold}")
            missing, possible, fraction = row.get("missing_target_pairs"), row.get("possible_target_pairs"), row.get("target_pair_missing_fraction")
            if not isinstance(missing, int) or not isinstance(possible, int) or possible <= 0 or not isinstance(fraction, (int, float)):
                raise GateError(f"DATA_PREFLIGHT_BLOCKED_CELL_MISSINGNESS_FIELDS:{label}:{fold}")
            calculated = missing / possible
            if abs(calculated - fraction) > 1e-12 or calculated <= 0.01:
                raise GateError(f"DATA_PREFLIGHT_BLOCKED_CELL_FRACTION_INVALID:{label}:{fold}")
            if reasons != ["TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT"]:
                raise GateError(f"DATA_PREFLIGHT_BLOCKED_CELL_REASON_UNEXPECTED:{label}:{fold}:{reasons}")
            blocked.add(cell)
            counts["blocked"] += 1
    expected_grid = {(label, fold) for label in label_ids for fold in FOLD_IDS}
    if seen != expected_grid:
        raise GateError(f"DATA_PREFLIGHT_FOLD_GRID_INCOMPLETE:missing={sorted(expected_grid-seen)}")
    if blocked != EXPECTED_BLOCKED_CELLS:
        raise GateError(f"DATA_PREFLIGHT_SCOPED_BLOCKS_CHANGED:{sorted(blocked)}")
    if counts != Counter({"pass": 75, "blocked": 5}):
        raise GateError(f"DATA_PREFLIGHT_CELL_COUNTS_MISMATCH:{dict(counts)}")
    return {
        "status": preflight["status"],
        "canonical_hash_matches": True,
        "rows_read": preflight["rows_read"],
        "row_type_counts": preflight["rows_by_type"],
        "label_fold_cells": len(seen),
        "supported_cells": counts["pass"],
        "blocked_cells": counts["blocked"],
        "blocked_cell_ids": [{"label_id": label, "fold_id": fold} for label, fold in sorted(blocked)],
    }


def validate_disposition(disposition: dict) -> dict:
    rows = disposition.get("records")
    if disposition.get("empirical_fit_authorized") is not False:
        raise GateError("DISPOSITION_MANIFEST_IMPROPERLY_AUTHORIZES_FITTING")
    if not isinstance(rows, list) or len(rows) != 40000:
        raise GateError("DISPOSITION_RECORD_COUNT_MISMATCH")
    if disposition.get("record_count") != 40000 or disposition.get("unique_config_count") != 40000:
        raise GateError("DISPOSITION_AGGREGATE_COUNT_MISMATCH")
    ids = set()
    counts = Counter()
    for row in rows:
        cid = row.get("config_id")
        if not isinstance(cid, str) or cid in ids:
            raise GateError(f"DISPOSITION_CONFIG_ID_MISSING_OR_DUPLICATE:{cid}")
        ids.add(cid)
        if row.get("empirical_fit_authorized") is not False:
            raise GateError(f"DISPOSITION_CONFIG_IMPROPERLY_AUTHORIZES_FITTING:{cid}")
        label = row.get("label_id")
        if label not in ALL_LABELS:
            raise GateError(f"DISPOSITION_CONFIG_HAS_UNKNOWN_LABEL:{cid}:{label}")
        if row.get("disposition") == "ELIGIBLE_PENDING_EXECUTOR_GATE":
            raise GateError(f"CONFIG_MARKED_ELIGIBLE_BEFORE_IMPLEMENTATION_APPROVAL:{cid}")
        expected_blocked = ["F01"] if label in POSITIONAL_LABELS else []
        if row.get("blocked_outer_fold_ids") != expected_blocked:
            raise GateError(f"DISPOSITION_BLOCKED_FOLDS_NOT_PROPAGATED:{cid}")
        if row.get("supported_outer_fold_ids") != [f for f in FOLD_IDS if f not in expected_blocked]:
            raise GateError(f"DISPOSITION_SUPPORTED_FOLDS_NOT_PROPAGATED:{cid}")
        counts[row.get("disposition", "MISSING")] += 1
    expected_counts = Counter({
        "BLOCKED_IMPLEMENTATION_OR_AUTHORIZATION": 17040,
        "BLOCKED_METHOD_COMPATIBILITY": 22960,
    })
    if counts != expected_counts:
        raise GateError(f"DISPOSITION_ACCOUNTING_CHANGED:{dict(counts)}")
    if disposition.get("eligible_fold_label_cell_count") != 75 or disposition.get("blocked_fold_label_cell_count") != 5:
        raise GateError("DISPOSITION_FOLD_LABEL_CELL_SUMMARY_CHANGED")
    return {
        "configuration_count": len(ids),
        "disposition_counts": dict(sorted(counts.items())),
        "eligible_fold_label_cells": disposition["eligible_fold_label_cell_count"],
        "blocked_fold_label_cells": disposition["blocked_fold_label_cell_count"],
        "all_fit_flags_false": True,
    }


def build_report() -> dict:
    prereg = read_json(PREREG_PATH)
    if prereg.get("schema_version") != "prediction-preregistration-v3-r3":
        raise GateError("PREREG_SCHEMA_VERSION_MISMATCH")
    if prereg.get("gate", {}).get("empirical_fitting_authorized_by_builder") is not False:
        raise GateError("PREREG_BUILDER_GATE_NOT_CLOSED")
    if prereg.get("gate", {}).get("holdout_access_authorized") is not False:
        raise GateError("PREREG_HOLDOUT_GATE_NOT_CLOSED")

    pinned = verify_source_pins(prereg)
    registry_report = validate_registry(prereg, pinned)
    compatibility_report = validate_compatibility()
    preflight = validate_preflight(read_json(PREFLIGHT_PATH))
    disposition_report = validate_disposition(read_json(DISPOSITION_PATH))
    data_pin = read_json(DATA_PIN_PATH)
    pin_summary = data_pin.get("verified_summary", {})
    if pin_summary.get("encrypted_members_checked") != 61 or pin_summary.get("encrypted_member_hash_or_size_mismatches") != 0:
        raise GateError("ENCRYPTED_ARTIFACT_PART_AUDIT_NOT_CLEAN")
    if pin_summary.get("declared_part_row_count_sum") != 8999865 or pin_summary.get("row_count_by_month_sum") != 8999865:
        raise GateError("ENCRYPTED_ARTIFACT_PART_ROW_ACCOUNTING_MISMATCH")
    if pin_summary.get("plaintext_decrypted") is not False or pin_summary.get("model_fitting_performed") is not False or pin_summary.get("holdout_accessed") is not False:
        raise GateError("ENCRYPTED_ARTIFACT_PIN_SAFETY_FLAGS_NOT_CLOSED")

    # These are readiness findings only. They deliberately do not flip any method flags
    # or authorize training. An empirical runner must separately demonstrate method
    # implementation contracts, train-only transformations, calibration leakage tests,
    # and the execution-specific frozen result schema.
    return {
        "schema_version": "prediction-r3-prerequisite-audit-v1",
        "date": "2026-10-13",
        "audit_generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_DATA_AND_REGISTRY_PREREQUISITES_WITH_SCOPED_BLOCKS",
        "source_pin_verification": pinned["verified"],
        "registry": registry_report,
        "compatibility": compatibility_report,
        "data_preflight": preflight,
        "eligibility_disposition": disposition_report,
        "execution_gate": {
            "empirical_fit_authorized": False,
            "holdout_accessed": False,
            "strategy_selection_authorized": False,
            "reason_code": "BLOCKED_ALL_METHODS_UNIMPLEMENTED_OR_NOT_APPROVED",
            "detail": "All 1,000 compatibility records remain NOT_IMPLEMENTED_OR_TESTER_APPROVED and all method/config fit flags remain false. Complete and test the development-fold executor and method implementations before authorizing a fit.",
            "next_gate": "IMPLEMENT_AND_TEST_DEVELOPMENT_FOLD_EXECUTOR_WITH_EXPLICIT_METHOD_ALLOWLIST",
        },
        "no_raw_or_plaintext_data_in_report": True,
        "model_fitting_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=rel(DEFAULT_REPORT))
    args = parser.parse_args()
    report = build_report()
    out = safe_repo_file(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    summary = {
        "status": report["status"],
        "report": args.report,
        "configurations": report["registry"]["configuration_count"],
        "methods": report["compatibility"]["method_count"],
        "supported_label_fold_cells": report["data_preflight"]["supported_cells"],
        "blocked_label_fold_cells": report["data_preflight"]["blocked_cells"],
        "empirical_fit_authorized": False,
        "execution_gate": report["execution_gate"]["reason_code"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateError as exc:
        print(json.dumps({"status": "BLOCKED_FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        raise SystemExit(2)
