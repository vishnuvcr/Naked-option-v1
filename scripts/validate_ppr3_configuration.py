#!/usr/bin/env python3
"""Offline PPR-3 configuration validation. No market data, network, or model fitting."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "research/phase7/PPR3_CONFIGURATION_MATRIX.csv"
CELLS_PATH = ROOT / "research/phase7/PPR3_CANDIDATE_CELLS.csv"
SETTINGS_PATH = ROOT / "research/phase7/PPR3_MODEL_SETTINGS.json"
CONTRACT_PATH = ROOT / "research/phase7/PPR_TARGET_INFERENCE_CONTRACT.json"
MANIFEST_PATH = ROOT / "research/phase7/PPR3_CONFIGURATION_MANIFEST.json"
PROTOCOL_PATH = ROOT / "research/phase7/PPR3_PROTOCOL_FREEZE.md"

EXPECTED_FAMILY_COUNTS = {
    "COMMON_DIRECTION_3CLASS": 375,
    "COMMON_CLOSE_REGRESSION": 760,
    "NEXT_OPEN_REGRESSION": 48,
}
EXPECTED_PIPELINE_COUNTS = {
    "CORE_OHLCV_TECH": 302,
    "EXTERNAL_MARKET": 292,
    "FLOWS_OPTIONS": 292,
    "TIMESTAMPED_SENTIMENT_FUSION": 297,
}
EXPECTED_HORIZON_COUNTS = {1: 275, 2: 227, 3: 227, 5: 227, 10: 227}
EXPECTED_TUNING_CELLS = {
    ("R010", "CORE_OHLCV_TECH", 1), ("R010", "CORE_OHLCV_TECH", 2),
    ("R010", "CORE_OHLCV_TECH", 3), ("R010", "CORE_OHLCV_TECH", 5),
    ("R010", "CORE_OHLCV_TECH", 10),
    ("R029", "CORE_OHLCV_TECH", 1), ("R029", "CORE_OHLCV_TECH", 2),
    ("R029", "CORE_OHLCV_TECH", 3), ("R029", "CORE_OHLCV_TECH", 5),
    ("R029", "CORE_OHLCV_TECH", 10),
    ("R038", "CORE_OHLCV_TECH", 1), ("R041", "CORE_OHLCV_TECH", 1),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def validate() -> list[str]:
    errors: list[str] = []
    for path in (MATRIX_PATH, CELLS_PATH, SETTINGS_PATH, CONTRACT_PATH, MANIFEST_PATH, PROTOCOL_PATH):
        if not path.is_file():
            errors.append(f"required PPR-3 file missing: {path.relative_to(ROOT)}")
    if errors:
        return errors

    try:
        matrix = read_csv(MATRIX_PATH)
        cells = read_csv(CELLS_PATH)
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        return [f"cannot parse a required PPR-3 artifact: {exc}"]

    if len(matrix) != 80:
        errors.append(f"configuration matrix has {len(matrix)} rows; expected 80")
    ids = [r.get("config_id", "") for r in matrix]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        errors.append("configuration config_id values are blank or duplicated")
    active = {r["config_id"]: r for r in matrix if r.get("confirmatory_inference_member") == "true"}
    cap_rows = [r for r in matrix if r.get("counts_toward_93_cap") == "true"]
    blocked = [r for r in matrix if r.get("confirmatory_inference_member") != "true"]
    if len(active) != 71:
        errors.append(f"active config rows={len(active)}; expected 71")
    if len(cap_rows) != 72:
        errors.append(f"rows counted toward base-config cap={len(cap_rows)}; expected 72")
    if len(cap_rows) > contract.get("search_bounds", {}).get("max_estimator_or_architecture_configs", 0):
        errors.append("base configuration rows exceed the contract cap")
    if len(blocked) != 9:
        errors.append(f"blocked/backlog rows={len(blocked)}; expected 9")
    for row in blocked:
        if row.get("confirmatory_inference_member") != "false":
            errors.append(f"{row.get('config_id')}: blocked row must not be a confirmatory candidate")
        if int(row.get("max_evaluation_cells", "0") or 0) != 0 or int(row.get("max_fit_calls_at_3_seeds", "0") or 0) != 0:
            errors.append(f"{row.get('config_id')}: blocked/out-of-scope row has nonzero forecast cells or fit calls")

    template_ids = set(settings.get("templates", {}))
    alias_ids = set(settings.get("aliases", {}))
    blocked_setting_ids = set(settings.get("blocked_settings", {}))
    setting_ids = template_ids | alias_ids | blocked_setting_ids
    for row in matrix:
        setting = row.get("settings_id", "")
        if setting and setting not in setting_ids:
            errors.append(f"{row.get('config_id')}: settings_id {setting} unresolved in settings/templates/aliases/blocked_settings")
    for key, alias in settings.get("aliases", {}).items():
        if alias not in template_ids:
            errors.append(f"settings alias {key} points to unknown template {alias}")
    for key, obj in settings.get("templates", {}).items():
        if isinstance(obj, dict) and obj.get("status") == "BLOCKED_METHOD":
            if key not in blocked_setting_ids:
                errors.append(f"blocked template {key} must be listed in blocked_settings")

    # Reconcile each matrix active row to its expanded pipeline × horizon cells.
    expected_keys = set()
    for config_id, row in active.items():
        pipes = [p for p in row.get("feature_pipeline_scope", "").split("|") if p]
        horizons = [int(h) for h in row.get("common_horizons_sessions", "").split("|") if h]
        if not pipes or not horizons:
            errors.append(f"{config_id}: active row has empty pipeline or horizon scope")
            continue
        for pipe in pipes:
            for horizon in horizons:
                expected_keys.add((config_id, pipe, horizon))
    cell_keys = [
        (r.get("config_id", ""), r.get("feature_pipeline_id", ""), int(r.get("horizon_sessions", "0") or 0))
        for r in cells
    ]
    if len(cells) != 1183:
        errors.append(f"expanded candidate-cell ledger has {len(cells)} rows; expected 1183")
    if len(cell_keys) != len(set(cell_keys)):
        errors.append("duplicate config × pipeline × horizon cells found")
    actual_keys = set(cell_keys)
    missing = expected_keys - actual_keys
    extra = actual_keys - expected_keys
    if missing:
        errors.append(f"expanded ledger missing {len(missing)} matrix-derived cells; first={sorted(missing)[:5]}")
    if extra:
        errors.append(f"expanded ledger has {len(extra)} cells not permitted by active matrix; first={sorted(extra)[:5]}")
    for row in cells:
        cid = row.get("config_id", "")
        if cid not in active:
            errors.append(f"expanded cell references inactive/unknown config {cid}")
            continue
        m = active[cid]
        if row.get("target_schema_id") != m.get("target_schema_id"):
            errors.append(f"{row.get('cell_id')}: target schema differs from config matrix")
        if row.get("inferential_family_id") != m.get("inferential_family_id"):
            errors.append(f"{row.get('cell_id')}: inferential family differs from config matrix")
        if row.get("settings_id") != m.get("settings_id"):
            errors.append(f"{row.get('cell_id')}: settings_id differs from config matrix")
        if row.get("status") != "PROPOSED_NOT_AUTHORIZED":
            errors.append(f"{row.get('cell_id')}: status must remain PROPOSED_NOT_AUTHORIZED")
        if row.get("execution_gate") != "PPR4_DATA_GATE_THEN_PPR5_CODE_GATE_THEN_PPR6_EXACT_SNAPSHOT_PASS":
            errors.append(f"{row.get('cell_id')}: unexpected execution authorization chain")
        if row.get("tuned_inner_search") == "true" and row.get("feature_pipeline_id") != "CORE_OHLCV_TECH":
            errors.append(f"{row.get('cell_id')}: tuning outside the frozen CORE pipeline")

    families = Counter(r.get("inferential_family_id", "") for r in cells)
    for key, expected in EXPECTED_FAMILY_COUNTS.items():
        if families.get(key, 0) != expected:
            errors.append(f"{key} has {families.get(key, 0)} cells; expected {expected}")
    pipelines = Counter(r.get("feature_pipeline_id", "") for r in cells)
    for key, expected in EXPECTED_PIPELINE_COUNTS.items():
        if pipelines.get(key, 0) != expected:
            errors.append(f"{key} has {pipelines.get(key, 0)} cells; expected {expected}")
    horizons = Counter(int(r.get("horizon_sessions", "0") or 0) for r in cells)
    for key, expected in EXPECTED_HORIZON_COUNTS.items():
        if horizons.get(key, 0) != expected:
            errors.append(f"horizon {key} has {horizons.get(key, 0)} cells; expected {expected}")

    tuned = {
        (r.get("config_id", ""), r.get("feature_pipeline_id", ""), int(r.get("horizon_sessions", "0") or 0))
        for r in cells if r.get("tuned_inner_search") == "true"
    }
    if tuned != EXPECTED_TUNING_CELLS:
        errors.append(f"tuning cells differ from frozen 12-cell set; actual={sorted(tuned)}")
    grids = settings.get("tuning", {}).get("grids", {})
    if len(grids.get("RANDOM_FOREST_REGRESSION", {}).get("candidate_settings", [])) != 18:
        errors.append("Random Forest tuning grid must list exactly 18 candidate settings")
    if len(grids.get("XGBOOST_REGRESSION", {}).get("candidate_settings", [])) != 8:
        errors.append("XGBoost tuning grid must list exactly 8 candidate settings")
    if settings.get("tuning", {}).get("actual_candidate_cells") != 12:
        errors.append("model settings tuning count must be 12")
    expected_tuning_fits = (6 * 18 * 6) + (6 * 8 * 6)
    if settings.get("tuning", {}).get("calculated_tuning_fit_calls") != expected_tuning_fits:
        errors.append(f"tuning fit-call arithmetic incorrect; expected {expected_tuning_fits}")
    outer_fits = len(cells) * 3
    total_fits = outer_fits + expected_tuning_fits
    if manifest.get("inventory", {}).get("active_candidate_cells") != len(cells):
        errors.append("manifest active candidate cell count differs from ledger")
    if manifest.get("inventory", {}).get("active_candidate_configuration_rows") != len(active):
        errors.append("manifest active configuration row count differs from matrix")
    if manifest.get("fit_budget", {}).get("outer_fit_calls_upper_bound_at_3_seeds") != outer_fits:
        errors.append(f"outer fit-call cap incorrect; expected {outer_fits}")
    if manifest.get("fit_budget", {}).get("tuning", {}).get("counted_fit_calls") != expected_tuning_fits:
        errors.append("manifest tuning fit-call count incorrect")
    if manifest.get("fit_budget", {}).get("total_model_fit_calls_upper_bound") != total_fits:
        errors.append(f"total fit-call cap incorrect; expected {total_fits}")
    hard_cap = contract.get("search_bounds", {}).get("max_total_fit_calls_including_inner_folds", 0)
    if total_fits > hard_cap:
        errors.append(f"planned fits {total_fits} exceed global cap {hard_cap}")
    if manifest.get("hard_boundary", {}).get("model_fitting_tuning_scoring_authorized") is not False:
        errors.append("manifest must keep model fitting/tuning/scoring unauthorized")
    if manifest.get("hard_boundary", {}).get("final_holdout_access_authorized") is not False:
        errors.append("manifest must keep final holdout access unauthorized")
    if manifest.get("hard_boundary", {}).get("new_source_requests_authorized") is not False:
        errors.append("manifest must keep new source requests unauthorized")
    if settings.get("status") != "PROPOSED_NOT_AUTHORIZED":
        errors.append("model settings must remain proposed/not authorized")
    if contract.get("status") != "PROPOSED_NOT_AUTHORIZED":
        errors.append("target/inference contract must remain proposed/not authorized")
    if contract.get("evaluation_protocol", {}).get("status") != "PROPOSED_FOR_TESTER_REVIEW":
        errors.append("evaluation protocol must remain proposed for tester review")
    if not manifest.get("frozen_files", {}).get("configuration_matrix", {}).get("blob"):
        errors.append("manifest lacks matrix blob reference")
    if not manifest.get("frozen_files", {}).get("expanded_candidate_cells", {}).get("blob"):
        errors.append("manifest lacks expanded-cell blob reference")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: PPR-3 configuration rows, candidate-cell expansion, target families, tuning grids and fit budget reconcile.")
    print("Scope: offline documentation/schema validation only. No source requests, market-data reads, model fitting, tuning, scoring or holdout access.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
