#!/usr/bin/env python3
"""Read-only integrity audit for the frozen Phase 8P R3 prediction registry."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("research/gates/PREDICTION_REGISTRY_ACCOUNTING_AUDIT_R3_2026-10-13.json")
def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def load(p): return json.loads((ROOT / p).read_text(encoding="utf-8"))
def fail(msg): raise ValueError(msg)

cm_path = "research/registry/PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json"
ci_path = "research/registry/PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
cm, ci = load(cm_path), load(ci_path)
configs, methods, errors = [], {}, []
for entry in cm["config_shards"]:
    raw = (ROOT / entry["path"]).read_bytes()
    if len(raw) != entry["byte_count"] or sha(raw) != entry["sha256"]:
        errors.append("config shard integrity mismatch: " + entry["path"]); continue
    shard = json.loads(raw)
    rows = shard.get("configs", [])
    if len(rows) != entry["count"]: errors.append("config shard count mismatch: " + entry["path"])
    for row in rows:
        if sha(canonical(row["configuration"])) != row["config_sha256"]:
            errors.append("config digest mismatch: " + row.get("config_id", "?"))
        if row.get("method_id") != row.get("configuration", {}).get("method_id"):
            errors.append("config method mismatch: " + row.get("config_id", "?"))
        configs.append(row)
for entry in ci["shards"]:
    raw = (ROOT / entry["path"]).read_bytes()
    if len(raw) != entry["bytes"] or sha(raw) != entry["sha256"]:
        errors.append("compatibility shard integrity mismatch: " + entry["path"]); continue
    rows = json.loads(raw).get("rows", [])
    if len(rows) != entry["record_count"]: errors.append("compatibility shard count mismatch: " + entry["path"])
    for row in rows:
        mid = row.get("method_id")
        if mid in methods: errors.append("duplicate method: " + str(mid))
        methods[mid] = row
if len(configs) != cm["configuration_count"]: errors.append("configuration total mismatch")
if len(methods) != ci["record_count"]: errors.append("method total mismatch")
if len({r.get("config_id") for r in configs}) != len(configs): errors.append("duplicate config_id")
if set(methods) != {f"PM{i:04d}" for i in range(1, 1001)}: errors.append("method ID coverage mismatch")
label_counts = {}
for row in configs:
    label = row["configuration"].get("label_id")
    label_counts[label] = label_counts.get(label, 0) + 1
if label_counts != cm["configurations_per_label"]: errors.append("label distribution mismatch")
per_method = {}
for row in configs: per_method[row["method_id"]] = per_method.get(row["method_id"], 0) + 1
if len(per_method) != 1000 or any(n != cm["configurations_per_method"] for n in per_method.values()):
    errors.append("per-method configuration count mismatch")
decisions = {}
for row in methods.values():
    d = row.get("compatibility_decision")
    decisions[d] = decisions.get(d, 0) + 1
    if row.get("eligible_for_empirical_fitting") is not False:
        errors.append("empirical eligibility flag not false: " + str(row.get("method_id")))
if decisions.get("ALLOW_IN_PRINCIPLE", 0) != ci["allow_in_principle_count"]: errors.append("allow count mismatch")
if ci["blocked_count"] != len(methods) - ci["allow_in_principle_count"]: errors.append("blocked count mismatch")
if ci["empirically_eligible_count"] != 0: errors.append("index claims empirical eligibility")
report = {
 "schema_version":"prediction-registry-accounting-audit-r3",
 "status":"PASS_INTEGRITY_AND_ACCOUNTING" if not errors else "FAIL",
 "config_manifest_path":cm_path, "config_manifest_git_blob_sha1":"258b789a746186f2b83348a715a9da0d160a1baa",
 "compatibility_index_path":ci_path, "compatibility_index_git_blob_sha1":"ebe233aca9e3d12fb3a7af1af579261d4c4e872c",
 "configuration_count":len(configs), "method_count":len(methods),
 "configurations_per_label":label_counts, "compatibility_decisions":decisions,
 "empirically_eligible_methods":sum(r.get("eligible_for_empirical_fitting") is True for r in methods.values()),
 "empirical_fit_performed":False, "market_data_loaded":False, "holdout_accessed":False,
 "errors":errors
}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
print(json.dumps(report, indent=2))
if errors: raise SystemExit(1)
