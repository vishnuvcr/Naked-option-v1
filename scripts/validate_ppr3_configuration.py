#!/usr/bin/env python3
"""Offline PPR-3 configuration validation. No market data, network, or model fitting."""
from __future__ import annotations

import csv
import json
import sys
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "research/phase7/PPR3_CONFIGURATION_MATRIX.csv"
CELLS_PATH = ROOT / "research/phase7/PPR3_CANDIDATE_CELLS.csv"
SETTINGS_PATH = ROOT / "research/phase7/PPR3_MODEL_SETTINGS.json"
CONTRACT_PATH = ROOT / "research/phase7/PPR_TARGET_INFERENCE_CONTRACT.json"
MANIFEST_PATH = ROOT / "research/phase7/PPR3_CONFIGURATION_MANIFEST.json"
PROTOCOL_PATH = ROOT / "research/phase7/PPR3_PROTOCOL_FREEZE.md"
NATIVE_LEDGER_PATH = ROOT / "research/phase7/PPR3_PAPER_NATIVE_TASK_LEDGER.csv"

EXPECTED_FAMILY_COUNTS = {
    "COMMON_DIRECTION_3CLASS": 380,
    "COMMON_CLOSE_REGRESSION": 760,
    "NEXT_OPEN_REGRESSION": 48,
}
EXPECTED_PIPELINE_COUNTS = {
    "CORE_OHLCV_TECH": 307,
    "EXTERNAL_MARKET": 292,
    "FLOWS_OPTIONS": 292,
    "TIMESTAMPED_SENTIMENT_FUSION": 297,
}
EXPECTED_HORIZON_COUNTS = {1: 276, 2: 228, 3: 228, 5: 228, 10: 228}
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
    for path in (MATRIX_PATH, CELLS_PATH, SETTINGS_PATH, CONTRACT_PATH, MANIFEST_PATH, PROTOCOL_PATH, NATIVE_LEDGER_PATH):
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

    if len(matrix) != 81:
        errors.append(f"configuration matrix has {len(matrix)} rows; expected 81")
    ids = [r.get("config_id", "") for r in matrix]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        errors.append("configuration config_id values are blank or duplicated")
    active = {r["config_id"]: r for r in matrix if r.get("confirmatory_inference_member") == "true"}
    cap_rows = [r for r in matrix if r.get("counts_toward_93_cap") == "true"]
    blocked = [r for r in matrix if r.get("confirmatory_inference_member") != "true"]
    if len(active) != 72:
        errors.append(f"active config rows={len(active)}; expected 72")
    if len(cap_rows) != 73:
        errors.append(f"rows counted toward base-config cap={len(cap_rows)}; expected 73")
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
    # Protect scikit-learn's all-features float setting from int/float serialization drift.
    for template_name in ("BAGGING_CLASSIFIER", "BAGGING_REGRESSION", "RANDOM_FOREST_REGRESSION"):
        params = settings.get("templates", {}).get(template_name, {}).get("params", {})
        value = params.get("max_features")
        if type(value) is not float or value != 1.0:
            errors.append(f"{template_name}.max_features must be float 1.0 (all features), not integer 1")
    rf_grid = settings.get("tuning", {}).get("grids", {}).get("RANDOM_FOREST_REGRESSION", {})
    if not any(type(v) is float and v == 1.0 for v in rf_grid.get("max_features", [])):
        errors.append("Random Forest grid must preserve float 1.0 for all-features mode")
    for idx, candidate in enumerate(rf_grid.get("candidate_settings", [])):
        value = candidate.get("max_features")
        if value != "sqrt" and (type(value) is not float or value != 1.0):
            errors.append(f"Random Forest grid candidate {idx} max_features must be 'sqrt' or float 1.0")
    rf_text = settings.get("templates", {}).get("RANDOM_FOREST_REGRESSION", {}).get("preprocess", "")
    xgb_text = settings.get("templates", {}).get("XGBOOST_REGRESSION", {}).get("preprocess", "")
    if "R010" not in rf_text or "R038" not in rf_text:
        errors.append("Random Forest tuning scope must explicitly name R010 and R038")
    if "R029" not in xgb_text or "R041" not in xgb_text:
        errors.append("XGBoost tuning scope must explicitly name R029 and R041")
    cci = settings.get("templates", {}).get("CCI_20_DIRECTION", {}).get("params", {})
    if cci.get("lookback_sessions") != 20 or cci.get("state_thresholds", {}).get("bullish") != "CCI > +100" or cci.get("state_thresholds", {}).get("bearish") != "CCI < -100":
        errors.append("CCI adaptation must be predeclared as CCI(20) with +/-100 state thresholds")


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
    if len(cells) != 1188:
        errors.append(f"expanded candidate-cell ledger has {len(cells)} rows; expected 1188")
    if len(cell_keys) != len(set(cell_keys)):
        errors.append("duplicate config × pipeline × horizon cells found")
    actual_keys = set(cell_keys)
    missing = expected_keys - actual_keys
    extra = actual_keys - expected_keys
    if missing:
        errors.append(f"expanded ledger missing {len(missing)} matrix-derived cells; first={sorted(missing)[:5]}")
    if extra:
        errors.append(f"expanded ledger has {len(extra)} cells not permitted by active matrix; first={sorted(extra)[:5]}")
    # Source-native records are documented separately and never authorize fitting.
    native = read_csv(NATIVE_LEDGER_PATH)
    native_ids = [r.get("native_task_id", "") for r in native]
    native_papers = {r.get("source_paper_id", "") for r in native}
    if len(native) != 81:
        errors.append(f"paper-native task ledger has {len(native)} rows; expected 81")
    if any(not x for x in native_ids) or len(native_ids) != len(set(native_ids)):
        errors.append("paper-native native_task_id values are blank or duplicated")
    if native_papers != {f"P{i:02d}" for i in range(1, 16)}:
        errors.append("paper-native ledger must cover all P01-P15")
    native_by_id = {r.get("native_task_id", ""): r for r in native}
    # Source-to-adaptation semantics checks for previously corrected mappings.
    twitter = native_by_id.get("NT022", {})
    if "PIPELINE:TIMESTAMPED_SENTIMENT_FUSION" not in twitter.get("common_adaptation_links", "") or "C010" in twitter.get("common_adaptation_links", ""):
        errors.append("NT022 Twitter-mood component must link only to the sentiment pipeline, not BERT-LSTM C010")
    sofnn = native_by_id.get("NT023", {})
    blocked_sofnn = next((r for r in matrix if r.get("config_id") == "C011"), {})
    if sofnn.get("common_adaptation_links") != "C011" or blocked_sofnn.get("confirmatory_inference_member") != "false":
        errors.append("NT023 SOFNN must point to blocked C011, not an active substitute")
    for native_id in ("NT045", "NT046"):
        if native_by_id.get(native_id, {}).get("common_adaptation_links") != "NONE":
            errors.append(f"{native_id} strategy/descriptive average source must not be mapped to MA crossover configs")
    all_config_ids = set(ids)
    for native_row in native:
        if not native_row.get("source_method_or_component") or not native_row.get("method_source_locator"):
            errors.append(f"{native_row.get('native_task_id')}: method name and source locator are required")
        if native_row.get("ppr3_native_fidelity_row_only") != "true" or native_row.get("counts_toward_93_common_config_cap") != "false":
            errors.append(f"{native_row.get('native_task_id')}: native fidelity record must remain outside active model-fit cap")
        if native_row.get("executable_candidate_cell_count") != "0" or native_row.get("model_fit_authorized") != "false":
            errors.append(f"{native_row.get('native_task_id')}: native fidelity record cannot authorize execution")
        for link in [x for x in native_row.get("common_adaptation_links", "").split("|") if x and x != "NONE"]:
            if link.startswith(("PIPELINE:", "BASELINE:")):
                continue
            config_link = link.split(":", 1)[1] if link.startswith("CONFIG:") else link
            if config_link not in all_config_ids:
                errors.append(f"{native_row.get('native_task_id')}: unknown adaptation link {link}")

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
    expected_tuning_fits = (6 * 18 * 5) + (6 * 8 * 5)
    if settings.get("tuning", {}).get("calculated_tuning_fit_calls") != expected_tuning_fits:
        errors.append(f"tuning fit-call arithmetic incorrect; expected {expected_tuning_fits}")
    if settings.get("tuning", {}).get("fit_call_upper_bound") != 2000:
        errors.append("inner tuning fit-call ceiling must be 2000")
    outer_fits = len(cells) * 3
    total_fits = outer_fits + expected_tuning_fits
    if manifest.get("inventory", {}).get("active_candidate_cells") != len(cells):
        errors.append("manifest active candidate cell count differs from ledger")
    if manifest.get("inventory", {}).get("active_candidate_configuration_rows") != len(active):
        errors.append("manifest active configuration row count differs from matrix")
    if manifest.get("inventory", {}).get("configuration_ledger_rows") != len(matrix):
        errors.append("manifest configuration ledger row count differs from matrix")
    if manifest.get("inventory", {}).get("candidate_configuration_rows_counted_toward_cap") != len(cap_rows):
        errors.append("manifest cap-counted configuration rows differ from matrix")
    if manifest.get("inventory", {}).get("paper_native_method_rows") != len(native):
        errors.append("manifest paper-native method row count differs from ledger")
    if manifest.get("fit_budget", {}).get("actual_candidate_cell_count") != len(cells):
        errors.append("manifest actual candidate cell count differs from ledger")
    if manifest.get("fit_budget", {}).get("candidate_configuration_rows_counted") != len(cap_rows):
        errors.append("manifest fit-budget configuration row count differs from matrix")
    if manifest.get("fit_budget", {}).get("actual_configuration_rows_counted") != len(cap_rows):
        errors.append("manifest actual configuration row count differs from matrix")
    if manifest.get("fit_budget", {}).get("outer_fit_calls_upper_bound_at_3_seeds") != outer_fits:
        errors.append(f"outer fit-call cap incorrect; expected {outer_fits}")
    if manifest.get("fit_budget", {}).get("tuning", {}).get("counted_fit_calls") != expected_tuning_fits:
        errors.append("manifest tuning fit-call count incorrect")
    if manifest.get("fit_budget", {}).get("total_model_fit_calls_upper_bound") != total_fits:
        errors.append(f"total fit-call cap incorrect; expected {total_fits}")
    if manifest.get("fit_budget", {}).get("tuning", {}).get("fit_call_upper_bound") != 2000:
        errors.append("manifest tuning upper bound must equal 2000 inner fits")
    if manifest.get("fit_budget", {}).get("theoretical_total_fit_calls_upper_bound") != 7580:
        errors.append("theoretical total fit-call ceiling must be 7580 under current contract")
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
    direction_targets = contract.get("common_targets", [])
    direction_contract = next((x for x in direction_targets if x.get("family_id") == "COMMON_DIRECTION_3CLASS"), {})
    flat_text = direction_contract.get("flat_semantics", "")
    if "numerical zero-return tie" not in flat_text or "not an economically neutral move" not in flat_text:
        errors.append("FLAT semantics must state numerical tie only, not economically neutral/no-trade")
    if "FLAT means only a numerical zero-return tie" not in PROTOCOL_PATH.read_text(encoding="utf-8"):
        errors.append("protocol freeze must document the fixed FLAT numerical-tie meaning")
    if not manifest.get("frozen_files", {}).get("configuration_matrix", {}).get("blob"):
        errors.append("manifest lacks matrix blob reference")
    if not manifest.get("frozen_files", {}).get("expanded_candidate_cells", {}).get("blob"):
        errors.append("manifest lacks expanded-cell blob reference")

    # Verify pinned blobs only after the final snapshot is explicitly enabled.
    if manifest.get("snapshot_checks_enabled") is True:
        pins = list(manifest.get("frozen_files", {}).values()) + list(manifest.get("source_artifacts", {}).values())
        for entry in pins:
            if not isinstance(entry, dict):
                errors.append("manifest pin must be an object")
                continue
            rel = entry.get("path", "")
            expected_blob = entry.get("blob", "")
            if not rel or not expected_blob:
                errors.append("manifest pin requires path and blob")
                continue
            path = ROOT / rel
            if not path.is_file():
                errors.append(f"manifest-pinned file missing: {rel}")
                continue
            try:
                actual_blob = subprocess.run(["git", "hash-object", str(path)], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
            except (OSError, subprocess.CalledProcessError) as exc:
                errors.append(f"cannot hash manifest-pinned file {rel}: {exc}")
                continue
            if actual_blob != expected_blob:
                errors.append(f"manifest blob mismatch for {rel}: expected {expected_blob}, got {actual_blob}")

    return errors


def main() -> int:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read PPR-3 manifest: {exc}")
        return 2
    if manifest.get("staging_mode") is True:
        print("STAGING ONLY: PPR-3 structural and blob-pin checks are intentionally skipped while tester-requested documentation corrections are staged.")
        print("No gate PASS is asserted. No source requests, market-data reads, model fitting, tuning, scoring or holdout access occurred.")
        return 0
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
