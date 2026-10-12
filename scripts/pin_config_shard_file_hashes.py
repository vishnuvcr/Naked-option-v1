#!/usr/bin/env python3
"""Pin config shard digests to exact committed bytes and document that contract."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "registry" / "PREDICTION_CONFIG_MANIFEST_V2_R2.json"

def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    shards = manifest.get("config_shards")
    if not isinstance(shards, list) or len(shards) != 4:
        raise SystemExit("BLOCKED: expected four declared config shards")
    for shard in shards:
        if not isinstance(shard, dict) or not isinstance(shard.get("path"), str):
            raise SystemExit("BLOCKED: malformed shard declaration")
        path = ROOT / shard["path"]
        if not path.is_file() or ROOT not in path.resolve().parents:
            raise SystemExit(f"BLOCKED: missing or unsafe shard path: {shard.get('path')}")
        raw = path.read_bytes()
        obj = json.loads(raw.decode("utf-8"))
        records = obj.get("configs", obj.get("configurations", obj.get("records"))) if isinstance(obj, dict) else obj
        if not isinstance(records, list) or len(records) != shard.get("count"):
            raise SystemExit(f"BLOCKED: count mismatch for {shard['path']}")
        ids = []
        for record in records:
            if not isinstance(record, dict):
                raise SystemExit(f"BLOCKED: non-object config record in {shard['path']}")
            keys = [k for k in ("config_id", "configuration_id", "id") if k in record]
            if len(keys) != 1 or not isinstance(record[keys[0]], str):
                raise SystemExit(f"BLOCKED: invalid config ID in {shard['path']}")
            ids.append(record[keys[0]])
        if len(set(ids)) != len(ids) or ids[0] != shard.get("first_id") or ids[-1] != shard.get("last_id"):
            raise SystemExit(f"BLOCKED: duplicate IDs or range mismatch in {shard['path']}")
        shard["sha256"] = hashlib.sha256(raw).hexdigest()
    manifest["config_hash_rule"] = "SHA-256 over exact committed shard file bytes (UTF-8 JSON bytes, including final newline if present)"
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"hash_rule": manifest["config_hash_rule"], "shards_updated": len(shards),
                      "digests": [{"path": s["path"], "sha256": s["sha256"]} for s in shards]}, indent=2))

if __name__ == "__main__":
    main()
