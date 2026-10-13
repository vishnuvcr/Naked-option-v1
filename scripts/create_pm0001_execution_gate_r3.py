#!/usr/bin/env python3
"""Create an ephemeral PM0001 execution gate after current data preflight.

The gate authorizes only the 40 registered PM0001 configurations for the exact
verified dataset, preflight report, implementation gate, eligibility manifest,
and runner source hashes. It never loads market observations or fits a model.
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


def build_execution_gate(
    eligibility: dict[str, Any],
    preflight: dict[str, Any],
    implementation_gate: dict[str, Any],
    *,
    eligibility_blob_sha1: str,
    preflight_blob_sha1: str,
    implementation_gate_blob_sha1: str,
    prereg_blob_sha1: str,
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

    if implementation_gate.get("status") != "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY":
        raise ValueError("PM0001_IMPLEMENTATION_GATE_STATUS_INVALID")
    return {
        "schema_version": "pm0001-execution-gate-r3-v1",
        "status": "PASS_PM0001_EXECUTION_PRECHECK",
        "method_id": "PM0001",
        "configuration_count": 40,
        "config_ids": config_ids,
        "empirical_fit_authorized": True,
        "manual_authorization_required": False,
        "scope": "PM0001 registered configurations only; no holdout; exact pinned dataset and source",
        "source_data_sha256": EXPECTED_DATA_SHA256,
        "eligibility_manifest_git_blob_sha1": eligibility_blob_sha1,
        "preflight_report_git_blob_sha1": preflight_blob_sha1,
        "implementation_gate_git_blob_sha1": implementation_gate_blob_sha1,
        "preregistration_git_blob_sha1": prereg_blob_sha1,
        "runner_git_blob_sha1": runner_blob_sha1,
        "source_commit": source_commit,
        "workflow_run_id": workflow_run_id,
        "holdout_accessed": False,
        "market_data_loaded_by_precheck": False,
        "model_fitting_performed_by_precheck": False,
        "preflight_status": preflight["status"],
        "eligible_fold_label_cells": 75,
        "blocked_fold_label_cells": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--eligibility", default=str(ROOT / ELIGIBILITY_PATH))
    parser.add_argument("--implementation-gate", default=str(ROOT / IMPLEMENTATION_GATE_PATH))
    parser.add_argument("--preregistration", default=str(ROOT / PREREG_PATH))
    parser.add_argument("--runner", default=str(ROOT / "scripts/run_pm0001_prediction_sweep_r3.py"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", default="unknown")
    parser.add_argument("--workflow-run-id", default="unknown")
    args = parser.parse_args()

    preflight_path = Path(args.preflight)
    eligibility_path = Path(args.eligibility)
    implementation_path = Path(args.implementation_gate)
    prereg_path = Path(args.preregistration)
    runner_path = Path(args.runner)
    eligibility = read_json(eligibility_path)
    preflight = read_json(preflight_path)
    implementation_gate = read_json(implementation_path)
    prereg = read_json(prereg_path)
    verify_implementation_gate(implementation_gate)
    if prereg.get("date") != "2026-10-13" or len(prereg.get("labels", {})) != 10:
        raise ValueError("FROZEN_PREREGISTRATION_INVALID")
    if not runner_path.is_file():
        raise ValueError("PM0001_RUNNER_MISSING")
    gate = build_execution_gate(
        eligibility, preflight, implementation_gate,
        eligibility_blob_sha1=git_blob_sha1(eligibility_path.read_bytes()),
        preflight_blob_sha1=git_blob_sha1(preflight_path.read_bytes()),
        implementation_gate_blob_sha1=git_blob_sha1(implementation_path.read_bytes()),
        prereg_blob_sha1=git_blob_sha1(prereg_path.read_bytes()),
        runner_blob_sha1=git_blob_sha1(runner_path.read_bytes()),
        source_commit=args.source_commit,
        workflow_run_id=args.workflow_run_id,
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(gate, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": gate["status"], "method_id": gate["method_id"],
        "configuration_count": gate["configuration_count"],
        "empirical_fit_authorized": gate["empirical_fit_authorized"],
        "manual_authorization_required": gate["manual_authorization_required"],
        "holdout_accessed": gate["holdout_accessed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
