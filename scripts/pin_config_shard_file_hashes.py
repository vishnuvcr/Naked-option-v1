#!/usr/bin/env python3
"""Set documented exact-file-byte SHA-256 digests for config shards."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/registry/PREDICTION_CONFIG_MANIFEST_V2_R2.json"

def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    shards = manifest.get("config_shards")
    if not isinstance(shards, list) or len(shards) != 4:
        raise SystemExit("BLOCKED: expected exactly four config shards")
    for shard in shards:
        rel = shard.get("path")
        if not isinstance(rel, str) or rel.startswith("/") or ".." in Path(rel).parts:
            raise SystemExit(f"BLOCKED: unsafe path {rel!r}")
        path = ROOT / rel
        raw = path.read_bytes()
        obj = json.loads(raw.decode("utf-8"))
        if isinstance(obj, list):
            records = obj
        elif isinstance(obj, dict):
            matches = [k for k in ("configs", "configurations", "records") if isinstance(obj.get(k), list)]
            if len(matches) != 1:
                raise SystemExit(f"BLOCKED: expected one record array in {rel}")
            records = obj[matches[0]]
        else:
            raise SystemExit(f"BLOCKED: invalid JSON root in {rel}")
        ids = []
        for row in records:
            if not isinstance(row, dict):
                raise SystemExit(f"BLOCKED: non-object record in {rel}")
            keys = [k for k in ("config_id", "configuration_id", "id") if k in row]
            if len(keys) != 1:
                raise SystemExit(f"BLOCKED: ambiguous config ID in {rel}")
            ids.append(str(row[keys[0]]))
        if len(records) != shard.get("count") or not ids or len(ids) != len(set(ids)):
            raise SystemExit(f"BLOCKED: count/uniqueness failure in {rel}")
        if ids[0] != shard.get("first_id") or ids[-1] != shard.get("last_id"):
            raise SystemExit(f"BLOCKED: ID range mismatch in {rel}")
        shard["sha256"] = hashlib.sha256(raw).hexdigest()
    manifest["config_hash_rule"] = "SHA-256 over exact committed shard file bytes; UTF-8 JSON bytes, including any final newline"
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"updated": len(shards), "digests": [{"path": x["path"], "sha256": x["sha256"]} for x in shards]}, indent=2))

if __name__ == "__main__":
    main()
