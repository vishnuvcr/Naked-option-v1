#!/usr/bin/env python3
"""Validate the frozen family implementation inventory against all compatibility shards."""
import hashlib, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
idx=load("research/registry/PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json")
plan=load("research/registry/PREDICTION_METHOD_FAMILY_IMPLEMENTATION_PLAN_R3_2026-10-13.json")
counts=Counter(); decisions=Counter(); method_ids=set(); errors=[]
for shard in idx["shards"]:
    raw=(ROOT/shard["path"]).read_bytes()
    if len(raw)!=shard["bytes"] or sha(raw)!=shard["sha256"]:
        errors.append("SHARD_HASH_OR_BYTES_MISMATCH:"+shard["path"]); continue
    rows=json.loads(raw).get("rows",[])
    if len(rows)!=shard["record_count"]: errors.append("SHARD_COUNT_MISMATCH:"+shard["path"])
    for row in rows:
        mid=row.get("method_id")
        if mid in method_ids: errors.append("DUPLICATE_METHOD:"+str(mid))
        method_ids.add(mid)
        fam=row.get("algorithm_family"); decision=row.get("compatibility_decision")
        counts[(fam,decision)]+=1; decisions[decision]+=1
planned={r["family"]:r for r in plan["families"]}
actual_families={fam for fam,_ in counts}
if len(method_ids)!=1000: errors.append("METHOD_COUNT_MISMATCH:"+str(len(method_ids)))
if actual_families!=set(planned): errors.append("FAMILY_SET_MISMATCH")
for fam,row in planned.items():
    actual_total=sum(counts[(fam,d)] for d in ("ALLOW_IN_PRINCIPLE","BLOCK"))
    if actual_total!=row["methods"]: errors.append("FAMILY_TOTAL_MISMATCH:"+fam)
    if counts[(fam,"ALLOW_IN_PRINCIPLE")]!=row["allow_in_principle"]: errors.append("FAMILY_ALLOW_COUNT_MISMATCH:"+fam)
    if counts[(fam,"BLOCK")]!=row["blocked"]: errors.append("FAMILY_BLOCK_COUNT_MISMATCH:"+fam)
    if row["synthetic_gate"]=="PASS" and not row.get("adapter"): errors.append("PASS_WITHOUT_ADAPTER:"+fam)
    if row["empirical_status"]!="NOT_AUTHORIZED" and row["family"]=="logistic_regression": errors.append("LOGISTIC_EMPIRICAL_STATUS_CHANGED")
if decisions["ALLOW_IN_PRINCIPLE"]!=426 or decisions["BLOCK"]!=574: errors.append("GLOBAL_DECISION_COUNTS_MISMATCH")
if plan.get("empirical_fitting_authorized") is not False: errors.append("EMPIRICAL_FITTING_FLAG_NOT_FALSE")
report={
 "schema_version":"prediction-method-family-plan-validation-r3",
 "status":"PASS_FAMILY_PLAN_ACCOUNTING" if not errors else "FAIL",
 "method_count":len(method_ids),"family_count":len(actual_families),
 "allow_in_principle":decisions["ALLOW_IN_PRINCIPLE"],"blocked":decisions["BLOCK"],
 "empirically_eligible":0,"empirical_fitting_authorized":False,
 "family_counts":{fam:{"methods":sum(counts[(fam,d)] for d in ("ALLOW_IN_PRINCIPLE","BLOCK")),"allow_in_principle":counts[(fam,"ALLOW_IN_PRINCIPLE")],"blocked":counts[(fam,"BLOCK")]} for fam in sorted(actual_families)},
 "errors":errors
}
print(json.dumps(report,indent=2,sort_keys=True))
if errors: raise SystemExit(1)
