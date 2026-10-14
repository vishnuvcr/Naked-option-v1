#!/usr/bin/env python3
"""Create an isolated PM0051 eligibility variant without changing the frozen registry.

Only the registered probit probability-threshold method PM0051 can move from
implementation-blocked to pending-executor in this variant. No fitting or holdout
access occurs. The original 40,000-row manifest remains unchanged.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE="research/gates/PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json"
OUT="research/gates/PREDICTION_PM0051_ELIGIBILITY_DISPOSITION_R3_2026-10-14.json"
CONFIG_INDEX="research/registry/PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
COMPAT_INDEX="research/registry/PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
IMPLEMENTATION_GATE="research/gates/PREDICTION_PM0051_IMPLEMENTATION_GATE_R3_2026-10-14.json"
EXPECTED_DATA="cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"

def sha256(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()
def blob_sha1(raw:bytes)->str: return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def obj(path:str): return json.loads((ROOT/path).read_text(encoding="utf-8"))

def verified_records(index_path:str, shard_key:str, rows_key_options:tuple[str,...], count_keys:tuple[str,...]):
    index=obj(index_path); rows=[]; seen=set()
    entries=index.get(shard_key)
    if not isinstance(entries,list): raise ValueError(f"SHARD_INDEX_MISSING:{index_path}:{shard_key}")
    for item in entries:
        path=item.get("path")
        if not isinstance(path,str): raise ValueError("SHARD_PATH_INVALID")
        raw=(ROOT/path).read_bytes()
        expected=item.get("sha256")
        if expected and sha256(raw)!=expected: raise ValueError(f"SHARD_HASH_MISMATCH:{path}")
        data=json.loads(raw.decode("utf-8"))
        part=None
        for key in rows_key_options:
            if isinstance(data.get(key),list): part=data[key]; break
        if part is None: raise ValueError(f"SHARD_ROWS_MISSING:{path}")
        want=next((item[k] for k in count_keys if k in item),None)
        if want is not None and len(part)!=want: raise ValueError(f"SHARD_COUNT_MISMATCH:{path}")
        for row in part:
            identity=row.get("config_id") or row.get("method_id")
            if not identity or identity in seen: raise ValueError(f"DUPLICATE_OR_EMPTY_ID:{identity}")
            seen.add(identity); rows.append(row)
    return index, rows

def build(output:str=OUT)->dict:
    base=obj(BASE)
    if base.get("record_count")!=40000 or base.get("unique_config_count")!=40000 or len(base.get("records",[]))!=40000:
        raise ValueError("BASE_ELIGIBILITY_MANIFEST_INVALID")
    if base.get("empirical_fit_authorized") is not False or base.get("manual_authorization_required") is not False:
        raise ValueError("BASE_ELIGIBILITY_FLAGS_INVALID")
    source_pins=base.get("source_pins",{})
    if source_pins.get("canonical_uncompressed_csv_sha256")!=EXPECTED_DATA:
        raise ValueError("BASE_ELIGIBILITY_DATA_PIN_MISMATCH")
    gate_path=ROOT/IMPLEMENTATION_GATE
    if not gate_path.is_file(): raise ValueError("PM0051_IMPLEMENTATION_GATE_MISSING")
    gate=obj(IMPLEMENTATION_GATE)
    if gate.get("method_id")!="PM0051" or gate.get("status")!="PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY":
        raise ValueError("PM0051_IMPLEMENTATION_GATE_NOT_PASS")
    verify=gate.get("verification",{})
    if verify.get("conclusion")!="success" or verify.get("source_data_loaded") is not False:
        raise ValueError("PM0051_SYNTHETIC_WORKFLOW_SCOPE_INVALID")
    if verify.get("empirical_model_fit") is not False or verify.get("holdout_accessed") is not False:
        raise ValueError("PM0051_SYNTHETIC_GATE_SCOPE_INVALID")
    if gate.get("empirical_fit_authorized") is not False or gate.get("manual_authorization_required") is not False:
        raise ValueError("PM0051_IMPLEMENTATION_GATE_FLAGS_INVALID")
    for path,expected in gate.get("source_blob_pins",{}).items():
        file=ROOT/path
        if not file.is_file() or blob_sha1(file.read_bytes())!=expected:
            raise ValueError(f"PM0051_SOURCE_PIN_MISMATCH:{path}")

    compat_index, methods=verified_records(COMPAT_INDEX,"shards",("rows",),("record_count",))
    comp=[m for m in methods if m.get("method_id")=="PM0051"]
    if len(comp)!=1: raise ValueError("PM0051_COMPATIBILITY_RECORD_NOT_UNIQUE")
    method=comp[0]
    required={
       "algorithm_family":"probit_regression",
       "compatibility_decision":"ALLOW_IN_PRINCIPLE",
       "inference_operator":"probability_threshold",
       "inference_definition":"calibrated_probability_with_frozen_0_5_threshold",
       "target_family":"directional_probability",
       "learning_objective":"bernoulli_probit_nll",
    }
    for key,value in required.items():
        if method.get(key)!=value: raise ValueError(f"PM0051_COMPATIBILITY_CONTRACT_MISMATCH:{key}")
    if method.get("eligible_for_empirical_fitting") is not False:
        raise ValueError("PM0051_BASE_REGISTRY_AUTHORIZATION_FLAG_CHANGED")

    config_index, configs=verified_records(CONFIG_INDEX,"config_shards",("configs",),("record_count","count"))
    selected=[c for c in configs if c.get("method_id")=="PM0051"]
    if len(selected)!=40 or len({c.get("config_id") for c in selected})!=40:
        raise ValueError(f"PM0051_CONFIG_COUNT_INVALID:{len(selected)}")
    config_map={c["config_id"]:c for c in selected}
    for row in selected:
        spec=row["configuration"]; p=spec.get("model_parameters",{})
        if set(p)!={"prior_scale"} or p.get("prior_scale") not in {0.5,2,0.5,2.0}:
            raise ValueError(f"PM0051_PARAMETER_SCHEMA_INVALID:{row['config_id']}")
        expected_scale=2.0 if spec.get("complexity_preset")=="flexible" else 0.5 if spec.get("complexity_preset")=="regularized" else None
        if expected_scale is None or float(p["prior_scale"])!=expected_scale:
            raise ValueError(f"PM0051_COMPLEXITY_MAPPING_INVALID:{row['config_id']}")
        if spec.get("normalization")!="fit_on_training_fold_only":
            raise ValueError(f"PM0051_TRAIN_ONLY_NORMALIZATION_INVALID:{row['config_id']}")
        if spec.get("probability_calibration")!="inner_chronological_training_fold_only":
            raise ValueError(f"PM0051_CALIBRATION_PROTOCOL_INVALID:{row['config_id']}")
        label_id=str(spec.get("label_id",""))
        if label_id.startswith("POS_"):
            pieces=label_id.split("_")
            if len(pieces)<2 or not pieces[1].endswith("D") or not pieces[1][:-1].isdigit():
                raise ValueError(f"PM0051_HORIZON_LABEL_INVALID:{row['config_id']}")
            expected_purge=int(pieces[1][:-1])
        else:
            expected_purge=1
        if (spec.get("purge_exchange_sessions")!=expected_purge or
                spec.get("embargo_exchange_sessions")!=expected_purge):
            raise ValueError(f"PM0051_PURGE_OR_EMBARGO_INVALID:{row['config_id']}")
        if spec.get("refit_cadence")!="every_20_trading_sessions" or spec.get("score_only_matured_targets") is not True:
            raise ValueError(f"PM0051_MATURITY_OR_REFIT_CONTRACT_INVALID:{row['config_id']}")

    records=base["records"]
    byid={r.get("config_id"):r for r in records}
    if len(byid)!=40000 or set(config_map).intersection(byid.keys())!=set(config_map):
        raise ValueError("CONFIGURATION_MANIFEST_COVERAGE_INVALID")
    pm0001=[r for r in records if r.get("method_id")=="PM0001" and r.get("disposition")=="ELIGIBLE_PENDING_EXECUTOR_GATE"]
    if len(pm0001)!=40: raise ValueError(f"PM0001_BASELINE_PENDING_COUNT_INVALID:{len(pm0001)}")
    pm0051_base=[byid[cid] for cid in config_map]
    if any(r.get("disposition")!="BLOCKED_IMPLEMENTATION_NOT_READY" for r in pm0051_base):
        raise ValueError("PM0051_BASELINE_DISPOSITION_UNEXPECTED")
    for r in pm0001:
        r["disposition"]="BLOCKED_IMPLEMENTATION_NOT_READY"
        r["reason_code"]="METHOD_NOT_SELECTED_IN_PM0051_SCOPED_EXECUTION"
        r["implementation_gate_status"]="NOT_DEMONSTRATED"
        r["empirical_fit_authorized"]=False
        r["manual_authorization_required"]=False
    for r in pm0051_base:
        r["disposition"]="ELIGIBLE_PENDING_EXECUTOR_GATE"
        r["reason_code"]="PM0051_COMPATIBILITY_AND_SYNTHETIC_IMPLEMENTATION_PASS_EXECUTOR_GATE_REQUIRED"
        r["implementation_gate_status"]="DEVELOPER_TESTED_SYNTHETIC_ONLY"
        r["empirical_fit_authorized"]=False
        r["manual_authorization_required"]=False
        r["active_method_id"]="PM0051"
        r["config_sha256"]=config_map[r["config_id"]].get("config_sha256")
    counts=dict(sorted(Counter(r["disposition"] for r in records).items()))
    pending=[r for r in records if r.get("disposition")=="ELIGIBLE_PENDING_EXECUTOR_GATE"]
    if len(pending)!=40 or any(r.get("method_id")!="PM0051" for r in pending):
        raise ValueError("PM0051_PENDING_SET_NOT_EXACT")
    if any(r.get("empirical_fit_authorized") is not False for r in pending):
        raise ValueError("ELIGIBILITY_BUILDER_MUST_NOT_AUTHORIZE_FITTING")
    base["schema_version"]="prediction-eligibility-disposition-r3-pm0051-v1"
    base["research_date"]="2026-10-14"
    base["active_method_id"]="PM0051"
    base["record_count"]=40000; base["unique_config_count"]=40000
    base["disposition_counts"]=counts
    base["empirical_fit_authorized"]=False; base["manual_authorization_required"]=False
    base["implementation_gate_path"]=IMPLEMENTATION_GATE
    base["implementation_gate_status"]=gate["status"]
    source_pins["implementation_gate_git_blob_sha1"]=blob_sha1(gate_path.read_bytes())
    source_pins["implementation_gate_path"]=IMPLEMENTATION_GATE
    source_pins["probit_adapter_git_blob_sha1"]=blob_sha1((ROOT/"scripts/prediction_probit_adapter_r3.py").read_bytes())
    source_pins["probit_executor_git_blob_sha1"]=blob_sha1((ROOT/"scripts/prediction_probit_executor_r3.py").read_bytes())
    source_pins["probit_executor_test_git_blob_sha1"]=blob_sha1((ROOT/"scripts/test_prediction_probit_executor_r3.py").read_bytes())
    source_pins["parameter_binding_git_blob_sha1"]=blob_sha1((ROOT/"scripts/prediction_parameter_binding_r3.py").read_bytes())
    source_pins["parameter_binding_test_git_blob_sha1"]=blob_sha1((ROOT/"scripts/test_prediction_parameter_binding_r3.py").read_bytes())
    source_pins["eligibility_builder_git_blob_sha1"]=blob_sha1(Path(__file__).read_bytes())
    source_pins["compatibility_method_semantic_sha256"]=method.get("semantic_fingerprint_sha256")
    source_pins["base_eligibility_blob_sha1"]=blob_sha1((ROOT/BASE).read_bytes())
    base["source_pins"]=source_pins
    # A method-scoped eligibility variant preserves all 40,000 registry outcomes.
    base["records"]=sorted(records,key=lambda r:r["config_id"])
    base["pending_method_config_count"]=len(pending)
    base["configuration_subset"]={cid:{"configuration_sha256":config_map[cid]["config_sha256"],"prior_scale":config_map[cid]["configuration"]["model_parameters"]["prior_scale"]} for cid in sorted(config_map)}
    output_path=ROOT/output
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(base,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    return {"status":"PASS_PM0051_ELIGIBILITY_DISPOSITION_ONLY","record_count":40000,"pending_method_config_count":40,
            "method_id":"PM0051","compatibility":"ALLOW_IN_PRINCIPLE","empirical_fit_authorized":False,
            "holdout_accessed":False,"output":output,"disposition_counts":counts}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default=OUT)
    args=ap.parse_args()
    report=build(args.output); print(json.dumps(report,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
