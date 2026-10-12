#!/usr/bin/env python3
"""Fill only missing R2 method shards from the canonical master; never overwrite."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "registry"
MASTER = REGISTRY / "METHOD_REGISTRY_V2_R2.json"
OUT = REGISTRY / "method_shards"
TOTAL, SIZE = 1000, 50

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    obj = load(MASTER)
    methods = obj.get("methods") if isinstance(obj, dict) else None
    if not isinstance(methods, list) or len(methods) != TOTAL:
        raise SystemExit("BLOCKED: master must contain exactly 1000 methods")
    ids = [x.get("method_id") if isinstance(x, dict) else None for x in methods]
    if ids != [f"PM{i:04d}" for i in range(1, TOTAL + 1)]:
        raise SystemExit("BLOCKED: master IDs invalid, duplicated, or out of order")
    OUT.mkdir(parents=True, exist_ok=True)
    created = []
    for part, start in enumerate(range(0, TOTAL, SIZE), 1):
        records = methods[start:start + SIZE]
        path = OUT / f"METHODS_V2_R2_PART{part}.json"
        if path.exists():
            old = load(path)
            if old != {"schema_version":"prediction-method-shard-v2-r2","part":part,"count":len(records),"methods":records}:
                raise SystemExit(f"BLOCKED: existing shard differs from master: {path.name}")
            continue
        payload = {"schema_version":"prediction-method-shard-v2-r2","part":part,"count":len(records),"methods":records}
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        created.append(path.name)
    print(json.dumps({"master_records":len(methods),"shards_expected":TOTAL//SIZE,"created":created,"created_count":len(created)},indent=2))

if __name__ == "__main__":
    main()
