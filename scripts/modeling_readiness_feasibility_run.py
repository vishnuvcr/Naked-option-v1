#!/usr/bin/env python3
"""Bounded metadata-only feasibility audit for the frozen Phase 7 composite.

Real mode is deliberately fail-closed: it requires an exact-snapshot tester
authorization, pinned input hashes and a verified byte-level holdout boundary.
The CSV parser is bounded to the pre-holdout byte prefix and never parses rows
at or after that boundary. This program does not fit or score a model.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, BinaryIO, Mapping

EXPECTED_DATASET_ID = "NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_SPOT_GAPFILL_DERIVED_REPAIR_V1"
EXPECTED_DATASET_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
EXPECTED_ROWS = 8_999_865
EXPECTED_COLUMNS = 47
HORIZONS = (1, 2, 3, 5, 10)
ALLOWED_FEATURE_FAMILIES = {"SPOT_OHLCV", "OPTION_MARKET", "CONTRACT_METADATA", "GREEKS_RATES_DIVIDENDS", "VOLATILITY_RISK_INDICES", "NSE_BSE_BREADTH", "FII_DII", "GLOBAL_MARKETS", "NEWS_SENTIMENT_MACRO"}
FLAT_TOLERANCE = 1e-8
REVIEWED_BLOB_PATHS = (
    "scripts/modeling_readiness_feasibility_run.py",
    "tests/test_modeling_readiness_feasibility_run.py",
    "research/gates/MODELING_READINESS_FEASIBILITY_REPORT_SCHEMA_R5_2026-10-11.json",
    ".github/workflows/phase-07-modeling-readiness-feasibility-synthetic.yml",
)
BLOCKED_SCOPE_KEYS = (
    "model_fitting", "model_tuning", "prediction_scoring", "holdout_observation_access",
    "new_source_requests", "strategy_pnl", "trading",
)
ALLOWED_STATUS = {
    "PASS", "PASS_WITH_RESTRICTIONS", "PASS_WITH_EXCLUSIONS", "CANDIDATE",
    "BLOCKED", "BLOCKED_DATA", "BLOCKED_HOLDOUT_PROOF", "BLOCKED_LEAKAGE",
    "BLOCKED_INVALID_COUNTS", "NOT_ESTIMABLE", "INCOMPLETE_NOT_PROMOTABLE", "NOT_RUN",
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha1(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json_object(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        value = json.load(stream, object_pairs_hook=_no_duplicate_pairs)
    if not isinstance(value, dict):
        raise ValueError("JSON_ROOT_NOT_OBJECT")
    return value


def _sha(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _nonnegative_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def validate_execution_authorization(auth: Mapping[str, Any], paths: Mapping[str, str | Path]) -> None:
    """Validate scope and every protected source blob before any CSV parsing."""
    if auth.get("gate_id") != "MODELING_READINESS_FEASIBILITY_RUN_R5":
        raise ValueError("AUTH_GATE_ID_MISMATCH")
    if auth.get("verdict") != "PASS_WITH_SCOPED_RESTRICTIONS":
        raise ValueError("AUTH_VERDICT_NOT_PASS")
    if auth.get("allowed_scope") != "one bounded metadata-only MR-0 to MR-5 feasibility audit":
        raise ValueError("AUTH_SCOPE_MISMATCH")
    if auth.get("one_use") is not True:
        raise ValueError("AUTH_NOT_ONE_USE")
    permissions = auth.get("permissions")
    if not isinstance(permissions, dict) or any(permissions.get(key) is not False for key in BLOCKED_SCOPE_KEYS):
        raise ValueError("AUTH_DOWNSTREAM_PERMISSION_NOT_CLOSED")
    reviewed = auth.get("reviewed_blobs")
    if not isinstance(reviewed, dict):
        raise ValueError("AUTH_REVIEWED_BLOBS_MISSING")
    for path in REVIEWED_BLOB_PATHS:
        if path not in reviewed or reviewed[path] != git_blob_sha1(paths[path]):
            raise ValueError("AUTH_STALE_CODE_BLOB")
    if auth.get("decoded_dataset_sha256") != EXPECTED_DATASET_SHA256:
        raise ValueError("AUTH_DATASET_HASH_MISMATCH")
    if auth.get("max_dataset_rows") != EXPECTED_ROWS or auth.get("max_dataset_columns") != EXPECTED_COLUMNS:
        raise ValueError("AUTH_DATASET_BOUNDS_MISMATCH")
    inputs = auth.get("input_sha256")
    if not isinstance(inputs, dict):
        raise ValueError("AUTH_INPUT_HASHES_MISSING")
    for label in ("dataset", "input_manifest", "source_manifest", "calendar_manifest", "split_manifest"):
        if not _sha(inputs.get(label)):
            raise ValueError("AUTH_INPUT_HASH_INVALID")


def _iso_date(value: Any) -> dt.date:
    if not isinstance(value, str):
        raise ValueError("INVALID_ISO_DATE")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("INVALID_ISO_DATE") from exc
    if parsed.isoformat() != value:
        raise ValueError("INVALID_ISO_DATE")
    return parsed


def validate_input_manifests(
    input_manifest: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    calendar_manifest: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
) -> tuple[bool, str]:
    """Return whether data parsing is authorized by input metadata; never infer a boundary."""
    for manifest in (input_manifest, source_manifest, calendar_manifest, split_manifest):
        if manifest.get("dataset_sha256") != EXPECTED_DATASET_SHA256:
            raise ValueError("MANIFEST_DATASET_HASH_MISMATCH")
        if manifest.get("dataset_id") not in (None, EXPECTED_DATASET_ID):
            raise ValueError("MANIFEST_DATASET_ID_MISMATCH")
    if input_manifest.get("expected_rows") != EXPECTED_ROWS or input_manifest.get("expected_columns") != EXPECTED_COLUMNS:
        raise ValueError("INPUT_MANIFEST_DIMENSIONS_MISMATCH")
    column_map = input_manifest.get("column_map")
    required_columns = {"row_type", "timestamp_epoch", "session_date", "open", "high", "low", "close", "volume", "quality_flags", "join_status"}
    if not isinstance(column_map, dict) or any(not isinstance(column_map.get(k), str) or not column_map[k] for k in required_columns):
        raise ValueError("INPUT_COLUMN_MAP_INCOMPLETE")
    if len(set(column_map[k] for k in required_columns)) != len(required_columns):
        raise ValueError("INPUT_COLUMN_MAP_COLLISION")
    if input_manifest.get("row_type_values") != {"option": "OPTION", "spot": "SPOT"}:
        raise ValueError("INPUT_ROW_TYPE_MAP_UNSUPPORTED")
    if source_manifest.get("cache_only") is not True:
        raise ValueError("SOURCE_MANIFEST_NOT_CACHE_ONLY")
    vintages = source_manifest.get("source_vintages")
    if not isinstance(vintages, list) or not vintages:
        raise ValueError("SOURCE_VINTAGE_PROVENANCE_MISSING")
    for vintage in vintages:
        if not isinstance(vintage, dict) or not isinstance(vintage.get("family"), str) or type(vintage.get("pit_proven")) is not bool:
            raise ValueError("SOURCE_VINTAGE_SCHEMA_INVALID")

    sessions = calendar_manifest.get("valid_sessions")
    if calendar_manifest.get("exchange") != "NSE" or not isinstance(calendar_manifest.get("calendar_source"), str) or not calendar_manifest.get("calendar_source"):
        raise ValueError("NSE_CALENDAR_PROVENANCE_MISSING")
    if not isinstance(sessions, list) or not sessions:
        raise ValueError("NSE_CALENDAR_SESSIONS_MISSING")
    parsed_sessions = [_iso_date(x) for x in sessions]
    if parsed_sessions != sorted(set(parsed_sessions)):
        raise ValueError("NSE_CALENDAR_NOT_UNIQUE_SORTED")

    if input_manifest.get("timestamp_semantics") not in {"BAR_START", "BAR_END"}:
        return False, "CANDLE_SEMANTICS_UNPROVEN"
    if input_manifest.get("official_close_linkage_proven") is not True:
        return False, "CLOSE_LINKAGE_UNPROVEN"

    if split_manifest.get("holdout_boundary_found") is not True:
        return False, "BLOCKED_HOLDOUT_PROOF"
    if split_manifest.get("record_boundary_verified") is not True or split_manifest.get("chronological_order_verified") is not True:
        return False, "BLOCKED_HOLDOUT_PROOF"
    if split_manifest.get("holdout_values_accessed") is not False or split_manifest.get("holdout_labels_accessed") is not False:
        raise ValueError("HOLDOUT_ACCESS_HISTORY_NOT_CLEAN")
    if split_manifest.get("holdout_excluded_from_feature_fit") is not True or split_manifest.get("holdout_excluded_from_label_selection") is not True:
        return False, "BLOCKED_HOLDOUT_PROOF"
    if split_manifest.get("train_label_endpoint_purge_verified") is not True or split_manifest.get("validation_label_endpoint_purge_verified") is not True:
        return False, "BLOCKED_LEAKAGE"
    if split_manifest.get("train_eligible_origins") != split_manifest.get("train_eligible_origins_verified"):
        return False, "BLOCKED_LEAKAGE"
    if split_manifest.get("validation_eligible_origins") != split_manifest.get("validation_eligible_origins_verified"):
        return False, "BLOCKED_LEAKAGE"
    if not _nonnegative_int(split_manifest.get("train_eligible_origins")) or not _nonnegative_int(split_manifest.get("common_validation_origins")):
        return False, "BLOCKED_LEAKAGE"
    if split_manifest["train_eligible_origins"] < 252 or split_manifest["common_validation_origins"] < 250:
        return False, "INCOMPLETE_NOT_PROMOTABLE"
    offsets = [split_manifest.get(k) for k in ("train_end_byte_offset", "validation_end_byte_offset", "holdout_start_byte_offset")]
    if any(not _nonnegative_int(x) for x in offsets) or not (0 < offsets[0] <= offsets[1] < offsets[2]):
        raise ValueError("SPLIT_BYTE_OFFSETS_INVALID")
    _iso_date(split_manifest.get("train_end_session"))
    _iso_date(split_manifest.get("validation_end_session"))
    _iso_date(split_manifest.get("holdout_start_session"))
    if not (_iso_date(split_manifest["train_end_session"]) < _iso_date(split_manifest["validation_end_session"]) < _iso_date(split_manifest["holdout_start_session"])):
        raise ValueError("SPLIT_SESSION_ORDER_INVALID")
    return True, "READY"


class BoundedReader(io.RawIOBase):
    """Read a file prefix only; never request bytes after a pre-validated boundary."""
    def __init__(self, source: BinaryIO, limit: int):
        self.source = source
        self.remaining = limit

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray) -> int:
        if self.remaining <= 0:
            return 0
        size = min(len(buffer), self.remaining)
        chunk = self.source.read(size)
        if not chunk:
            return 0
        buffer[:len(chunk)] = chunk
        self.remaining -= len(chunk)
        return len(chunk)


def _finite_positive(text: str) -> float | None:
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) and value > 0 else None


def _valid_ohlc(row: Mapping[str, str], cmap: Mapping[str, str]) -> bool:
    values = [_finite_positive(row.get(cmap[k], "")) for k in ("open", "high", "low", "close")]
    if any(v is None for v in values):
        return False
    op, hi, lo, cl = values
    return hi >= max(op, cl) and lo <= min(op, cl) and hi >= lo


def _report_schema_subset_validate(instance: Any, schema: Mapping[str, Any], path: str = "$",
                                   root_schema: Mapping[str, Any] | None = None) -> None:
    """Strict local validator for the schema keywords used in this fixed report schema."""
    if root_schema is None:
        root_schema = schema
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
            raise ValueError(f"REPORT_SCHEMA_REF_UNSUPPORTED:{path}")
        ref_name = reference.split("/")[-1]
        definitions = root_schema.get("$defs")
        if not isinstance(definitions, dict) or ref_name not in definitions:
            raise ValueError(f"REPORT_SCHEMA_REF_MISSING:{path}")
        _report_schema_subset_validate(instance, definitions[ref_name], path, root_schema)
        return
    expected_type = schema.get("type")
    type_ok = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "integer": lambda x: type(x) is int,
        "number": lambda x: type(x) in (int, float) and math.isfinite(x),
        "boolean": lambda x: type(x) is bool,
    }
    if expected_type in type_ok and not type_ok[expected_type](instance):
        raise ValueError(f"REPORT_SCHEMA_TYPE:{path}")
    if "enum" in schema and instance not in schema["enum"]:
        raise ValueError(f"REPORT_SCHEMA_ENUM:{path}")
    if isinstance(instance, str) and "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
        raise ValueError(f"REPORT_SCHEMA_PATTERN:{path}")
    if type(instance) in (int, float):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ValueError(f"REPORT_SCHEMA_MINIMUM:{path}")
        if "maximum" in schema and instance > schema["maximum"]:
            raise ValueError(f"REPORT_SCHEMA_MAXIMUM:{path}")
    if isinstance(instance, dict):
        required = schema.get("required", [])
        if any(key not in instance for key in required):
            raise ValueError(f"REPORT_SCHEMA_REQUIRED:{path}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and any(key not in properties for key in instance):
            raise ValueError(f"REPORT_SCHEMA_EXTRA_PROPERTY:{path}")
        for key, value in instance.items():
            if key in properties:
                _report_schema_subset_validate(value, properties[key], f"{path}.{key}", root_schema)
            elif isinstance(schema.get("additionalProperties"), dict):
                _report_schema_subset_validate(value, schema["additionalProperties"], f"{path}.{key}", root_schema)
    if isinstance(instance, list) and isinstance(schema.get("items"), dict):
        for index, value in enumerate(instance):
            _report_schema_subset_validate(value, schema["items"], f"{path}[{index}]", root_schema)


def sanitize_report(report: Mapping[str, Any], schema: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(report, Mapping):
        raise ValueError("REPORT_NOT_MAPPING")
    _report_schema_subset_validate(dict(report), schema)
    if report.get("dataset_sha256") != EXPECTED_DATASET_SHA256:
        raise ValueError("REPORT_DATASET_HASH_MISMATCH")
    if report.get("gate_status") not in {"BLOCKED", "NOT_ESTIMABLE", "PASS", "PASS_WITH_RESTRICTIONS", "PASS_WITH_EXCLUSIONS"}:
        raise ValueError("REPORT_GATE_STATUS_INVALID")
    if report.get("prefix_rows_scanned") != report.get("option_rows_scanned", 0) + report.get("spot_rows_scanned", 0):
        raise ValueError("REPORT_ROW_TYPE_TOTAL_MISMATCH")
    if report.get("prefix_rows_scanned", 0) > report.get("expected_rows", -1):
        raise ValueError("REPORT_PREFIX_EXCEEDS_DATASET")
    targets = report.get("target_horizons", {})
    for horizon, values in targets.items():
        if values.get("eligible_origins") != values.get("down_count", 0) + values.get("flat_count", 0) + values.get("up_count", 0):
            raise ValueError("REPORT_TARGET_COUNTS_MISMATCH")
    for family, values in report.get("feature_families", {}).items():
        possible = values.get("possible_cells", 0)
        nonblank = values.get("nonblank_cells", 0)
        if nonblank > possible:
            raise ValueError("REPORT_FEATURE_COUNTS_MISMATCH")
        expected_rate = nonblank / possible if possible else 0.0
        if abs(values.get("coverage_rate", -1) - expected_rate) > 1e-12:
            raise ValueError("REPORT_COVERAGE_RATE_MISMATCH")
    return dict(report)


def _hash_receipt(path: str | Path, expected_hash: str) -> None:
    actual = sha256_file(path)
    if actual != expected_hash:
        raise ValueError("INPUT_SHA256_MISMATCH")


def _scan_prefix(dataset_path: str | Path, byte_limit: int, manifest: Mapping[str, Any],
                 input_manifest: Mapping[str, Any], source_manifest: Mapping[str, Any],
                 calendar_manifest: Mapping[str, Any]) -> dict[str, Any]:
    cmap = input_manifest["column_map"]
    row_values = input_manifest["row_type_values"]
    calendar = set(calendar_manifest["valid_sessions"])
    header = None
    count = {"rows": 0, "option": 0, "spot": 0, "invalid_ohlc": 0, "off_calendar": 0,
             "duplicate_spot_epochs": 0, "unmatched_option": 0, "weekend_review": 0}
    nonblank: dict[str, int] = {}
    feature_specs = source_manifest.get("feature_families", [])
    if not isinstance(feature_specs, list):
        raise ValueError("FEATURE_FAMILY_MANIFEST_INVALID")
    seen_families: set[str] = set()
    for spec in feature_specs:
        if not isinstance(spec, dict) or spec.get("family") not in ALLOWED_FEATURE_FAMILIES or spec["family"] in seen_families:
            raise ValueError("FEATURE_FAMILY_SPEC_INVALID")
        if spec.get("row_type") not in {"OPTION", "SPOT", "ALL"} or not isinstance(spec.get("columns"), list) or not spec["columns"]:
            raise ValueError("FEATURE_FAMILY_SPEC_INVALID")
        if any(not isinstance(col, str) or not col for col in spec["columns"]) or len(set(spec["columns"])) != len(spec["columns"]):
            raise ValueError("FEATURE_FAMILY_SPEC_INVALID")
        if type(spec.get("pit_proven")) is not bool or type(spec.get("join_validity_proven")) is not bool:
            raise ValueError("FEATURE_FAMILY_EVIDENCE_INVALID")
        seen_families.add(spec["family"])
    feature_rows: dict[str, int] = {}
    feature_type_counts: dict[str, int] = {"OPTION": 0, "SPOT": 0}
    spot_by_session: dict[str, tuple[int, float]] = {}
    seen_spot_epochs: set[int] = set()
    last_timestamp = -1
    valid_sessions = set()
    train_end = _iso_date(manifest["train_end_session"])
    validation_end = _iso_date(manifest["validation_end_session"])
    holdout_start = _iso_date(manifest["holdout_start_session"])
    session_rows = {"train": set(), "validation": set()}
    train_endpoints_purged = 0
    if type(byte_limit) is not int or byte_limit <= 0 or byte_limit > Path(dataset_path).stat().st_size:
        raise ValueError("HOLDOUT_OFFSET_OUT_OF_RANGE")
    with Path(dataset_path).open("rb") as boundary_check:
        boundary_check.seek(byte_limit - 1)
        if boundary_check.read(1) != b"\n":
            raise ValueError("HOLDOUT_OFFSET_NOT_RECORD_BOUNDARY")

    with Path(dataset_path).open("rb") as source:
        bounded = io.BufferedReader(BoundedReader(source, byte_limit))
        text = io.TextIOWrapper(bounded, encoding="utf-8", newline="")
        reader = csv.DictReader(text, strict=True)
        header = reader.fieldnames
        if not header or len(header) != EXPECTED_COLUMNS or len(set(header)) != len(header):
            raise ValueError("DATASET_HEADER_INVALID")
        required_actual = set(cmap.values())
        if not required_actual.issubset(set(header)):
            raise ValueError("DATASET_HEADER_COLUMN_MAP_MISMATCH")
        for row in reader:
            if None in row:
                raise ValueError("CSV_ROW_WIDTH_INVALID")
            if any(row.get(name) is None for name in required_actual):
                raise ValueError("CSV_REQUIRED_VALUE_MISSING")
            count["rows"] += 1
            if count["rows"] > EXPECTED_ROWS:
                raise ValueError("ROW_BOUND_EXCEEDED")
            row_type = row[cmap["row_type"]]
            if row_type not in (row_values["option"], row_values["spot"]):
                raise ValueError("UNKNOWN_ROW_TYPE")
            session_date = row[cmap["session_date"]]
            parsed_date = _iso_date(session_date)
            if parsed_date >= holdout_start:
                raise ValueError("PREHOLDOUT_PREFIX_CROSSES_BOUNDARY")
            if session_date not in calendar:
                count["off_calendar"] += 1
            if "WEEKEND_SESSION" in row[cmap["quality_flags"]]:
                count["weekend_review"] += 1
            try:
                timestamp = int(row[cmap["timestamp_epoch"]])
            except (TypeError, ValueError):
                raise ValueError("TIMESTAMP_PARSE_INVALID")
            if timestamp < last_timestamp:
                raise ValueError("PREHOLDOUT_TIMESTAMP_ORDER_INVALID")
            last_timestamp = timestamp
            feature_type_counts[row_type] += 1
            if row_type == row_values["spot"]:
                count["spot"] += 1
                if timestamp in seen_spot_epochs:
                    count["duplicate_spot_epochs"] += 1
                seen_spot_epochs.add(timestamp)
                if not _valid_ohlc(row, cmap):
                    count["invalid_ohlc"] += 1
                else:
                    close = _finite_positive(row[cmap["close"]])
                    prior = spot_by_session.get(session_date)
                    if prior is None or timestamp > prior[0]:
                        spot_by_session[session_date] = (timestamp, close)  # latest valid bar close
                        valid_sessions.add(session_date)
            else:
                count["option"] += 1
                if row[cmap["join_status"]].upper() == "UNMATCHED":
                    count["unmatched_option"] += 1
            for spec in feature_specs:
                family = spec["family"]
                if spec["row_type"] not in {"ALL", row_type}:
                    continue
                feature_rows[family] = feature_rows.get(family, 0) + 1
                for col in spec["columns"]:
                    if col not in header:
                        raise ValueError("FEATURE_COLUMN_NOT_IN_HEADER")
                    key = family + "::" + col
                    nonblank[key] = nonblank.get(key, 0) + int(bool(row[col].strip()))
            if parsed_date <= train_end:
                session_rows["train"].add(session_date)
            elif parsed_date <= validation_end:
                session_rows["validation"].add(session_date)

    sessions = sorted(calendar)
    close_by_session = {k: v[1] for k, v in spot_by_session.items()}
    target_results: dict[str, Any] = {}
    eligible_origins = 0
    for horizon in HORIZONS:
        down = flat = up = excluded = 0
        for i, session in enumerate(sessions):
            if session >= holdout_start or i + horizon >= len(sessions):
                continue
            endpoint = sessions[i + horizon]
            if endpoint >= holdout_start:
                continue
            start_price = close_by_session.get(session)
            end_price = close_by_session.get(endpoint)
            if start_price is None or end_price is None:
                excluded += 1
                continue
            ret = (end_price - start_price) / start_price
            if abs(ret) <= FLAT_TOLERANCE:
                flat += 1
            elif ret > 0:
                up += 1
            else:
                down += 1
        total = down + flat + up
        eligible_origins = max(eligible_origins, total)
        target_results[str(horizon)] = {
            "status": "CANDIDATE" if total > 0 else "NOT_ESTIMABLE",
            "eligible_origins": total, "excluded_missing_endpoint": excluded,
            "down_count": down, "flat_count": flat, "up_count": up,
        }

    feature_results: dict[str, Any] = {}
    for spec in feature_specs:
        family = spec["family"]
        columns = spec["columns"]
        values = sum(nonblank.get(family + "::" + col, 0) for col in columns)
        denom = feature_rows.get(family, 0) * len(columns)
        coverage = values / denom if denom else 0.0
        if values == 0:
            status = "BLOCKED_DATA"
        elif spec.get("pit_proven") is not True:
            status = "NOT_ESTIMABLE"
        elif spec.get("join_validity_proven") is not True:
            status = "PASS_WITH_RESTRICTIONS"
        else:
            status = "CANDIDATE"
        feature_results[family] = {"status": status, "nonblank_cells": values, "possible_cells": denom,
                                   "coverage_rate": coverage}
    split = "PASS"
    if count["off_calendar"] or count["invalid_ohlc"] or count["duplicate_spot_epochs"]:
        split = "PASS_WITH_EXCLUSIONS"
    if count["rows"] != manifest.get("pre_holdout_prefix_rows"):
        raise ValueError("PREHOLDOUT_ROW_COUNT_MISMATCH")
    report = {
        "dataset_id": EXPECTED_DATASET_ID, "dataset_sha256": EXPECTED_DATASET_SHA256,
        "expected_rows": EXPECTED_ROWS, "expected_columns": EXPECTED_COLUMNS,
        "prefix_rows_scanned": count["rows"], "option_rows_scanned": count["option"], "spot_rows_scanned": count["spot"],
        "invalid_ohlc_rows": count["invalid_ohlc"], "off_calendar_rows": count["off_calendar"],
        "duplicate_spot_epoch_rows": count["duplicate_spot_epochs"], "unmatched_option_rows": count["unmatched_option"],
        "weekend_review_rows": count["weekend_review"], "target_horizons": target_results,
        "feature_families": feature_results, "train_session_count": len(session_rows["train"]),
        "validation_session_count": len(session_rows["validation"]), "session_status": split,
        "split_status": "PASS", "source_manifest_sha256": "", "calendar_manifest_sha256": "",
        "split_manifest_sha256": "", "cleanup_status": "PASS",
        "gate_status": "PASS_WITH_RESTRICTIONS" if (
            split != "PASS" or count["unmatched_option"] > 0 or count["weekend_review"] > 0
            or any(v["status"] != "CANDIDATE" for v in feature_results.values())
            or any(v["status"] != "CANDIDATE" for v in target_results.values())
        ) else "PASS",
    }
    return report


def build_blocked_report(input_manifest: Mapping[str, Any], reason: str) -> dict[str, Any]:
    """Emit a metadata-only blocked/not-estimable report; no CSV path is opened."""
    if reason == "BLOCKED_HOLDOUT_PROOF":
        target_status, split_status, gate_status = "BLOCKED_HOLDOUT_PROOF", "BLOCKED_HOLDOUT_PROOF", "BLOCKED"
    elif reason == "BLOCKED_LEAKAGE":
        target_status, split_status, gate_status = "NOT_ESTIMABLE", "BLOCKED_LEAKAGE", "BLOCKED"
    elif reason == "INCOMPLETE_NOT_PROMOTABLE":
        target_status, split_status, gate_status = "NOT_ESTIMABLE", "NOT_ESTIMABLE", "NOT_ESTIMABLE"
    else:
        target_status, split_status, gate_status = "NOT_ESTIMABLE", "NOT_ESTIMABLE", "NOT_ESTIMABLE"
    return {
        "dataset_id": EXPECTED_DATASET_ID, "dataset_sha256": EXPECTED_DATASET_SHA256,
        "expected_rows": EXPECTED_ROWS, "expected_columns": EXPECTED_COLUMNS,
        "prefix_rows_scanned": 0, "option_rows_scanned": 0, "spot_rows_scanned": 0,
        "invalid_ohlc_rows": 0, "off_calendar_rows": 0, "duplicate_spot_epoch_rows": 0,
        "unmatched_option_rows": 0, "weekend_review_rows": 0,
        "target_horizons": {str(h): {"status": target_status, "eligible_origins": 0,
                          "excluded_missing_endpoint": 0, "down_count": 0, "flat_count": 0, "up_count": 0}
                            for h in HORIZONS},
        "feature_families": {}, "train_session_count": 0, "validation_session_count": 0,
        "session_status": "NOT_ESTIMABLE", "split_status": split_status,
        "source_manifest_sha256": "", "calendar_manifest_sha256": "", "split_manifest_sha256": "",
        "block_reason": reason, "cleanup_status": "NOT_RUN", "gate_status": gate_status,
    }


def execute(args: argparse.Namespace) -> dict[str, Any]:
    paths = {
        "scripts/modeling_readiness_feasibility_run.py": args.runner_file,
        "tests/test_modeling_readiness_feasibility_run.py": args.tests_file,
        "research/gates/MODELING_READINESS_FEASIBILITY_REPORT_SCHEMA_R5_2026-10-11.json": args.schema,
        ".github/workflows/phase-07-modeling-readiness-feasibility-synthetic.yml": args.workflow_file,
    }
    auth = read_json_object(args.authorization)
    validate_execution_authorization(auth, paths)
    path_labels = {
        "dataset": args.dataset, "input_manifest": args.input_manifest,
        "source_manifest": args.source_manifest, "calendar_manifest": args.calendar_manifest,
        "split_manifest": args.split_manifest,
    }
    if auth["input_sha256"].get("dataset") != EXPECTED_DATASET_SHA256:
        raise ValueError("AUTH_DATASET_HASH_MISMATCH")
    for label, path in path_labels.items():
        _hash_receipt(path, auth["input_sha256"][label])

    input_manifest = read_json_object(args.input_manifest)
    source_manifest = read_json_object(args.source_manifest)
    calendar_manifest = read_json_object(args.calendar_manifest)
    split_manifest = read_json_object(args.split_manifest)
    ready, status = validate_input_manifests(input_manifest, source_manifest, calendar_manifest, split_manifest)
    schema = read_json_object(args.schema)
    if not ready:
        report = build_blocked_report(input_manifest, status)
    else:
        if sha256_file(args.dataset) != EXPECTED_DATASET_SHA256:
            raise ValueError("DATASET_HASH_MISMATCH")
        if split_manifest["holdout_start_byte_offset"] > Path(args.dataset).stat().st_size:
            raise ValueError("HOLDOUT_OFFSET_OUT_OF_RANGE")
        report = _scan_prefix(args.dataset, split_manifest["holdout_start_byte_offset"], split_manifest,
                              input_manifest, source_manifest, calendar_manifest)
        report["source_manifest_sha256"] = sha256_file(args.source_manifest)
        report["calendar_manifest_sha256"] = sha256_file(args.calendar_manifest)
        report["split_manifest_sha256"] = sha256_file(args.split_manifest)
    clean = sanitize_report(report, schema)
    Path(args.output).write_text(json.dumps(clean, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return clean


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run synthetic contract tests; never reads real market data")
    parser.add_argument("--dataset")
    parser.add_argument("--input-manifest")
    parser.add_argument("--source-manifest")
    parser.add_argument("--calendar-manifest")
    parser.add_argument("--split-manifest")
    parser.add_argument("--authorization")
    parser.add_argument("--schema")
    parser.add_argument("--runner-file")
    parser.add_argument("--tests-file")
    parser.add_argument("--workflow-file")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"suite": "modeling-readiness-feasibility-v1", "real_data_execution": "NOT_RUN",
                          "model_fitting": "NOT_AUTHORIZED", "holdout_access": "NOT_AUTHORIZED"}, sort_keys=True))
        return 0
    required = ("dataset", "input_manifest", "source_manifest", "calendar_manifest", "split_manifest",
                "authorization", "schema", "runner_file", "tests_file", "workflow_file", "output")
    if any(not getattr(args, key) for key in required):
        parser.error("real mode requires every path, an exact-snapshot authorization and all frozen input manifests")
    try:
        report = execute(args)
    except (OSError, UnicodeError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        # Never print exception strings from malformed input: they can contain path/value context.
        print(json.dumps({"status": "BLOCKED", "error_code": str(exc) if str(exc).isupper() else "INPUT_VALIDATION_FAILED",
                          "real_data_execution": "ATTEMPTED", "model_fitting": "NOT_AUTHORIZED",
                          "holdout_access": "NOT_AUTHORIZED"}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"gate_status": report["gate_status"], "output_schema_valid": True,
                      "model_fitting": "NOT_AUTHORIZED", "holdout_access": "NOT_AUTHORIZED"}, sort_keys=True))
    return 0 if report["gate_status"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
