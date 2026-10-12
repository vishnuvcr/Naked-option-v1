#!/usr/bin/env python3
"""Refresh R2 preregistration Git blob SHA-1 pins after deterministic registry rebuild."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "research" / "registry"
PREREG = REG / "PREDICTION_PREREGISTRATION_V2_R2.json"
PATHS = {
    "data_manifest_git_blob_sha1": ROOT / "research" / "data" / "DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json",
    "label_manifest_git_blob_sha1": REG / "PREDICTION_LABEL_MANIFEST_V2_R2.json",
    "config_manifest_git_blob_sha1": REG / "PREDICTION_CONFIG_MANIFEST_V2_R2.json",
    "registry_index_git_blob_sha1": REG / "PREDICTION_REGISTRY_SHARD_INDEX_V2_R2.json",
    "compatibility_matrix_git_blob_sha1": REG / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json",
}

def git_blob_sha1(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()

def main() -> int:
    obj = json.loads(PREREG.read_text(encoding="utf-8"))
    scope = obj.get("scope")
    if not isinstance(scope, dict):
        raise SystemExit("BLOCKED: preregistration scope must be an object")
    for key, path in PATHS.items():
        if not path.is_file():
            raise SystemExit(f"BLOCKED: required source pin is missing: {path}")
        scope[key] = git_blob_sha1(path.read_bytes())
    scope["preregistration_note"] = (
        "All source pins are 40-character Git blob SHA-1 object IDs, not SHA-256 file digests. "
        "Exact content digests in the run report use SHA-256. Any pinned input change requires "
        "regenerating and reviewing this preregistration before the synthetic runner proceeds; "
        "no pin authorizes empirical access."
    )
    PREREG.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"updated_pins": {key: scope[key] for key in PATHS}}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
