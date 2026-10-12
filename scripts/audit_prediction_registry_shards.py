#!/usr/bin/env python3
"""Audit committed R2 registry shard counts, IDs and declared integrity hashes.

This is a data-integrity audit, not scientific compatibility approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "registry"
METHOD_MASTER = REGISTRY / "METHOD_REGISTRY_V2_R2.json"
CONFIG_MANIFEST = REGISTRY / "PREDICTION_CONFIG_MANIFEST_V2_R2.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def records_from(obj: Any, keys: tuple[str, ...], path: Path) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        records = obj
    elif isinstance(obj, dict):
        found = [key for key in keys if isinstance(obj.get(key), list)]
        if len(found) != 1:
            raise ValueError(f"{path}: expected exactly one record list from {keys}, found {found}")
        records = obj[found[0]]
    else:
        raise ValueError(f"{path}: shard root must be object or list")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError(f"{path}: every record must be an object")
    return records


def stable_id(record: dict[str, Any], candidates: tuple[str, ...], path: Path) -> str:
    keys = [key for key in candidates if key in record]
    if len(keys) != 1:
        raise ValueError(f"{path}: expected exactly one ID from {candidates}; found {keys}")
    value = record[keys[0]]
    if not isinstance(value, (str, int)) or isinstance(value, bool) or not str(value).strip():
        raise ValueError(f"{path}: invalid ID in {keys[0]}: {value!r}")
    return str(value)


def audit_method_shards(errors: list[str]) -> tuple[int, set[str], dict[str, Any]]:
    paths = sorted((REGISTRY / "method_shards").glob("METHODS_V2_R2_PART*.json"))
    all_ids: set[str] = set()
    total = 0
    for expected_part, path in enumerate(paths, 1):
        try:
            obj = load_json(path)
            records = records_from(obj, ("methods",), path)
            ids = [stable_id(record, ("method_id",), path) for record in records]
            if isinstance(obj, dict) and obj.get("part") != expected_part:
                errors.append(f"{path.relative_to(ROOT)}: part metadata {obj.get('part')} != {expected_part}")
            if isinstance(obj, dict) and obj.get("count") != len(records):
                errors.append(f"{path.relative_to(ROOT)}: declared count {obj.get('count')} != {len(records)}")
            if len(ids) != len(set(ids)):
                errors.append(f"{path.relative_to(ROOT)}: duplicate IDs within shard")
            duplicates = all_ids.intersection(ids)
            if duplicates:
                errors.append(f"{path.relative_to(ROOT)}: duplicate IDs across shards: {sorted(duplicates)[:5]}")
            all_ids.update(ids)
            total += len(records)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(str(exc))
    master_summary: dict[str, Any] = {}
    try:
        master = load_json(METHOD_MASTER)
        master_records = records_from(master, ("methods", "method_registry", "registry"), METHOD_MASTER)
        master_ids = [stable_id(record, ("method_id",), METHOD_MASTER) for record in master_records]
        master_summary = {"master_records": len(master_records), "master_unique_ids": len(set(master_ids))}
        if len(master_ids) != len(set(master_ids)):
            errors.append("master method registry contains duplicate method IDs")
        missing = sorted(set(master_ids) - all_ids)
        unexpected = sorted(all_ids - set(master_ids))
        if missing:
            errors.append(f"method shards omit {len(missing)} master IDs; first={missing[:10]}")
        if unexpected:
            errors.append(f"method shards contain {len(unexpected)} IDs absent from master; first={unexpected[:10]}")
        if len(master_records) != 1000:
            errors.append(f"master method total mismatch; expected=1000 actual={len(master_records)}")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"master registry audit error: {exc}")
    return total, all_ids, master_summary


def audit_config_shards(errors: list[str]) -> tuple[int, set[str], list[dict[str, Any]]]:
    try:
        manifest = load_json(CONFIG_MANIFEST)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load config manifest: {exc}")
        return 0, set(), []
    shards = manifest.get("config_shards") if isinstance(manifest, dict) else None
    if not isinstance(shards, list):
        errors.append("config manifest config_shards must be a list")
        return 0, set(), []
    all_ids: set[str] = set()
    total = 0
    hash_diagnostics = []
    for shard in shards:
        if not isinstance(shard, dict):
            errors.append("config manifest shard entry must be an object")
            continue
        try:
            rel = shard["path"]
            path = ROOT / rel
            if not path.is_file():
                errors.append(f"missing config shard: {rel}")
                continue
            raw = path.read_bytes()
            obj = json.loads(raw.decode("utf-8"))
            records = records_from(obj, ("configs", "configurations", "records"), path)
            ids = [stable_id(record, ("config_id", "configuration_id", "id"), path) for record in records]
            actual_raw_sha = sha256_bytes(raw)
            actual_canonical_root_sha = sha256_bytes(canonical_json(obj))
            actual_canonical_records_sha = sha256_bytes(b"".join(canonical_json(record) + b"\n" for record in records))
            expected_sha = shard.get("sha256")
            hash_match = expected_sha in (actual_raw_sha, actual_canonical_root_sha, actual_canonical_records_sha)
            hash_diagnostics.append({
                "path": rel,
                "manifest_sha256": expected_sha,
                "raw_file_sha256": actual_raw_sha,
                "canonical_root_sha256": actual_canonical_root_sha,
                "canonical_records_lf_sha256": actual_canonical_records_sha,
                "matched_known_file_encoding": hash_match,
            })
            if not hash_match:
                errors.append(f"{rel}: declared shard SHA-256 matches neither raw file nor canonical JSON/root or canonical record stream")
            if len(records) != shard.get("count"):
                errors.append(f"{rel}: record count mismatch; manifest={shard.get('count')} actual={len(records)}")
            if ids:
                if ids[0] != shard.get("first_id"):
                    errors.append(f"{rel}: first ID mismatch; manifest={shard.get('first_id')} actual={ids[0]}")
                if ids[-1] != shard.get("last_id"):
                    errors.append(f"{rel}: last ID mismatch; manifest={shard.get('last_id')} actual={ids[-1]}")
            if len(ids) != len(set(ids)):
                errors.append(f"{rel}: duplicate IDs within shard")
            duplicates = all_ids.intersection(ids)
            if duplicates:
                errors.append(f"{rel}: duplicate IDs across shards: {sorted(duplicates)[:5]}")
            all_ids.update(ids)
            total += len(records)
        except (KeyError, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"config shard audit error: {exc}")
    if isinstance(manifest, dict) and total != manifest.get("configuration_count"):
        errors.append(f"config total mismatch; manifest={manifest.get('configuration_count')} actual={total}")
    return total, all_ids, hash_diagnostics


def main() -> int:
    errors: list[str] = []
    method_count, method_ids, master_summary = audit_method_shards(errors)
    config_count, config_ids, hash_diagnostics = audit_config_shards(errors)
    if method_count != 1000:
        errors.append(f"method shard total mismatch; expected=1000 actual={method_count}")
    if config_count != 8000:
        errors.append(f"config total mismatch; expected=8000 actual={config_count}")
    print(json.dumps({
        "method_shards": {"shard_records": method_count, "unique_shard_ids": len(method_ids), **master_summary},
        "config_shards": {"records": config_count, "unique_ids": len(config_ids), "hash_diagnostics": hash_diagnostics},
        "errors": errors,
        "scientific_status": "UNREVIEWED; data integrity checks do not establish compatibility or predictive validity",
    }, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
