#!/usr/bin/env python3
"""Offline structural checks for the proposed PPR protocol; no market data is opened."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/phase7/PPR_TARGET_INFERENCE_CONTRACT.json"
MATRIX = ROOT / "research/literature/PAPER_SOURCE_EVIDENCE_MATRIX.md"


def validate(contract, matrix_text):
    errors = []
    if contract.get("status") != "PROPOSED_NOT_AUTHORIZED":
        errors.append("contract must remain proposed/not authorized")
    boundary = contract.get("hard_boundary", {})
    for key in ("empirical_execution_authorized", "new_source_pulls_authorized",
                "final_holdout_access_authorized", "options_pnl_authorized"):
        if boundary.get(key) is not False:
            errors.append(f"hard boundary {key} must be false")
    for n in range(1, 16):
        if f"## Paper {n} " not in matrix_text:
            errors.append(f"source matrix missing paper {n}")
    targets = {x.get("family_id"): x for x in contract.get("common_targets", [])}
    expected = {"COMMON_DIRECTION_3CLASS", "COMMON_CLOSE_REGRESSION", "NEXT_OPEN_REGRESSION"}
    if set(targets) != expected:
        errors.append("unexpected or missing common target family")
    direction = targets.get("COMMON_DIRECTION_3CLASS", {})
    if direction.get("classes_in_fixed_order") != ["DOWN", "FLAT", "UP"]:
        errors.append("direction classes must be DOWN, FLAT, UP")
    if direction.get("horizons_sessions") != [1, 2, 3, 5, 10]:
        errors.append("direction horizons are not frozen")
    if direction.get("primary_metric") != "multiclass_brier_loss":
        errors.append("direction primary metric must be multiclass Brier")
    if targets.get("COMMON_CLOSE_REGRESSION", {}).get("baseline_prediction_formula") != "baseline_close_hat[t+h]=close[t]":
        errors.append("close persistence formula mismatch")
    if targets.get("NEXT_OPEN_REGRESSION", {}).get("baseline_prediction_formula") != "baseline_open_hat[t+1]=close[t]":
        errors.append("next-open persistence formula mismatch")
    inf = contract.get("inference", {})
    if inf.get("replicates") != 10000 or not isinstance(inf.get("seed"), int):
        errors.append("bootstrap replication count/seed missing")
    if "d0[i,j]=d[i,j]-mean(d[,j])" not in inf.get("null_centering", ""):
        errors.append("bootstrap null centering is unspecified")
    if "(1 + count(T_star >= T_obs))/(1 + B)" != inf.get("adjusted_p_value"):
        errors.append("adjusted p-value formula mismatch")
    if "INCOMPLETE_NOT_PROMOTABLE" not in inf.get("missing_candidate_rule", ""):
        errors.append("missing candidate must block confirmation")
    if inf.get("minimum_valid_rows", 0) < 250:
        errors.append("minimum valid row count below 250")
    bounds = contract.get("search_bounds", {})
    if bounds.get("max_outer_model_cells") != bounds.get("max_estimator_or_architecture_configs", 0) * bounds.get("max_feature_pipeline_classes", 0) * len(bounds.get("common_horizons", [])):
        errors.append("outer model-cell cap mismatch")
    if bounds.get("max_inner_hyperparameter_trials_total") != bounds.get("max_tuned_candidate_configs", 0) * bounds.get("max_inner_hyperparameter_configs_per_candidate", 0):
        errors.append("inner search cap mismatch")
    return errors


def main():
    try:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        matrix = MATRIX.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2
    errors = validate(contract, matrix)
    if errors:
        print("\n".join(f"FAIL: {e}" for e in errors))
        return 1
    print("PASS: source matrix, target/inference contract, search bounds and fail-closed flags.")
    print("Offline structure check only; no source requests, market-data access or model fitting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
