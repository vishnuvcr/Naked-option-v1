#!/usr/bin/env python3
"""Fail-closed accounting executor: emits one terminal row per config x outer fold.

This is not a model executor. It intentionally performs zero fitting until method
implementation/test approval and empirical authorization are explicitly granted.
"""
import gzip, hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(v): return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def read_json(path): return json.loads((ROOT / path).read_text(encoding="utf-8"))
def main(out_path):
    cm_path = "research/registry/PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json"
    ci_path = "research/registry/PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
    pre_path = "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
    prereg_path = "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
    cm, ci, pre, prereg = map(read_json, (cm_path, ci_path, pre_path, prereg_path))
    if pre.get("status") != "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS": raise ValueError("PREFLIGHT_STATUS_NOT_APPROVED")
    if pre.get("canonical_hash_matches") is not True: raise ValueError("PREFLIGHT_CANONICAL_HASH_NOT_VERIFIED")
    if pre.get("expected_canonical_csv_sha256") != pre.get("canonical_uncompressed_csv_sha256"): raise ValueError("PREFLIGHT_CANONICAL_HASH_DISAGREEMENT")
    if pre.get("model_fitting_performed") is not False or pre.get("holdout_accessed") is not False: raise ValueError("PREFLIGHT_PROVENANCE_FLAGS_UNSAFE")
    compat = {}
    for sh in ci["shards"]:
        raw = (ROOT / sh["path"]).read_bytes()
        if len(raw) != sh["bytes"] or sha(raw) != sh["sha256"]: raise ValueError("COMPAT_SHARD_HASH_MISMATCH:"+sh["path"])
        rows = json.loads(raw)["rows"]
        if len(rows) != sh["record_count"]: raise ValueError("COMPAT_SHARD_COUNT_MISMATCH:"+sh["path"])
        for row in rows:
            if row["method_id"] in compat: raise ValueError("DUPLICATE_METHOD:"+row["method_id"])
            compat[row["method_id"]] = row
    configs = []
    for sh in cm["config_shards"]:
        raw = (ROOT / sh["path"]).read_bytes()
        if len(raw) != sh["byte_count"] or sha(raw) != sh["sha256"]: raise ValueError("CONFIG_SHARD_HASH_MISMATCH:"+sh["path"])
        rows = json.loads(raw)["configs"]
        if len(rows) != sh["count"]: raise ValueError("CONFIG_SHARD_COUNT_MISMATCH:"+sh["path"])
        for row in rows:
            if sha(canonical(row["configuration"])) != row["config_sha256"]: raise ValueError("CONFIG_DIGEST_MISMATCH:"+row["config_id"])
            configs.append(row)
    if len(configs) != cm["configuration_count"] or len(compat) != ci["record_count"]: raise ValueError("REGISTRY_TOTAL_MISMATCH")
    windows = prereg["chronological_validation"]["fold_calendar_windows"]
    labels = prereg["labels"]
    pre_rows = pre.get("label_sample_support", [])
    cell = {}
    for row in pre_rows:
        key=(row.get("label_id"),row.get("fold_id"))
        if key in cell: raise ValueError("DUPLICATE_PREFLIGHT_CELL:"+str(key))
        cell[key]=row
    expected_labels = set(cm["configurations_per_label"])
    if set(labels) != expected_labels: raise ValueError("PREREG_LABEL_SET_MISMATCH")
    if len(windows) != 8: raise ValueError("OUTER_FOLD_COUNT_MISMATCH")
    if len(cell) != len(expected_labels)*len(windows): raise ValueError("PREFLIGHT_GRID_INCOMPLETE")
    source_hash = pre.get("canonical_uncompressed_csv_sha256")
    if not isinstance(source_hash,str) or len(source_hash)!=64: raise ValueError("CANONICAL_SOURCE_HASH_MISSING")
    output = Path(out_path); output.parent.mkdir(parents=True, exist_ok=True)
    counts=Counter(); seen=set(); rows_written=0
    with gzip.open(output,"wt",encoding="utf-8",newline="") as f:
        for cfg in sorted(configs,key=lambda x:x["config_id"]):
            detail=cfg["configuration"]; mid=cfg["method_id"]; label=detail["label_id"]
            method=compat.get(mid)
            if method is None: raise ValueError("CONFIG_METHOD_NOT_REGISTERED:"+mid)
            for fold in windows:
                fid=fold["id"]; key=(cfg["config_id"],fid)
                if key in seen: raise ValueError("DUPLICATE_CONFIG_FOLD:"+str(key))
                seen.add(key)
                pre_cell=cell[(label,fid)]
                if pre_cell.get("passes_frozen_data_minima") is not True:
                    status="BLOCKED_DATA"
                    reasons=pre_cell.get("block_reasons") or ["PREFLIGHT_CELL_BLOCKED_WITHOUT_REASON"]
                    reason="PREFLIGHT_BLOCK:"+",".join(map(str,reasons))
                elif method.get("compatibility_decision") != "ALLOW_IN_PRINCIPLE":
                    status="BLOCKED_GATE"; reason="METHOD_COMPATIBILITY_BLOCK"
                elif method.get("implementation_status") != "TESTER_APPROVED":
                    status="BLOCKED_GATE"; reason="IMPLEMENTATION_OR_TESTER_APPROVAL_MISSING"
                elif method.get("eligible_for_empirical_fitting") is not True:
                    status="BLOCKED_GATE"; reason="EMPIRICAL_FIT_AUTHORIZATION_MISSING"
                else:
                    # Deliberate fail-closed branch. This script never fits models.
                    status="BLOCKED_GATE"; reason="NO_FITTING_ENGINE_IN_ACCOUNTING_EXECUTOR"
                row={
                  "config_id":cfg["config_id"],"method_id":mid,"label_id":label,"fold_id":fid,
                  "train_start":prereg["chronological_validation"]["calendar_range"][0],
                  "train_end":fold["start"],"validation_start":fold["start"],"validation_end":fold["end_inclusive"],
                  "eligible_train_rows":0,"eligible_validation_rows":0,"positive_support":0,"negative_support":0,
                  "feature_missingness":None,"label_exclusion_count":None,
                  "baseline_log_loss":None,"candidate_log_loss":None,"log_loss_improvement":None,
                  "bootstrap_ci_lower":None,"bootstrap_ci_upper":None,"raw_p_value":None,"by_adjusted_p_value":None,
                  "terminal_status":status,"failure_reason":reason,"label_target_endpoint":None,
                  "purge_sessions":detail["purge_exchange_sessions"],"embargo_sessions":detail["embargo_exchange_sessions"],
                  "class_prior_baseline_log_loss":None,"previous_sign_baseline_log_loss":None,"brier_score":None,
                  "balanced_accuracy":None,"roc_auc":None,"average_precision":None,"calibration_intercept":None,
                  "calibration_slope":None,"observed_session_count":0,"bootstrap_status":"NOT_RUN","bootstrap_replicates":0,
                  "by_family_id":label,"source_manifest_sha256":source_hash,"train_positive_support":0,
                  "train_negative_support":0,"created_utc":"2026-10-13T00:00:00+00:00",
                  "model_fitting_performed":False,"holdout_accessed":False
                }
                f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
                counts[status]+=1; rows_written+=1
    expected=len(configs)*len(windows)
    if rows_written != expected or len(seen)!=expected: raise ValueError("TERMINAL_ROW_COVERAGE_MISMATCH")
    summary={
      "schema_version":"prediction-fail-closed-accounting-r3","status":"PASS_COMPLETE_BLOCKED_ACCOUNTING",
      "configurations":len(configs),"outer_folds":len(windows),"expected_terminal_rows":expected,
      "terminal_rows_written":rows_written,"unique_config_fold_pairs":len(seen),
      "terminal_status_counts":dict(sorted(counts.items())),"config_shards_verified":len(cm["config_shards"]),
      "compatibility_shards_verified":len(ci["shards"]),"empirical_fit_performed":False,
      "market_data_loaded":False,"holdout_accessed":False,"source_manifest_sha256":source_hash,
      "compressed_jsonl_path":str(output),"compressed_jsonl_sha256":sha(output.read_bytes()),
      "authorization":"FAIL_CLOSED_NO_MODEL_FITTING"
    }
    summary_path=output.with_suffix(output.suffix+".summary.json")
    summary_path.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: prediction_accounting_executor_r3.py OUTPUT.jsonl.gz")
    main(sys.argv[1])
