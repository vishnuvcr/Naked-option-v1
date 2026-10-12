#!/usr/bin/env python3
"""Audit committed R2 registry shard counts, IDs and manifest file hashes.

This is a data-integrity audit, not scientific compatibility approval.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "registry"
CONFIG_MANIFEST = REGISTRY / "PREDICTION_CONFIG_MANIFEST_V2_R2.json"
METHOD_GLOB = "method_shards/METHODS_V2_R2_PART*.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def audit_method_shards(errors: list[str]) -> tuple[int, set[str]]:
    paths = sorted((REGISTRY / "method_shards").glob("METHODS_V2_R2_PART*.json"))
    if not paths:
        errors.append("no method shard files found")
        return 0, set()
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
    return total, all_ids


def audit_config_shards(errors: list[str]) -> tuple[int, set[str]]:
    try:
        manifest = load_json(CONFIG_MANIFEST)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load config manifest: {exc}")
        return 0, set()
    shards = manifest.get("config_shards") if isinstance(manifest, dict) else None
    if not isinstance(shards, list):
        errors.append("config manifest config_shards must be a list")
        return 0, set()
    all_ids: set[str] = set()
    total = 0
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
            actual_sha = sha256_file(path)
            if actual_sha != shard.get("sha256"):
                errors.append(f"{rel}: file SHA-256 mismatch; manifest={shard.get('sha256')} actual={actual_sha}")
            obj = load_json(path)
            records = records_from(obj, ("configs", "configurations", "records"), path)
            ids = [stable_id(record, ("config_id", "configuration_id", "id"), path) for record in records]
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
    if isinstance(manifest, dict):
        if total != manifest.get("configuration_count"):
            errors.append(f"config total mismatch; manifest={manifest.get('configuration_count')} actual={total}")
    return total, all_ids


def main() -> int:
    errors: list[str] = []
    method_count, method_ids = audit_method_shards(errors)
    config_count, config_ids = audit_config_shards(errors)
    expected_methods = 1000
    expected_configs = 8000
    if method_count != expected_methods:
        errors.append(f"method total mismatch; expected={expected_methods} actual={method_count}")
    if config_count != expected_configs:
        errors.append(f"config total mismatch; expected={expected_configs} actual={config_count}")
    print(json.dumps({
        "method_records": method_count,
        "unique_method_ids": len(method_ids),
        "config_records": config_count,
        "unique_config_ids": len(config_ids),
        "errors": errors,
        "scientific_status": "UNREVIEWED; data integrity checks do not establish compatibility or predictive validity",
    }, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
