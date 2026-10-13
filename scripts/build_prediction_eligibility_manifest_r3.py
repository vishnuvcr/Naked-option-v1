#!/usr/bin/env python3
"""Build a deterministic, fail-closed disposition for the frozen Phase 8P R3 registry.

This script performs registry accounting only. It does not load market rows, fit models,
open holdout data, or authorize empirical execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = "research/registry/PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
COMPAT_INDEX_PATH = "research/registry/PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
PREFLIGHT_PATH = "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json"
OUT_PATH = "research/gates/PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def load_verified_shards(index: dict, key: str, path_key: str, hash_key: str, count_key: str):
    rows = []
    seen = set()
    for shard in index[key]:
        raw = (ROOT / shard[path_key]).read_bytes()
        if sha256(raw) != shard[hash_key]:
            raise ValueError(f"SHARD_HASH_MISMATCH:{shard[path_key]}")
        payload = json.loads(raw.decode("utf-8"))
        records = payload.get("configs", payload.get("rows"))
        if not isinstance(records, list) or len(records) != shard[count_key]:
            raise ValueError(f"SHARD_COUNT_MISMATCH:{shard[path_key]}")
        for rec in records:
            identity = rec.get("config_id") if "config_id" in rec else rec.get("method_id")
            if not identity or identity in seen:
                raise ValueError(f"DUPLICATE_OR_MISSING_ID:{identity}")
            seen.add(identity)
            rows.append(rec)
    return rows

def classify(config: dict, method: dict, blocked_labels: set[str]) -> dict:
    c = config["configuration"]
    if method["compatibility_decision"] == "BLOCK":
        disposition = "BLOCKED_METHOD_COMPATIBILITY"
        reason = method.get("decision_code", "COMPATIBILITY_BLOCK")
    elif method.get("eligible_for_empirical_fitting") is not True:
        disposition = "BLOCKED_IMPLEMENTATION_OR_AUTHORIZATION"
        reason = method.get("implementation_status", "NOT_EXPLICITLY_EMPIRICALLY_ELIGIBLE")
    elif c.get("label_id") in blocked_labels:
        disposition = "BLOCKED_DATA_SUPPORT"
        reason = "ONE_OR_MORE_FROZEN_OUTER_FOLD_LABEL_CELLS_BLOCKED"
    else:
        # No record currently satisfies the explicit method authorization contract.
        # This branch is intentionally strict and never inferred from ALLOW_IN_PRINCIPLE.
        disposition = "ELIGIBLE_PENDING_EXECUTOR_GATE"
        reason = "METHOD_FLAG_AND_DATA_SUPPORT_PASS_BUT_EXECUTOR_AUTHORIZATION_MUST_STILL_PASS"
    return {
        "config_id": config["config_id"],
        "config_sha256": config["config_sha256"],
        "method_id": config["method_id"],
        "label_id": c["label_id"],
        "stratum": c["stratum"],
        "disposition": disposition,
        "reason_code": reason,
        "empirical_fit_authorized": False,
    }

def build_manifest(configs: list[dict], methods: list[dict], blocked_labels: set[str],
                   source_pins: dict) -> dict:
    method_map = {m["method_id"]: m for m in methods}
    if len(method_map) != len(methods):
        raise ValueError("DUPLICATE_METHOD_ID")
    out = []
    for cfg in configs:
        mid = cfg.get("method_id")
        if mid not in method_map:
            raise ValueError(f"CONFIG_METHOD_NOT_REGISTERED:{mid}")
        out.append(classify(cfg, method_map[mid], blocked_labels))
    if len({x["config_id"] for x in out}) != len(out):
        raise ValueError("DUPLICATE_CONFIG_ID")
    counts = dict(sorted(Counter(x["disposition"] for x in out).items()))
    return {
        "schema_version": "prediction-eligibility-disposition-r3-v1",
        "research_date": "2026-10-13",
        "source_pins": source_pins,
        "record_count": len(out),
        "unique_config_count": len({x["config_id"] for x in out}),
        "empirical_fit_authorized": False,
        "disposition_counts": counts,
        "blocked_fold_labels": sorted(blocked_labels),
        "records": sorted(out, key=lambda x: x["config_id"]),
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=OUT_PATH)
    args = parser.parse_args()
    index = read_json(INDEX_PATH)
    comp_index = read_json(COMPAT_INDEX_PATH)
    preflight = read_json(PREFLIGHT_PATH)
    configs = load_verified_shards(index, "config_shards", "path", "sha256", "record_count")
    methods = load_verified_shards(comp_index, "shards", "path", "sha256", "record_count")
    if len(configs) != index.get("config_count", 40000):
        raise ValueError(f"CONFIG_TOTAL_MISMATCH:{len(configs)}")
    if len(methods) != comp_index.get("record_count", 1000):
        raise ValueError(f"METHOD_TOTAL_MISMATCH:{len(methods)}")
    blocked_labels = {
        "POS_1D_UP_DOWN", "POS_2D_UP_DOWN", "POS_3D_UP_DOWN",
        "POS_5D_UP_DOWN", "POS_10D_UP_DOWN"
    }
    pins = {
        "registry_index_git_blob_sha1": index.get("git_blob_sha1", "PINNED_BY_COMMIT"),
        "registry_index_path": INDEX_PATH,
        "compatibility_index_git_blob_sha1": comp_index.get("git_blob_sha1", "PINNED_BY_COMMIT"),
        "compatibility_index_path": COMPAT_INDEX_PATH,
        "preflight_git_blob_sha1": "9da9692d67b5fda6271e021c77e429d1b9f32b3c",
        "preflight_path": PREFLIGHT_PATH,
        "config_manifest_git_blob_sha1": index["config_manifest_git_blob_sha1"],
        "config_manifest_path": index["config_manifest_path"],
    }
    manifest = build_manifest(configs, methods, blocked_labels, pins)
    if manifest["record_count"] != 40000 or manifest["unique_config_count"] != 40000:
        raise ValueError("EXPECTED_40000_UNIQUE_CONFIGURATIONS")
    if manifest["disposition_counts"].get("ELIGIBLE_PENDING_EXECUTOR_GATE", 0) != 0:
        raise ValueError("UNEXPECTED_CONFIG_ELIGIBILITY_REQUIRES_REVIEW")
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status":"PASS_REGISTRY_DISPOSITION_ONLY","output":args.output,
                      "record_count":manifest["record_count"],
                      "disposition_counts":manifest["disposition_counts"],
                      "empirical_fit_authorized":False}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
