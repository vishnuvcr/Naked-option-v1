#!/usr/bin/env python3
"""Create and verify small, independently auditable JSON record shards.

Canonical shard bytes are UTF-8 JSON: sorted keys, compact separators, one
record per line, a final newline. SHA-256 in the index covers the exact bytes
written to each shard. This tool does not certify scientific compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_id(record: Any) -> str:
    if not isinstance(record, dict):
        raise ValueError("every record must be a JSON object")
    for key in ("method_id", "config_id", "id", "method_key", "configuration_id"):
        if key in record:
            return str(record[key])
    raise ValueError("record has no recognized stable ID field")


def load_records(path: Path, key: str | None) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, list):
        records = obj
    elif isinstance(obj, dict):
        if key:
            records = obj.get(key)
        else:
            candidates = [k for k, v in obj.items() if isinstance(v, list) and v
                          and all(isinstance(x, dict) for x in v)]
            if len(candidates) != 1:
                raise ValueError(f"cannot infer record list; candidates={candidates}; pass --records-key")
            records = obj[candidates[0]]
    else:
        raise ValueError("input JSON must be a list or object containing a record list")
    if not isinstance(records, list) or not all(isinstance(x, dict) for x in records):
        raise ValueError("selected record collection must be a list of JSON objects")
    ids = [record_id(x) for x in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate stable IDs in source records")
    return records


def canonical_record_line(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def build_index(source: Path, out_dir: Path, records: list[dict[str, Any]],
                kind: str, shard_size: int) -> dict[str, Any]:
    if shard_size < 1:
        raise ValueError("shard size must be positive")
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for start in range(0, len(records), shard_size):
        chunk = records[start:start + shard_size]
        payload = b"".join(canonical_record_line(r) for r in chunk)
        name = f"{kind}_{start // shard_size + 1:04d}.jsonl"
        (out_dir / name).write_bytes(payload)
        entries.append({
            "path": str((out_dir / name).as_posix()),
            "record_count": len(chunk),
            "byte_length": len(payload),
            "first_id": record_id(chunk[0]),
            "last_id": record_id(chunk[-1]),
            "sha256": sha256_bytes(payload),
        })
    index = {
        "schema_version": "auditable-record-shards-v1",
        "source_file": source.as_posix(),
        "source_sha256": sha256_bytes(source.read_bytes()),
        "record_kind": kind,
        "total_records": len(records),
        "shard_size_limit": shard_size,
        "shard_count": len(entries),
        "canonical_bytes": "UTF-8 JSONL; each record sorted-key compact JSON plus LF; SHA-256 covers exact file bytes",
        "shards": entries,
        "scientific_status": "UNREVIEWED; shard integrity does not imply scientific validity or compatibility",
    }
    index_path = out_dir / f"{kind}_INDEX.json"
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def verify_index(index_path: Path) -> list[str]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    errors = []
    total = 0
    seen_ids: set[str] = set()
    for entry in index.get("shards", []):
        path = Path(entry["path"])
        if not path.is_absolute():
            path = index_path.parent.parent / path
        if not path.exists():
            errors.append(f"missing shard: {entry['path']}")
            continue
        payload = path.read_bytes()
        if len(payload) != entry["byte_length"]:
            errors.append(f"byte length mismatch: {entry['path']}")
        if sha256_bytes(payload) != entry["sha256"]:
            errors.append(f"SHA-256 mismatch: {entry['path']}")
        lines = payload.splitlines()
        if len(lines) != entry["record_count"]:
            errors.append(f"record count mismatch: {entry['path']}")
        ids = []
        for line_no, line in enumerate(lines, 1):
            try:
                rec = json.loads(line)
                rid = record_id(rec)
                ids.append(rid)
                if rid in seen_ids:
                    errors.append(f"duplicate ID {rid} in {entry['path']}:{line_no}")
                seen_ids.add(rid)
            except Exception as exc:
                errors.append(f"invalid record {entry['path']}:{line_no}: {exc}")
        if ids and (ids[0] != entry["first_id"] or ids[-1] != entry["last_id"]):
            errors.append(f"ID range mismatch: {entry['path']}")
        total += len(lines)
    if total != index.get("total_records"):
        errors.append(f"total record mismatch: index={index.get('total_records')} actual={total}")
    return errors


def self_test() -> None:
    known = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert sha256_bytes(b"abc") == known, "SHA-256 known-vector test failed"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-index", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--records-key")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--kind", choices=("methods", "configs"), default="methods")
    parser.add_argument("--shard-size", type=int)
    args = parser.parse_args()
    self_test()
    if args.verify_index:
        errors = verify_index(args.verify_index)
        if errors:
            print("\n".join(errors))
            return 1
        print(f"PASS: verified {args.verify_index}")
        return 0
    if not all((args.input, args.out_dir, args.shard_size)):
        parser.error("provide --input, --out-dir, and --shard-size, or --verify-index")
    records = load_records(args.input, args.records_key)
    index = build_index(args.input, args.out_dir, records, args.kind, args.shard_size)
    print(json.dumps({"records": index["total_records"], "shards": index["shard_count"],
                      "index": str(args.out_dir / f"{args.kind}_INDEX.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
