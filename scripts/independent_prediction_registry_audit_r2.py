#!/usr/bin/env python3
"""Independent, read-only Phase 8P registry and statistical-gate audit.

This checker is maintained on the isolated tester branch. It reads the developer
branch checkout but never decrypts or opens market data, fits a model, or accesses a holdout.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
from collections import Counter

SEMANTIC_FIELDS = (
    "algorithm_family", "architecture_or_decision_function", "learning_objective",
    "input_representation", "feature_construction", "inference_operator",
    "inference_definition", "target_family", "probability_adapter",
    "survival_mapping", "causal_information_policy",
)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def digest_obj(value):
    return digest_bytes(canonical(value))

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def audit_shards(root, entries, records_key, id_key, issues, label):
    records, seen = [], set()
    shard_summaries = []
    for entry in entries:
        path = root / entry["path"]
        if not path.is_file():
            issues.append({"code": f"{label}_SHARD_MISSING", "path": entry["path"]})
            continue
        raw = path.read_bytes()
        byte_expected = entry.get("bytes", entry.get("byte_count"))
        hash_expected = entry.get("sha256")
        if byte_expected is not None and len(raw) != byte_expected:
            issues.append({"code": f"{label}_BYTE_COUNT", "path": entry["path"], "expected": byte_expected, "actual": len(raw)})
        if hash_expected and digest_bytes(raw) != hash_expected:
            issues.append({"code": f"{label}_SHA256", "path": entry["path"], "expected": hash_expected, "actual": digest_bytes(raw)})
        try:
            obj = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            issues.append({"code": f"{label}_JSON_INVALID", "path": entry["path"], "error": str(exc)})
            continue
        chunk = obj.get(records_key)
        if not isinstance(chunk, list):
            issues.append({"code": f"{label}_RECORD_ARRAY", "path": entry["path"], "expected_key": records_key})
            continue
        count_expected = entry.get("record_count", entry.get("count"))
        if count_expected is not None and len(chunk) != count_expected:
            issues.append({"code": f"{label}_COUNT", "path": entry["path"], "expected": count_expected, "actual": len(chunk)})
        first_expected = entry.get("first_method_id", entry.get("first_id"))
        last_expected = entry.get("last_method_id", entry.get("last_id"))
        if chunk and first_expected is not None and chunk[0].get(id_key) != first_expected:
            issues.append({"code": f"{label}_FIRST_ID", "path": entry["path"], "expected": first_expected, "actual": chunk[0].get(id_key)})
        if chunk and last_expected is not None and chunk[-1].get(id_key) != last_expected:
            issues.append({"code": f"{label}_LAST_ID", "path": entry["path"], "expected": last_expected, "actual": chunk[-1].get(id_key)})
        for rec in chunk:
            rid = rec.get(id_key)
            if not isinstance(rid, str) or rid in seen:
                issues.append({"code": f"{label}_DUPLICATE_OR_INVALID_ID", "path": entry["path"], "id": rid})
            seen.add(rid)
            records.append(rec)
        shard_summaries.append({"path": entry["path"], "records": len(chunk), "bytes": len(raw), "sha256": digest_bytes(raw), "matrix_sha256": obj.get("matrix_sha256")})
    return records, shard_summaries

def nearest_peer(method, methods):
    def distance(other):
        return sum(method.get(k) != other.get(k) for k in SEMANTIC_FIELDS)
    candidates = [m for m in methods if m["method_id"] != method["method_id"]]
    return min(candidates, key=lambda other: (distance(other), other["method_id"]))

def expected_contrast(a, b):
    fields = [k for k in SEMANTIC_FIELDS if a.get(k) != b.get(k)]
    details = "; ".join(f"{k}: {a.get(k)!r} vs {b.get(k)!r}" for k in fields)
    return b["method_id"], f"Nearest registered method {b['method_id']} differs in {', '.join(fields)} ({details})."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--developer-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    root, issues, warnings = args.developer_root.resolve(), [], []
    reg = root / "research" / "registry"

    compat_index = read_json(reg / "PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json")
    compat_shards, compat_meta = audit_shards(root, compat_index["shards"], "rows", "method_id", issues, "COMPATIBILITY")
    compat_master = read_json(reg / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json")
    if compat_master.get("rows") != compat_shards:
        issues.append({"code": "COMPATIBILITY_MASTER_RECONSTRUCTION_MISMATCH"})
    if len(compat_shards) != 1000 or len({r.get("method_id") for r in compat_shards}) != 1000:
        issues.append({"code": "COMPATIBILITY_NOT_1000_UNIQUE_ROWS", "rows": len(compat_shards), "unique_ids": len({r.get("method_id") for r in compat_shards})})
    if compat_master.get("method_count") != 1000 or compat_master.get("empirically_eligible_count") != 0:
        issues.append({"code": "COMPATIBILITY_MASTER_COUNTS_OR_GUARD", "method_count": compat_master.get("method_count"), "eligible": compat_master.get("empirically_eligible_count")})
    if any(r.get("eligible_for_empirical_fitting") is not False for r in compat_shards):
        issues.append({"code": "EMPIRICAL_ELIGIBILITY_NOT_FALSE_FOR_ALL_ROWS"})
    if any(x.get("matrix_sha256") != compat_master.get("matrix_sha256") for x in compat_meta):
        issues.append({"code": "SHARD_MASTER_DIGEST_LINKAGE"})
    decision_counts = dict(sorted(Counter(r.get("compatibility_decision") for r in compat_shards).items()))
    sem_fps = [r.get("semantic_fingerprint_sha256") for r in compat_shards]
    if len(set(sem_fps)) != len(sem_fps):
        issues.append({"code": "DUPLICATE_COMPATIBILITY_SEMANTIC_FINGERPRINT"})

    registry_index = read_json(reg / "PREDICTION_REGISTRY_SHARD_INDEX_V2_R2.json")
    methods, method_meta = audit_shards(root, registry_index["method_shards"], "methods", "method_id", issues, "METHOD")
    configs, config_meta = audit_shards(root, registry_index["config_shards"], "configs", "config_id", issues, "CONFIG")
    method_master = read_json(reg / "METHOD_REGISTRY_V2_R2.json")
    master_methods = method_master.get("methods", method_master.get("method_registry", method_master.get("registry")))
    if master_methods != methods:
        issues.append({"code": "METHOD_MASTER_RECONSTRUCTION_MISMATCH"})
    if len(methods) != 1000 or len({m.get("method_id") for m in methods}) != 1000:
        issues.append({"code": "METHOD_COUNT_OR_UNIQUENESS", "records": len(methods), "unique": len({m.get("method_id") for m in methods})})
    if len(configs) != 8000 or len({c.get("config_id") for c in configs}) != 8000:
        issues.append({"code": "CONFIG_COUNT_OR_UNIQUENESS", "records": len(configs), "unique": len({c.get("config_id") for c in configs})})

    method_by_id = {m["method_id"]: m for m in methods if isinstance(m.get("method_id"), str)}
    compat_by_id = {r["method_id"]: r for r in compat_shards if isinstance(r.get("method_id"), str)}
    for method in methods:
        sem = {k: method.get(k) for k in SEMANTIC_FIELDS}
        fp = digest_obj(sem)
        row = compat_by_id.get(method.get("method_id"))
        if row is None:
            issues.append({"code": "METHOD_MISSING_FROM_COMPATIBILITY", "method_id": method.get("method_id")})
        elif row.get("semantic_fingerprint_sha256") != fp:
            issues.append({"code": "SEMANTIC_FINGERPRINT_MISMATCH", "method_id": method.get("method_id")})
        peer = nearest_peer(method, methods)
        peer_id, contrast = expected_contrast(method, peer)
        if method.get("nearest_neighbor_method_id") != peer_id or method.get("nearest_neighbor_contrast") != contrast:
            issues.append({"code": "NEAREST_PEER_CONTRAST_MISMATCH", "method_id": method.get("method_id"), "expected_peer": peer_id})
    method_ids = set(method_by_id)
    for c in configs:
        conf = c.get("configuration")
        if not isinstance(conf, dict):
            issues.append({"code": "CONFIGURATION_OBJECT_MISSING", "config_id": c.get("config_id")})
            continue
        if c.get("method_id") not in method_ids or conf.get("method_id") != c.get("method_id"):
            issues.append({"code": "CONFIG_METHOD_LINK_MISMATCH", "config_id": c.get("config_id"), "method_id": c.get("method_id")})
        if digest_obj(conf) != c.get("config_sha256"):
            issues.append({"code": "CONFIG_CANONICAL_HASH_MISMATCH", "config_id": c.get("config_id")})

    label_manifest = read_json(reg / "PREDICTION_LABEL_MANIFEST_V2_R2.json")
    label_ids = {x.get("id") for x in label_manifest.get("labels", [])}
    full_horizon_target_coverage = {"INTRA_5M_UP_DOWN","INTRA_15M_UP_DOWN","INTRA_30M_UP_DOWN","INTRA_60M_UP_DOWN","INTRA_120M_UP_DOWN","POS_1D_UP_DOWN","POS_2D_UP_DOWN","POS_3D_UP_DOWN","POS_5D_UP_DOWN","POS_10D_UP_DOWN"}
    missing_horizons = sorted(full_horizon_target_coverage - label_ids)
    if missing_horizons:
        warnings.append({"code":"PREDICTION_HORIZON_SCOPE_GAP","present_labels":sorted(label_ids),"missing_labels":missing_horizons,"basis":"earlier frozen research scope records intraday 5/15/30/60/120-minute and positional +1/+2/+3/+5/+10-session horizons"})

    # Explicitly probe the preregistered bootstrap utility with an uninformative
    # sample: a five-session fold resampled in five-session blocks has one support point.
    stats_path = root / "scripts" / "prediction_statistics.py"
    spec = importlib.util.spec_from_file_location("developer_prediction_statistics", stats_path)
    stats = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stats)
    degenerate = stats.paired_moving_block_bootstrap([[0.1] * 5], block_length=5, replicates=1000, seed=2026101209)
    p_key = "raw_two_sided_p_value_centered_bootstrap"
    degenerate_problem = degenerate.get("ci_low") == degenerate.get("ci_high") and degenerate.get(p_key, 1.0) < 0.05
    if degenerate_problem:
        warnings.append({"code":"BOOTSTRAP_DEGENERACY_FALSE_CERTAINTY","observed_improvement":degenerate.get("observed_mean_improvement"),"ci":[degenerate.get("ci_low"),degenerate.get("ci_high")],"p_value":degenerate.get(p_key),"fold_session_counts":degenerate.get("fold_session_counts"),"block_length":degenerate.get("block_length_exchange_sessions"),"detail":"A single admissible block makes every resample identical; p-value reaches the minimum and CI has zero width, so inferential output is non-identifiable and must fail closed."})

    result = {
        "schema_version":1,
        "audit":"phase-08p-independent-read-only-prediction-registry-audit",
        "developer_branch":"phase-08-prediction-developer",
        "compatibility_rows":len(compat_shards),
        "compatibility_shards_checked":len(compat_meta),
        "compatibility_decision_counts":decision_counts,
        "method_rows":len(methods),
        "method_shards_checked":len(method_meta),
        "configuration_rows":len(configs),
        "configuration_shards_checked":len(config_meta),
        "semantic_fingerprint_count":len(set(sem_fps)),
        "all_methods_link_to_matrix":not any(x.get("code") in {"METHOD_MISSING_FROM_COMPATIBILITY","SEMANTIC_FINGERPRINT_MISMATCH"} for x in issues),
        "all_hashes_bytecounts_rows_ids_pass":not any(any(k in x.get("code","") for k in ("SHA256","BYTE_COUNT","COUNT","FIRST_ID","LAST_ID","JSON_INVALID","SHARD_MISSING","DUPLICATE_OR_INVALID_ID")) for x in issues),
        "issues":issues,
        "warnings":warnings,
        "market_data_opened":False,
        "model_fitting_performed":False,
        "holdout_accessed":False,
        "decision":"REQUEST_CHANGES" if issues or warnings else "PASS",
    }
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"issues"}},sort_keys=True,indent=2))
    if issues:
        print("ISSUES:", json.dumps(issues[:30],sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
