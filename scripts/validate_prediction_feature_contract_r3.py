#!/usr/bin/env python3
"""Validate the pre-result Phase 8P R3 spot-only lag-stack supplement.

This gate validates frozen input definitions and synthetic feature mechanics only.
It never decrypts market data, fits a model, ranks a method, or opens the holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research/registry/PREDICTION_FEATURE_CONSTRUCTION_CONTRACT_R3_2026-10-13.json"
LABEL_PATH = ROOT / "research/registry/PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json"
PREREG_PATH = ROOT / "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
CALENDAR_PATH = ROOT / "research/data/NSE_CAPITAL_MARKET_SESSION_CALENDAR_R3_2026-10-13.json"
PREFLIGHT_PATH = ROOT / "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
PREREQUISITE_AUDIT_PATH = ROOT / "research/gates/PREDICTION_R3_PREREQUISITE_AUDIT_2026-10-13.json"
METHOD_SHARD_PATH = ROOT / "research/registry/compatibility_shards/PREDICTION_COMPATIBILITY_PART001.json"
REPORT_PATH = ROOT / "research/gates/PREDICTION_FEATURE_CONSTRUCTION_TEST_REPORT_R3_2026-10-13.json"

INTRADAY_MINUTES = {
    "INTRA_5M_UP_DOWN": 5,
    "INTRA_15M_UP_DOWN": 15,
    "INTRA_30M_UP_DOWN": 30,
    "INTRA_60M_UP_DOWN": 60,
    "INTRA_120M_UP_DOWN": 120,
}
POSITIONAL_SESSIONS = {
    "POS_1D_UP_DOWN": 1,
    "POS_2D_UP_DOWN": 2,
    "POS_3D_UP_DOWN": 3,
    "POS_5D_UP_DOWN": 5,
    "POS_10D_UP_DOWN": 10,
}
EXPECTED_BLOCKS = {
    ("POS_1D_UP_DOWN", "F01"),
    ("POS_2D_UP_DOWN", "F01"),
    ("POS_3D_UP_DOWN", "F01"),
    ("POS_5D_UP_DOWN", "F01"),
    ("POS_10D_UP_DOWN", "F01"),
}
EXPECTED_SOURCE_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
EXPECTED_CALENDAR_SHA256 = "ddce75f70f39e390e3d68fc6662ed31b3b85b9ecbc78d71178eedb7a34b9ae26"
EXPECTED_CALENDAR_ID = "NSE_CAPITAL_MARKET_EQUITIES_2021_2026_R3"


class ContractValidationError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    if not path.is_file():
        raise ContractValidationError(f"REQUIRED_FILE_MISSING:{path.relative_to(ROOT)}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"INVALID_JSON:{path.relative_to(ROOT)}") from exc
    if not isinstance(value, dict):
        raise ContractValidationError(f"JSON_TOP_LEVEL_NOT_OBJECT:{path.relative_to(ROOT)}")
    return value, raw


def validate_contract_objects(
    contract: dict[str, Any],
    label_manifest: dict[str, Any],
    preflight: dict[str, Any],
    prerequisite_audit: dict[str, Any],
    method_record: dict[str, Any],
    *,
    calendar_id: str,
    calendar_sha256: str,
    source_csv_sha256: str,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise ContractValidationError(f"{name}:{detail}")

    check("CONTRACT_STATUS", contract.get("status") == "FROZEN_PRE_RESULTS_IMPLEMENTATION_SUPPLEMENT", str(contract.get("status")))
    check("CONTRACT_ID", contract.get("amendment_id") == "PHASE8P_FEATURE_CONSTRUCTION_SUPPLEMENT_R3_2026-10-13", str(contract.get("amendment_id")))
    scope = contract.get("scope", {})
    check("CANONICAL_SOURCE_HASH", scope.get("canonical_csv_sha256") == EXPECTED_SOURCE_SHA256 == source_csv_sha256, str(source_csv_sha256))
    check("CALENDAR_PIN", calendar_id == EXPECTED_CALENDAR_ID and calendar_sha256 == EXPECTED_CALENDAR_SHA256, f"{calendar_id}:{calendar_sha256}")
    check("FEATURE_PRICE_SOURCE", scope.get("permitted_row_type") == "SPOT" and scope.get("price_field") == "nifty_close", f"{scope.get('permitted_row_type')}:{scope.get('price_field')}")
    check("FROZEN_LOOKBACKS", scope.get("lookback_bars") == [20, 60], str(scope.get("lookback_bars")))
    check("FEATURE_DIMENSION", scope.get("feature_dimension_rule") == "2 * lookback_bars", str(scope.get("feature_dimension_rule")))
    check("FEATURE_ORDER", scope.get("feature_order") == ["simple_returns_newest_to_oldest", "spot_close_levels_newest_to_oldest"], str(scope.get("feature_order")))
    check("TRAINING_ONLY_SCALING", scope.get("transformations") == "Only training-fold StandardScaler; fit its means and scales using training rows in the current fold. No global scaling, imputation from future rows, PCA, feature selection, or feature engineering fit on the full sample.", "transformations are frozen")
    check("OPTION_FEATURES_DEFERRED", contract.get("point_in_time_and_quarantine", {}).get("option_rows_are_features") == "Not in this initial PM0001 spot-only representation. Option-derived or global/contextual features require a separate pre-result feature contract with PIT publication/availability verification.", "spot-only PM0001; no proxy substitution")
    check("HOLDOUT_CLOSED", contract.get("point_in_time_and_quarantine", {}).get("holdout") == "No holdout data path or secret may be read.", "holdout stays sealed")

    labels = label_manifest.get("labels")
    if not isinstance(labels, list):
        raise ContractValidationError("LABEL_MANIFEST_LABELS_MISSING")
    by_id = {r.get("id"): r for r in labels if isinstance(r, dict)}
    check("TEN_LABELS", len(by_id) == 10 and set(by_id) == set(INTRADAY_MINUTES) | set(POSITIONAL_SESSIONS), f"n={len(by_id)}")
    check("FLAT_TOLERANCE", label_manifest.get("common_rules", {}).get("flat_tolerance_abs_simple_return") == 1e-8, str(label_manifest.get("common_rules", {}).get("flat_tolerance_abs_simple_return")))
    for label_id, horizon in INTRADAY_MINUTES.items():
        row = by_id.get(label_id, {})
        check(f"{label_id}_HORIZON", row.get("horizon_minutes") == horizon, f"registered={row.get('horizon_minutes')}, contract={horizon}")
        check(f"{label_id}_PURGE_EMBARGO", row.get("purge_exchange_sessions") == 1 and row.get("embargo_exchange_sessions") == 1, f"purge={row.get('purge_exchange_sessions')}, embargo={row.get('embargo_exchange_sessions')}")
    for label_id, horizon in POSITIONAL_SESSIONS.items():
        row = by_id.get(label_id, {})
        check(f"{label_id}_HORIZON", row.get("horizon_exchange_sessions") == horizon, f"registered={row.get('horizon_exchange_sessions')}, contract={horizon}")
        check(f"{label_id}_PURGE_EMBARGO", row.get("purge_exchange_sessions") == horizon and row.get("embargo_exchange_sessions") == horizon, f"purge={row.get('purge_exchange_sessions')}, embargo={row.get('embargo_exchange_sessions')}")
    check("ALL_TARGETS_USE_RETURN_FORMULA", all(by_id[k].get("return_formula") == "(target_spot_price / decision_spot_price) - 1" for k in INTRADAY_MINUTES) and all(by_id[k].get("return_formula") == "(target_spot_close_after_h_sessions / decision_session_close) - 1" for k in POSITIONAL_SESSIONS), "return formulas agree with the frozen label manifest")
    check("SOURCE_PREFLIGHT_PASSED", preflight.get("status") == "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS", str(preflight.get("status")))
    check("SOURCE_PREFLIGHT_HASH", preflight.get("canonical_uncompressed_csv_sha256") == EXPECTED_SOURCE_SHA256 and preflight.get("expected_canonical_csv_sha256") == EXPECTED_SOURCE_SHA256, str(preflight.get("canonical_uncompressed_csv_sha256")))
    check("SPOT_PRICE_COLUMN_PRESENT", "nifty_close" in preflight.get("column_names", []), "nifty_close is present in the 47-column schema")
    check("PREFLIGHT_CELL_COUNTS", len(preflight.get("label_sample_support", [])) == 80, f"cells={len(preflight.get('label_sample_support', []))}")
    blocked = {
        (r.get("label_id"), r.get("fold_id"))
        for r in preflight.get("label_sample_support", [])
        if r.get("passes_frozen_data_minima") is False
    }
    check("SCOPED_F01_BLOCKS", blocked == EXPECTED_BLOCKS, str(sorted(blocked)))
    check("PREFLIGHT_COUNTS", sum(r.get("passes_frozen_data_minima") is True for r in preflight.get("label_sample_support", [])) == 75, "75 pass / 5 blocked")
    check("PREREQUISITE_AUDIT_PASSED", prerequisite_audit.get("status") == "PASS_DATA_AND_REGISTRY_PREREQUISITES_WITH_SCOPED_BLOCKS", str(prerequisite_audit.get("status")))
    gate = prerequisite_audit.get("execution_gate", {})
    check("NO_FIT_AUTHORIZATION", gate.get("empirical_fit_authorized") is False and gate.get("holdout_accessed") is False, str(gate))
    check("PM0001_SEMANTICS", method_record.get("method_id") == "PM0001" and method_record.get("algorithm_family") == "logistic_regression" and method_record.get("input_representation") == "raw_lag_stack" and method_record.get("feature_construction") == "ordered_lagged_returns_and_levels" and method_record.get("compatibility_decision") == "ALLOW_IN_PRINCIPLE", str({k: method_record.get(k) for k in ("method_id", "algorithm_family", "input_representation", "feature_construction", "compatibility_decision")}))
    check("PM0001_NOT_YET_AUTHORIZED", method_record.get("eligible_for_empirical_fitting") is False and method_record.get("implementation_status") == "NOT_IMPLEMENTED_OR_TESTER_APPROVED", str({k: method_record.get(k) for k in ("eligible_for_empirical_fitting", "implementation_status")}))
    check("FEATURE_BUILDER_HAS_NO_FIT_FUNCTION", "model.fit(" not in (ROOT / "scripts/prediction_features_r3.py").read_text(encoding="utf-8"), "feature builder constructs samples only")
    return checks


def audit(report_path: Path = REPORT_PATH) -> dict[str, Any]:
    contract, contract_raw = load(CONTRACT_PATH)
    label, label_raw = load(LABEL_PATH)
    preflight, preflight_raw = load(PREFLIGHT_PATH)
    prereq, prereq_raw = load(PREREQUISITE_AUDIT_PATH)
    _, prereg_raw = load(PREREG_PATH)
    calendar, calendar_raw = load(CALENDAR_PATH)
    shard, _ = load(METHOD_SHARD_PATH)
    method = next((r for r in shard.get("rows", []) if r.get("method_id") == "PM0001"), None)
    if method is None:
        raise ContractValidationError("PM0001_METHOD_RECORD_MISSING")
    checks = validate_contract_objects(
        contract, label, preflight, prereq, method,
        calendar_id=calendar.get("calendar_id", ""),
        calendar_sha256=sha256(calendar_raw),
        source_csv_sha256=preflight.get("canonical_uncompressed_csv_sha256", ""),
    )
    # Verify source objects remain connected to the already frozen preregistration pins.
    scope = load(PREREG_PATH)[0].get("scope", {})
    source_checks = {
        "label_manifest_git_blob_sha1": git_blob_sha1(label_raw),
        "calendar_git_blob_sha1": git_blob_sha1(calendar_raw),
        "preflight_report_git_blob_sha1": git_blob_sha1(preflight_raw),
        "prerequisite_report_git_blob_sha1": git_blob_sha1(prereq_raw),
        "preregistration_git_blob_sha1": git_blob_sha1(prereg_raw),
        "contract_git_blob_sha1": git_blob_sha1(contract_raw),
        "contract_sha256": sha256(contract_raw),
        "label_manifest_sha256": sha256(label_raw),
        "calendar_sha256": sha256(calendar_raw),
    }
    if scope.get("label_manifest_git_blob_sha1") != source_checks["label_manifest_git_blob_sha1"]:
        raise ContractValidationError("PREREG_LABEL_MANIFEST_BLOB_PIN_MISMATCH")
    if scope.get("session_calendar_git_blob_sha1") != source_checks["calendar_git_blob_sha1"]:
        raise ContractValidationError("PREREG_CALENDAR_BLOB_PIN_MISMATCH")
    report = {
        "schema_version": "prediction-feature-construction-test-report-v1",
        "status": "PASS_FEATURE_CONTRACT_WITH_FITTING_BLOCKED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "check_count": len(checks),
        "checks_passed": sum(1 for c in checks if c["passed"]),
        "checks": checks,
        "verified_source_hashes": source_checks,
        "fitting_gate": {
            "empirical_fit_authorized": False,
            "holdout_accessed": False,
            "model_fitting_performed": False,
            "method_allowlist_authorized": [],
            "next_gate": "IMPLEMENT_AND_TEST_CHRONOLOGICAL_DEVELOPMENT_FOLD_EXECUTOR",
        },
        "raw_market_rows_in_report": False,
        "feature_samples_persisted": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=REPORT_PATH.relative_to(ROOT).as_posix())
    args = parser.parse_args()
    report = audit(ROOT / args.report)
    print(json.dumps({
        "status": report["status"],
        "check_count": report["check_count"],
        "checks_passed": report["checks_passed"],
        "empirical_fit_authorized": False,
        "report": args.report,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractValidationError as exc:
        print(json.dumps({"status": "BLOCKED_FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        raise SystemExit(2)
