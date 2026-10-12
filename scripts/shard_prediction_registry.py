#!/usr/bin/env python3
"""Create and verify small, independently auditable JSON record shards.

Canonical shard bytes are UTF-8 JSON: sorted keys, compact separators, one
record per line, a final LF. SHA-256 in the index covers the exact shard bytes.
This utility checks file integrity only; it does not certify scientific validity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ID_FIELDS = ("method_id", "config_id", "id", "method_key", "configuration_id")
SCHEMA_VERSION = "auditable-record-shards-v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_id(record: Any) -> str:
    if not isinstance(record, dict):
        raise ValueError("every record must be a JSON object")
    present = [key for key in ID_FIELDS if key in record]
    if len(present) != 1:
        raise ValueError(f"record must contain exactly one recognized stable ID field; found={present}")
    value = record[present[0]]
    if not isinstance(value, (str, int)) or isinstance(value, bool) or str(value).strip() == "":
        raise ValueError(f"stable ID field {present[0]} must be a non-empty string or integer")
    return str(value)


def load_records(path: Path, key: str | None) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, list):
        if key:
            raise ValueError("--records-key is only valid when input JSON is an object")
        records = obj
    elif isinstance(obj, dict):
        if key:
            if key not in obj:
                raise ValueError(f"requested records key not found: {key}")
            records = obj[key]
        else:
            candidates = [k for k, v in obj.items()
                          if isinstance(v, list) and all(isinstance(x, dict) for x in v)]
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
    if kind not in ("methods", "configs"):
        raise ValueError("kind must be methods or configs")
    if shard_size < 1:
        raise ValueError("shard size must be positive")
    # Revalidate callers that bypass load_records().
    ids = [record_id(record) for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate stable IDs in source records")
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for start in range(0, len(records), shard_size):
        chunk = records[start:start + shard_size]
        payload = b"".join(canonical_record_line(record) for record in chunk)
        name = f"{kind}_{start // shard_size + 1:04d}.jsonl"
        (out_dir / name).write_bytes(payload)
        entries.append({
            "path": name,
            "record_count": len(chunk),
            "byte_length": len(payload),
            "first_id": record_id(chunk[0]),
            "last_id": record_id(chunk[-1]),
            "sha256": sha256_bytes(payload),
        })
    index = {
        "schema_version": SCHEMA_VERSION,
        # Basename avoids embedding machine-specific absolute paths.
        "source_file": source.name,
        "source_sha256": sha256_bytes(source.read_bytes()),
        "record_kind": kind,
        "total_records": len(records),
        "shard_size_limit": shard_size,
        "shard_count": len(entries),
        "canonical_bytes": "UTF-8 JSONL; sorted-key compact JSON plus one LF per record; SHA-256 covers exact file bytes",
        "shards": entries,
        "scientific_status": "UNREVIEWED; shard integrity does not imply scientific validity or compatibility",
    }
    (out_dir / f"{kind}_INDEX.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def verify_index(index_path: Path) -> list[str]:
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"invalid index JSON/read: {exc}"]
    errors: list[str] = []
    if not isinstance(index, dict):
        return ["index root must be a JSON object"]
    required = ("schema_version", "total_records", "shard_count", "shards")
    missing = [key for key in required if key not in index]
    if missing:
        return [f"index missing required keys: {missing}"]
    if index["schema_version"] != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version: {index['schema_version']!r}")
    if not isinstance(index["shards"], list):
        return errors + ["index shards must be a list"]
    if not isinstance(index["total_records"], int) or index["total_records"] < 0:
        errors.append("total_records must be a non-negative integer")
    if not isinstance(index["shard_count"], int) or index["shard_count"] < 0:
        errors.append("shard_count must be a non-negative integer")
    if len(index["shards"]) != index["shard_count"]:
        errors.append(f"shard_count mismatch: index={index['shard_count']} actual={len(index['shards'])}")
    total = 0
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for n, entry in enumerate(index["shards"], 1):
        if not isinstance(entry, dict):
            errors.append(f"shard entry {n} must be an object")
            continue
        needed = ("path", "record_count", "byte_length", "first_id", "last_id", "sha256")
        absent = [key for key in needed if key not in entry]
        if absent:
            errors.append(f"shard entry {n} missing keys: {absent}")
            continue
        rel = entry["path"]
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or len(Path(rel).parts) != 1 or rel in (".", ".."):
            errors.append(f"unsafe shard path in entry {n}: {rel!r}")
            continue
        if rel in seen_paths:
            errors.append(f"duplicate shard path: {rel}")
            continue
        seen_paths.add(rel)
        path = index_path.parent / rel
        if not path.is_file():
            errors.append(f"missing shard: {rel}")
            continue
        payload = path.read_bytes()
        if not isinstance(entry["byte_length"], int) or len(payload) != entry["byte_length"]:
            errors.append(f"byte length mismatch: {rel}")
        if sha256_bytes(payload) != entry["sha256"]:
            errors.append(f"SHA-256 mismatch: {rel}")
        if payload and not payload.endswith(b"\n"):
            errors.append(f"missing final LF: {rel}")
        if b"\r" in payload:
            errors.append(f"non-canonical CR byte: {rel}")
        lines = payload.splitlines()
        if len(lines) != entry["record_count"]:
            errors.append(f"record count mismatch: {rel}")
        ids = []
        for line_no, line in enumerate(lines, 1):
            try:
                rec = json.loads(line)
                rid = record_id(rec)
                if canonical_record_line(rec).rstrip(b"\n") != line:
                    errors.append(f"non-canonical JSON record: {rel}:{line_no}")
                ids.append(rid)
                if rid in seen_ids:
                    errors.append(f"duplicate ID {rid} in {rel}:{line_no}")
                seen_ids.add(rid)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                errors.append(f"invalid record {rel}:{line_no}: {exc}")
        if ids and (ids[0] != entry["first_id"] or ids[-1] != entry["last_id"]):
            errors.append(f"ID range mismatch: {rel}")
        if not ids and entry["record_count"] != 0:
            errors.append(f"empty shard unexpectedly declares records: {rel}")
        total += len(lines)
    if total != index["total_records"]:
        errors.append(f"total record mismatch: index={index['total_records']} actual={total}")
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
    if args.input is None or args.out_dir is None or args.shard_size is None:
        parser.error("provide --input, --out-dir, and --shard-size, or --verify-index")
    records = load_records(args.input, args.records_key)
    index = build_index(args.input, args.out_dir, records, args.kind, args.shard_size)
    print(json.dumps({"records": index["total_records"], "shards": index["shard_count"],
                      "index": str(args.out_dir / f"{args.kind}_INDEX.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
