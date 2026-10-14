#!/usr/bin/env python3
"""Create a run-scoped PM0001 execution gate from exact pinned source and data precheck.

The gate authorizes only the 40 registered PM0001 configurations for this exact CI
snapshot and the complete 320-row configuration/fold precheck. It never fits models.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DATA_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
IMPLEMENTATION_GATE_PATH = "research/gates/PREDICTION_PM0001_IMPLEMENTATION_GATE_R3_2026-10-14.json"
ELIGIBILITY_PATH = "research/gates/PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json"
PREREG_PATH = "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
FOLD_IDS = tuple(f"F{i:02d}" for i in range(1, 9))
PRECHECK_TERMINAL = {"PRECHECK_PASS", "BLOCKED_DATA", "BLOCKED_SAMPLE_ELIGIBILITY"}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_TOP_LEVEL_NOT_OBJECT:{path}")
    return value


def verify_implementation_gate(gate: dict[str, Any], repo_root: Path = ROOT) -> None:
    if gate.get("method_id") != "PM0001" or gate.get("status") != "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY":
        raise ValueError("PM0001_IMPLEMENTATION_GATE_NOT_PASSED")
    v = gate.get("verification", {})
    if v.get("conclusion") != "success" or v.get("source_data_loaded") is not False:
        raise ValueError("PM0001_IMPLEMENTATION_CI_OR_SCOPE_INVALID")
    if v.get("empirical_model_fit") is not False or v.get("holdout_accessed") is not False:
        raise ValueError("PM0001_IMPLEMENTATION_GATE_SCOPE_INVALID")
    if gate.get("empirical_fit_authorized") is not False or gate.get("manual_authorization_required") is not False:
        raise ValueError("PM0001_IMPLEMENTATION_AUTHORIZATION_FLAGS_INVALID")
    pins = gate.get("source_blob_pins")
    if not isinstance(pins, dict) or not pins:
        raise ValueError("PM0001_IMPLEMENTATION_SOURCE_PINS_MISSING")
    for rel, expected in pins.items():
        path = repo_root / rel
        if not path.is_file() or git_blob_sha1(path.read_bytes()) != expected:
            raise ValueError(f"PM0001_IMPLEMENTATION_SOURCE_PIN_MISMATCH:{rel}")


def validate_precheck(precheck: dict[str, Any], config_ids: list[str]) -> dict[str, int]:
    if precheck.get("schema_version") != "pm0001-data-execution-precheck-r3-v1":
        raise ValueError("PM0001_DATA_PRECHECK_SCHEMA_INVALID")
    if precheck.get("status") != "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING":
        raise ValueError("PM0001_DATA_PRECHECK_NOT_COMPLETE_PASS")
    if precheck.get("source_csv_sha256") != EXPECTED_DATA_SHA256:
        raise ValueError("PM0001_DATA_PRECHECK_DATA_HASH_MISMATCH")
    if precheck.get("configuration_count") != 40 or precheck.get("outer_fold_count") != 8:
        raise ValueError("PM0001_DATA_PRECHECK_DIMENSIONS_INVALID")
    if precheck.get("result_row_count") != 320 or precheck.get("model_fitting_performed") is not False:
        raise ValueError("PM0001_DATA_PRECHECK_COUNT_OR_FIT_SCOPE_INVALID")
    if precheck.get("holdout_accessed") is not False or precheck.get("empirical_fit_authorized") is not False:
        raise ValueError("PM0001_DATA_PRECHECK_PROVENANCE_INVALID")
    rows = precheck.get("rows")
    if not isinstance(rows, list) or len(rows) != 320:
        raise ValueError("PM0001_DATA_PRECHECK_ROWS_MISSING")
    expected = {(cfg, fold) for cfg in config_ids for fold in FOLD_IDS}
    seen: set[tuple[str, str]] = set()
    counts: dict[str, int] = {}
    for pos, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"PM0001_DATA_PRECHECK_ROW_NOT_OBJECT:{pos}")
        key = (str(row.get("config_id", "")), str(row.get("fold_id", "")))
        if key in seen:
            raise ValueError(f"PM0001_DATA_PRECHECK_DUPLICATE_PAIR:{key}")
        seen.add(key)
        if row.get("method_id") != "PM0001":
            raise ValueError(f"PM0001_DATA_PRECHECK_METHOD_MISMATCH:{key}")
        if row.get("status") not in PRECHECK_TERMINAL:
            # FAILED_PRECHECK must not authorize any empirical fit.
            raise ValueError(f"PM0001_DATA_PRECHECK_TERMINAL_STATUS_INVALID:{key}:{row.get('status')}")
        if row.get("empirical_fit_authorized") is not False or row.get("model_fitting_performed") is not False:
            raise ValueError(f"PM0001_DATA_PRECHECK_ROW_AUTHORIZATION_INVALID:{key}")
        if row.get("holdout_accessed") is not False:
            raise ValueError(f"PM0001_DATA_PRECHECK_ROW_HOLDOUT_SCOPE_INVALID:{key}")
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    if seen != expected:
        raise ValueError(f"PM0001_DATA_PRECHECK_COVERAGE_MISMATCH:missing={len(expected-seen)}:extra={len(seen-expected)}")
    return counts


def build_execution_gate(
    eligibility: dict[str, Any],
    preflight: dict[str, Any],
    implementation_gate: dict[str, Any],
    precheck: dict[str, Any],
    *,
    eligibility_blob_sha1: str,
    preflight_blob_sha1: str,
    implementation_gate_blob_sha1: str,
    prereg_blob_sha1: str,
    precheck_blob_sha1: str,
    precheck_sha256: str,
    runner_blob_sha1: str,
    source_commit: str,
    workflow_run_id: str,
) -> dict[str, Any]:
    if preflight.get("canonical_hash_matches") is not True:
        raise ValueError("DATA_PREFLIGHT_CANONICAL_HASH_NOT_VERIFIED")
    if preflight.get("canonical_uncompressed_csv_sha256") != EXPECTED_DATA_SHA256:
        raise ValueError("DATA_PREFLIGHT_DATASET_HASH_MISMATCH")
    if preflight.get("status") not in {"PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS", "BLOCKED_SAMPLE_ELIGIBILITY"}:
        raise ValueError("DATA_PREFLIGHT_STATUS_NOT_ACCEPTABLE")
    if preflight.get("blockers") != []:
        raise ValueError("DATA_PREFLIGHT_HAS_GLOBAL_BLOCKERS")
    if preflight.get("holdout_accessed") is not False or preflight.get("model_fitting_performed") is not False:
        raise ValueError("DATA_PREFLIGHT_PROVENANCE_FLAGS_UNSAFE")
    if preflight.get("eligible_fold_label_cells") != 75 or preflight.get("blocked_fold_label_cells") != 5:
        raise ValueError("DATA_PREFLIGHT_FOLD_CELL_COUNTS_CHANGED")

    if eligibility.get("record_count") != 40000 or eligibility.get("unique_config_count") != 40000:
        raise ValueError("ELIGIBILITY_REGISTRY_TOTALS_INVALID")
    if eligibility.get("manual_authorization_required") is not False or eligibility.get("empirical_fit_authorized") is not False:
        raise ValueError("ELIGIBILITY_GATE_FLAGS_INVALID")
    if eligibility.get("implementation_gate_status") != "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY":
        raise ValueError("ELIGIBILITY_IMPLEMENTATION_GATE_STATUS_INVALID")
    source_pins = eligibility.get("source_pins", {})
    if source_pins.get("implementation_gate_git_blob_sha1") != implementation_gate_blob_sha1:
        raise ValueError("ELIGIBILITY_IMPLEMENTATION_GATE_PIN_MISMATCH")
    if source_pins.get("canonical_uncompressed_csv_sha256") != EXPECTED_DATA_SHA256:
        raise ValueError("ELIGIBILITY_DATASET_PIN_MISMATCH")

    records = eligibility.get("records")
    if not isinstance(records, list) or len(records) != 40000:
        raise ValueError("ELIGIBILITY_RECORDS_MISSING")
    pending = [r for r in records if r.get("disposition") == "ELIGIBLE_PENDING_EXECUTOR_GATE"]
    if len(pending) != 40 or any(r.get("method_id") != "PM0001" for r in pending):
        raise ValueError("EXPECTED_EXACTLY_40_PM0001_CONFIGS_PENDING_EXECUTOR_GATE")
    if any(r.get("empirical_fit_authorized") is not False or r.get("manual_authorization_required") is not False for r in pending):
        raise ValueError("PENDING_CONFIG_FLAGS_INVALID")
    config_ids = sorted(r["config_id"] for r in pending)
    if len(set(config_ids)) != 40:
        raise ValueError("PM0001_CONFIG_IDS_NOT_UNIQUE")
    precheck_counts = validate_precheck(precheck, config_ids)
    if implementation_gate.get("status") != "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY":
        raise ValueError("PM0001_IMPLEMENTATION_GATE_STATUS_INVALID")
    return {
        "schema_version": "pm0001-execution-gate-r3-v2",
        "status": "PASS_PM0001_EXECUTION_PRECHECK",
        "method_id": "PM0001",
        "configuration_count": 40,
        "config_ids": config_ids,
        "outer_fold_ids": list(FOLD_IDS),
        "expected_result_rows": 320,
        "precheck_status_counts": precheck_counts,
        "empirical_fit_authorized": True,
        "manual_authorization_required": False,
        "scope": "PM0001 registered configurations only; current complete data precheck and exact pinned source; holdout excluded",
        "source_data_sha256": EXPECTED_DATA_SHA256,
        "eligibility_manifest_git_blob_sha1": eligibility_blob_sha1,
        "preflight_report_git_blob_sha1": preflight_blob_sha1,
        "implementation_gate_git_blob_sha1": implementation_gate_blob_sha1,
        "preregistration_git_blob_sha1": prereg_blob_sha1,
        "precheck_report_git_blob_sha1": precheck_blob_sha1,
        "precheck_report_sha256": precheck_sha256,
        "runner_git_blob_sha1": runner_blob_sha1,
        "source_commit": source_commit,
        "workflow_run_id": workflow_run_id,
        "holdout_accessed": False,
        "market_data_loaded_by_precheck": True,
        "model_fitting_performed_by_precheck": False,
        "preflight_status": preflight["status"],
        "eligible_fold_label_cells": 75,
        "blocked_fold_label_cells": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", required=True, type=Path)
    parser.add_argument("--precheck-report", required=True, type=Path)
    parser.add_argument("--eligibility", default=str(ROOT / ELIGIBILITY_PATH), type=Path)
    parser.add_argument("--implementation-gate", default=str(ROOT / IMPLEMENTATION_GATE_PATH), type=Path)
    parser.add_argument("--preregistration", default=str(ROOT / PREREG_PATH), type=Path)
    parser.add_argument("--runner", default=str(ROOT / "scripts/run_pm0001_prediction_sweep_r3.py"), type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-commit", default="unknown")
    parser.add_argument("--workflow-run-id", default="unknown")
    args = parser.parse_args()

    eligibility = read_json(args.eligibility)
    preflight = read_json(args.preflight)
    implementation_gate = read_json(args.implementation_gate)
    prereg = read_json(args.preregistration)
    precheck = read_json(args.precheck_report)
    verify_implementation_gate(implementation_gate)
    if prereg.get("date") != "2026-10-13" or len(prereg.get("labels", {})) != 10:
        raise ValueError("FROZEN_PREREGISTRATION_INVALID")
    if not args.runner.is_file():
        raise ValueError("PM0001_RUNNER_MISSING")
    raw_precheck = args.precheck_report.read_bytes()
    gate = build_execution_gate(
        eligibility, preflight, implementation_gate, precheck,
        eligibility_blob_sha1=git_blob_sha1(args.eligibility.read_bytes()),
        preflight_blob_sha1=git_blob_sha1(args.preflight.read_bytes()),
        implementation_gate_blob_sha1=git_blob_sha1(args.implementation_gate.read_bytes()),
        prereg_blob_sha1=git_blob_sha1(args.preregistration.read_bytes()),
        precheck_blob_sha1=git_blob_sha1(raw_precheck),
        precheck_sha256=sha256(raw_precheck),
        runner_blob_sha1=git_blob_sha1(args.runner.read_bytes()),
        source_commit=args.source_commit,
        workflow_run_id=args.workflow_run_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(gate, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": gate["status"], "method_id": gate["method_id"],
        "configuration_count": gate["configuration_count"],
        "precheck_status_counts": gate["precheck_status_counts"],
        "empirical_fit_authorized": gate["empirical_fit_authorized"],
        "manual_authorization_required": gate["manual_authorization_required"],
        "holdout_accessed": gate["holdout_accessed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
