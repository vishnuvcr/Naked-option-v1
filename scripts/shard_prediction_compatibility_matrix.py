#!/usr/bin/env python3
"""Publish small, independently inspectable compatibility-matrix shards.

The full matrix remains the execution input. These 25-row JSON shards are a
review surface so the independent tester need not rely on oversized GitHub blobs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "research" / "registry"
MATRIX = REG / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"
OUT = REG / "compatibility_shards"
INDEX = REG / "PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
SHARD_SIZE = 25


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def main() -> int:
    matrix_bytes = MATRIX.read_bytes()
    matrix = json.loads(matrix_bytes)
    rows = matrix.get("rows")
    if not isinstance(rows, list) or len(rows) != 1000:
        raise SystemExit(f"expected 1000 compatibility rows; got {len(rows) if isinstance(rows, list) else type(rows).__name__}")
    ids = [r.get("method_id") for r in rows]
    if len(set(ids)) != 1000 or any(not isinstance(x, str) or not x for x in ids):
        raise SystemExit("method IDs must be 1000 nonempty unique strings")
    OUT.mkdir(parents=True, exist_ok=True)
    expected_names = set()
    entries = []
    for offset in range(0, len(rows), SHARD_SIZE):
        part = offset // SHARD_SIZE + 1
        name = f"PREDICTION_COMPATIBILITY_PART{part:03d}.json"
        expected_names.add(name)
        subset = rows[offset:offset + SHARD_SIZE]
        payload = {
            "schema_version": "prediction-compatibility-shard-v1",
            "part": part,
            "record_count": len(subset),
            "matrix_sha256": sha256(matrix_bytes),
            "matrix_semantic_sha256": matrix["matrix_sha256"],
            "rows": subset,
        }
        raw = compact_bytes(payload)
        (OUT / name).write_bytes(raw)
        entries.append({
            "path": (OUT / name).relative_to(ROOT).as_posix(),
            "sha256": sha256(raw),
            "bytes": len(raw),
            "record_count": len(subset),
            "first_method_id": subset[0]["method_id"],
            "last_method_id": subset[-1]["method_id"],
        })
    for path in OUT.glob("PREDICTION_COMPATIBILITY_PART*.json"):
        if path.name not in expected_names:
            path.unlink()
    index = {
        "schema_version": "prediction-compatibility-shard-index-v1",
        "status": "REVIEW_AID_NOT_SCIENTIFIC_APPROVAL",
        "shard_size": SHARD_SIZE,
        "shard_count": len(entries),
        "record_count": len(rows),
        "source_matrix_path": MATRIX.relative_to(ROOT).as_posix(),
        "source_matrix_file_sha256": sha256(matrix_bytes),
        "source_matrix_semantic_sha256": matrix["matrix_sha256"],
        "allow_in_principle_count": matrix.get("compatibility_allow_in_principle_count"),
        "blocked_count": matrix.get("compatibility_block_count"),
        "empirically_eligible_count": matrix.get("empirically_eligible_count"),
        "shards": entries,
    }
    INDEX.write_bytes(compact_bytes(index))
    print(json.dumps({
        "status": "PASS_REVIEW_SHARDS_GENERATED",
        "shard_count": len(entries),
        "record_count": len(rows),
        "source_matrix_file_sha256": index["source_matrix_file_sha256"],
        "index_path": INDEX.relative_to(ROOT).as_posix(),
        "empirically_eligible_count": index["empirically_eligible_count"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
