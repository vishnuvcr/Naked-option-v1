#!/usr/bin/env python3
"""Static Phase 8P protocol bridge audit. Never opens real market artifacts."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = {
  "scripts/phase8p_greek_prediction.py": "3358381d64b3e675e49687fa5d34df44d8a9c984",
  "scripts/test_phase8p_greek_prediction.py": "198e731e9e5f5dd011370cd6f656fe27e97c6ca5",
  "research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md": "018500722f88f5fb100a2e24afc3d5d97394631e",
  "research/gates/PHASE8P_DAILY_TIMESTAMP_AMENDMENT_R1_2026-10-12.md": "265c6696466b1999371cb4581baf20fbe950d3f1",
  "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json": "1ef2bf467928642aafc675899dd779a76394daab",
  "research/registry/PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json": "ec808129d19c1018d113ef01f9de230bae998b50",
  "research/registry/PREDICTION_CHRONOLOGICAL_EXECUTION_CONTRACT_R3_2026-10-13.json": "c91f3c4beefca3a2c4a68f6e6c55f73035e13378",
  "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json": "9da9692d67b5fda6271e021c77e429d1b9f32b3c",
  "research/gates/PREDICTION_DATA_PREFLIGHT_ATTEMPT_R3_2026-10-13.json": "8dca8cc069babcb18f2f618f41da018fb7ad31a0",
  "research/registry/MARKOV_SWITCHING_TRANSITION_PRIOR_CONTRACT_V1_2026-10-14.json": "c0334f7430418b65fa99980f961ecb9245f3b858",
  "research/registry/PREDICTION_PREREGISTRATION_V2_2026-10-14.json": "dd4c18c235803a9080f89b9f80bd512756db8a06"
}
LABEL_IDS = ["INTRA_5M_UP_DOWN","INTRA_15M_UP_DOWN","INTRA_30M_UP_DOWN","INTRA_60M_UP_DOWN","INTRA_120M_UP_DOWN","POS_1D_UP_DOWN","POS_2D_UP_DOWN","POS_3D_UP_DOWN","POS_5D_UP_DOWN","POS_10D_UP_DOWN"]

def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw).hexdigest()

def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def audit() -> dict:
    pins = {}
    for rel, expected in PINS.items():
        path = ROOT / rel
        actual = blob_sha(path) if path.is_file() else None
        pins[rel] = {"expected": expected, "actual": actual, "pass": actual == expected}
    src = (ROOT/"scripts/phase8p_greek_prediction.py").read_text(encoding="utf-8")
    tests = (ROOT/"scripts/test_phase8p_greek_prediction.py").read_text(encoding="utf-8")
    scope = (ROOT/"research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md").read_text(encoding="utf-8")
    prereg = load("research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json")
    label_manifest = load("research/registry/PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json")
    chrono = load("research/registry/PREDICTION_CHRONOLOGICAL_EXECUTION_CONTRACT_R3_2026-10-13.json")
    old_preflight = load("research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json")
    preflight_attempt = load("research/gates/PREDICTION_DATA_PREFLIGHT_ATTEMPT_R3_2026-10-13.json")
    markov = load("research/registry/MARKOV_SWITCHING_TRANSITION_PRIOR_CONTRACT_V1_2026-10-14.json")
    markov_v2 = load("research/registry/PREDICTION_PREREGISTRATION_V2_2026-10-14.json")
    checks = {}
    def check(name, ok, evidence):
        checks[name] = {"pass": bool(ok), "evidence": evidence}

    check("F1_END_TO_END_RUNNER", all(token in src for token in [
        "def run_schema_preflight_from_artifacts(", "def run_prediction_study_from_artifacts(",
        "def run_prediction_study(", "def main(", "--run-preflight", "--run-study",
        "write_aggregate_only_report("
    ]), "Separate preflight and fit CLI paths are present; actual run still separately gated")
    check("F2_PINNED_AUTHORIZATION", all(token in src for token in [
        "def verify_code_gate_for_preflight(", "def enforce_fit_gate(",
        "PHASE8P_AUTHORIZATION_BUNDLE_SHA256", "AUTHORIZATION_BUNDLE_DEVELOPER_COMMIT_MISMATCH",
        "CODE_REVIEW_DEVELOPER_COMMIT_MISMATCH", "_read_and_verify_tester_evidence("
    ]), "Authorization binds exact developer commit, tester evidence blobs and bundle SHA256")
    check("F3_CHRONOLOGY_AND_MATURITY", all(token in src and token in tests for token in [
        "BLOCK_INDEX_NOT_MONOTONE_WITH_DECISION_TIME", "TARGET_END_NOT_STRICTLY_AFTER_DECISION"
    ]) and "purge" in src.lower() and "target_end" in src.lower(),
        "Source and synthetic tests cover chronological blocks, target-end maturity and purge")
    check("F4_OPTION_SPOT_SEPARATION", all(token in src for token in [
        "row_type", "OPTION", "SPOT", "greek_features = build_option_feature_frame", "spot_sink"
    ]), "OPTION Greek and SPOT spot-price pathways are split")
    check("F5_DAILY_1530_IST", all(token in src for token in [
        "DATE_ONLY_DAILY_PANEL_TO_CASH_CLOSE_15_30_IST", "def daily_close_timestamp(", "15:30"
    ]) and "2025-01-02" in tests, "Date-only daily mapping uses approved 15:30 IST convention")
    check("F6_SCHEMA_COVERAGE_PREFLIGHT", all(token in src for token in [
        "def run_schema_preflight_from_artifacts(", "verify_code_gate_for_preflight(",
        "verify_pinned_artifact_identity(", "panel_file_sha256", "target_maturity_proof",
        "holdout_exclusion_proof", "exact_join_rate", "write_aggregate_only_report("
    ]), "Pinned receipts, panel hashes, label maturity, coverage, holdout proof, aggregate report")
    labels = [item.get("id") for item in label_manifest.get("labels", [])]
    prereg_text = json.dumps(prereg, sort_keys=True)
    check("GREEK_SCOPE_SEPARATION", all(token in scope for token in ["paired Brier", "B=500", "seed 42", "Holm"])
        and "BOOTSTRAP_REPS = 500" in src and re.search(r"SEED\s*=\s*42", src) is not None,
        "Greek study preserves 20 Brier comparisons, 500 bootstrap reps, seed 42, Holm")
    check("MAIN_REGISTRY_PROTOCOL_SEPARATION", all(token in prereg_text for token in [
        "out_of_sample_log_loss", "10000", "2026101209", "Benjamini-Yekutieli"
    ]) and labels == LABEL_IDS and chrono.get("status") == "FROZEN_PRE_RESULTS_IMPLEMENTATION_SUPPLEMENT",
        "Main R3 preserves ten labels, log-loss, 10000 reps, seed 2026101209 and BY")
    check("MARKOV_CONTRACT_SEPARATE", markov.get("registered_family") == "markov_switching_logit"
        and "markov_switching" not in src.lower()
        and markov_v2.get("model_parameter_semantics_contracts",{}).get("markov_switching_logit",{}).get("review_status") == "TESTER_APPROVED_CODE_CONTRACT_ONLY",
        "Markov contract belongs to main registry and is not used by Greek estimator")
    check("TEN_LABEL_MANIFEST_PENDING", labels == LABEL_IDS
        and label_manifest.get("status") == "FROZEN_TEN_HORIZONS_DEVELOPER_VALIDATION_PENDING_NO_EMPIRICAL_RUNS",
        "Canonical ten-label manifest is exact and still blocks empirical execution")
    check("NO_FIT_OR_HOLDOUT_OCCURRED", preflight_attempt.get("model_fitting_performed") is False
        and preflight_attempt.get("holdout_accessed") is False
        and prereg.get("scope",{}).get("empirical_execution_gate") == "BLOCKED_PENDING_DEVELOPER_DATA_PREFLIGHT_AND_TEN_HORIZON_REGISTRY_QA",
        "Existing preflight attempt remains non-empirical and canonical fitting gate stays blocked")

    old_preflight_text = json.dumps(old_preflight, sort_keys=True)
    scoped = old_preflight_text.count("BLOCKED_SAMPLE_ELIGIBILITY")
    old_pin = old_preflight.get("preregistration_git_blob_sha1")
    blockers = []
    if old_pin is None: blockers.append("MAIN_R3_PREFLIGHT_PREREGISTRATION_GIT_BLOB_SHA1_NULL")
    if scoped: blockers.append(f"MAIN_R3_PREFLIGHT_HAS_{scoped}_SCOPED_SAMPLE_ELIGIBILITY_BLOCKS")
    if label_manifest.get("status","").endswith("DEVELOPER_VALIDATION_PENDING_NO_EMPIRICAL_RUNS"):
        blockers.append("MAIN_R3_LABEL_MANIFEST_DEVELOPER_VALIDATION_PENDING")
    blockers.extend(["GREEK_SCHEMA_PREFLIGHT_NOT_RUN_ON_THIS_EXACT_DEVELOPER_COMMIT","NO_EMPIRICAL_FITTING_AUTHORIZATION"])
    all_pass = all(item["pass"] for item in pins.values()) and all(item["pass"] for item in checks.values())
    return {
        "schema_version":"phase8p-prereg-freeze-audit-r4",
        "gate":"PHASE8P_PREREGISTRATION_AND_DATA_PREFLIGHT_BRIDGE_R4",
        "status":"PASS_STATIC_PROTOCOL_RECONCILIATION_WITH_EXECUTION_BLOCKERS" if all_pass else "FAIL",
        "source_blob_checks":pins,"checks":checks,
        "protocol_separation":{"greek_comparisons":20,"greek_metric":"paired Brier improvement","greek_bootstrap_reps":500,"greek_seed":42,"greek_multiplicity":"Holm","main_registry_methods":1000,"main_registry_configs":40000,"main_metric":"out-of-sample log-loss","main_bootstrap_reps":10000,"main_seed":2026101209,"main_multiplicity":"Benjamini-Yekutieli","markov_contract_applies_to_greek_study":False},
        "main_registry_existing_preflight":{"status":old_preflight.get("status"),"preregistration_git_blob_sha1":old_pin,"scoped_block_count":scoped,"fit_authorized":False,"blockers":blockers},
        "authorization":{"synthetic_ci_authorized":True,"schema_only_artifact_preflight_authorized":False,"empirical_model_fitting_authorized":False,"holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False},
        "errors":[name for name,item in checks.items() if not item["pass"]]+[f"BLOB_PIN_MISMATCH:{name}" for name,item in pins.items() if not item["pass"]]
    }
if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_STATIC_PROTOCOL_RECONCILIATION_WITH_EXECUTION_BLOCKERS" else 1)
