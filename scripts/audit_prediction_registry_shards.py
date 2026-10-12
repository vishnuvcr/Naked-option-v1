#!/usr/bin/env python3
"""Strict integrity audit for R2 registries and their small-shard index.

This verifies committed bytes, record identity and master equality. It is not a scientific validity approval.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "registry"
METHOD_MASTER = REGISTRY / "METHOD_REGISTRY_V2_R2.json"
CONFIG_MANIFEST = REGISTRY / "PREDICTION_CONFIG_MANIFEST_V2_R2.json"
INDEX_PATH = REGISTRY / "PREDICTION_REGISTRY_SHARD_INDEX_V2_R2.json"
METHOD_PATTERN = re.compile(r"^METHODS_V2_R2_PART(\d{3})\.json$")
CONFIG_PATTERN = re.compile(r"^PREDICTION_CONFIGS_V2_R2_PART(\d{3})\.json$")
CONFIG_HASH_RULE = "SHA-256 over exact committed shard file bytes; UTF-8 JSON bytes, including any final newline"
METHOD_SIZE = 25
CONFIG_SIZE = 100


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def list_shards(directory: Path, pattern: re.Pattern[str], errors: list[str]) -> list[tuple[int, Path]]:
    found: list[tuple[int, Path]] = []
    for path in directory.glob("*.json"):
        match = pattern.fullmatch(path.name)
        if match:
            found.append((int(match.group(1)), path))
        elif path.name.startswith("METHODS_V2_R2_PART") or path.name.startswith("PREDICTION_CONFIGS_V2_R2_PART"):
            errors.append(f"{path.relative_to(ROOT)}: ambiguous shard filename")
    found.sort(key=lambda item: item[0])
    parts = [part for part, _ in found]
    expected = list(range(1, len(found) + 1))
    if parts != expected:
        errors.append(f"{directory.relative_to(ROOT)}: shard parts must be contiguous and start at 1; found {parts[:5]}...{parts[-5:]}")
    return found


def make_index_entry(part: int, path: Path, records: list[dict[str, Any]], id_keys: tuple[str, ...], raw: bytes) -> dict[str, Any]:
    ids = [stable_id(record, id_keys, path) for record in records]
    return {
        "part": part,
        "path": path.relative_to(ROOT).as_posix(),
        "byte_count": len(raw),
        "record_count": len(records),
        "first_id": ids[0] if ids else None,
        "last_id": ids[-1] if ids else None,
        "sha256": sha256_bytes(raw),
    }


def audit_method_shards(errors: list[str]) -> tuple[int, set[str], dict[str, Any], list[dict[str, Any]]]:
    try:
        master_obj = load_json(METHOD_MASTER)
        master_records = records_from(master_obj, ("methods", "method_registry", "registry"), METHOD_MASTER)
        master_ids = [stable_id(record, ("method_id",), METHOD_MASTER) for record in master_records]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"master method registry audit error: {exc}")
        return 0, set(), {}, []
    if len(master_records) != 1000:
        errors.append(f"master method total mismatch; expected=1000 actual={len(master_records)}")
    if master_ids != [f"PM{i:04d}" for i in range(1, 1001)]:
        errors.append("master IDs must be ordered and unique PM0001–PM1000")
    if len(master_ids) != len(set(master_ids)):
        errors.append("master method registry contains duplicate IDs")

    shards = list_shards(REGISTRY / "method_shards", METHOD_PATTERN, errors)
    if len(shards) != 40:
        errors.append(f"method shard count mismatch; expected=40 (25 records each) actual={len(shards)}")
    all_ids: set[str] = set()
    combined_records: list[dict[str, Any]] = []
    index_entries = []
    for part, path in shards:
        try:
            raw = path.read_bytes()
            obj = json.loads(raw.decode("utf-8"))
            records = records_from(obj, ("methods",), path)
            ids = [stable_id(record, ("method_id",), path) for record in records]
            expected_records = master_records[(part - 1) * METHOD_SIZE:part * METHOD_SIZE]
            expected_ids = master_ids[(part - 1) * METHOD_SIZE:part * METHOD_SIZE]
            if len(records) != METHOD_SIZE:
                errors.append(f"{path.relative_to(ROOT)}: expected {METHOD_SIZE} records; actual={len(records)}")
            if isinstance(obj, dict) and obj.get("part") != part:
                errors.append(f"{path.relative_to(ROOT)}: part metadata {obj.get('part')} != {part}")
            if isinstance(obj, dict) and obj.get("count") != len(records):
                errors.append(f"{path.relative_to(ROOT)}: declared count {obj.get('count')} != {len(records)}")
            if ids != expected_ids or records != expected_records:
                errors.append(f"{path.relative_to(ROOT)}: records are not the exact canonical master slice for part {part}")
            if len(ids) != len(set(ids)):
                errors.append(f"{path.relative_to(ROOT)}: duplicate IDs within shard")
            duplicates = all_ids.intersection(ids)
            if duplicates:
                errors.append(f"{path.relative_to(ROOT)}: duplicate IDs across shards: {sorted(duplicates)[:5]}")
            all_ids.update(ids)
            combined_records.extend(records)
            index_entries.append(make_index_entry(part, path, records, ("method_id",), raw))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(str(exc))
    if combined_records != master_records:
        errors.append("concatenated method shards differ from full method master")
    return len(combined_records), all_ids, {"master_records": len(master_records), "master_unique_ids": len(set(master_ids))}, index_entries


def audit_config_shards(errors: list[str]) -> tuple[int, set[str], list[dict[str, Any]]]:
    try:
        manifest = load_json(CONFIG_MANIFEST)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load config manifest: {exc}")
        return 0, set(), []
    if not isinstance(manifest, dict):
        errors.append("config manifest root must be an object")
        return 0, set(), []
    if manifest.get("config_hash_rule") != CONFIG_HASH_RULE:
        errors.append(f"config hash rule must be the exact-file-byte contract: {CONFIG_HASH_RULE}")
    declarations = manifest.get("config_shards")
    if not isinstance(declarations, list):
        errors.append("config manifest config_shards must be a list")
        return 0, set(), []
    by_path = {item.get("path"): item for item in declarations if isinstance(item, dict) and isinstance(item.get("path"), str)}
    if len(by_path) != len(declarations):
        errors.append("config manifest contains malformed or duplicate shard paths")

    shards = list_shards(REGISTRY / "config_shards", CONFIG_PATTERN, errors)
    if len(shards) != 80:
        errors.append(f"config shard count mismatch; expected=80 (100 records each) actual={len(shards)}")
    if len(declarations) != len(shards):
        errors.append(f"config manifest shard entry count mismatch; manifest={len(declarations)} actual_files={len(shards)}")

    all_ids: set[str] = set()
    total = 0
    index_entries = []
    for part, path in shards:
        rel = path.relative_to(ROOT).as_posix()
        declaration = by_path.get(rel)
        if declaration is None:
            errors.append(f"{rel}: no declaration in config manifest")
            declaration = {}
        try:
            raw = path.read_bytes()
            obj = json.loads(raw.decode("utf-8"))
            records = records_from(obj, ("configs", "configurations", "records"), path)
            ids = [stable_id(record, ("config_id", "configuration_id", "id"), path) for record in records]
            actual_sha = sha256_bytes(raw)
            if declaration.get("sha256") != actual_sha:
                errors.append(f"{rel}: exact-file-byte SHA-256 mismatch; manifest={declaration.get('sha256')} actual={actual_sha}")
            if declaration.get("byte_count") != len(raw):
                errors.append(f"{rel}: byte count mismatch; manifest={declaration.get('byte_count')} actual={len(raw)}")
            if len(records) != CONFIG_SIZE:
                errors.append(f"{rel}: expected {CONFIG_SIZE} records; actual={len(records)}")
            if declaration.get("count") != len(records):
                errors.append(f"{rel}: declared count mismatch; manifest={declaration.get('count')} actual={len(records)}")
            if not ids or ids[0] != declaration.get("first_id"):
                errors.append(f"{rel}: first ID mismatch; manifest={declaration.get('first_id')} actual={ids[0] if ids else None}")
            if not ids or ids[-1] != declaration.get("last_id"):
                errors.append(f"{rel}: last ID mismatch; manifest={declaration.get('last_id')} actual={ids[-1] if ids else None}")
            if isinstance(obj, dict) and (obj.get("part") != part or obj.get("count") != len(records)):
                errors.append(f"{rel}: shard part/count metadata mismatch")
            if len(ids) != len(set(ids)):
                errors.append(f"{rel}: duplicate IDs within shard")
            duplicates = all_ids.intersection(ids)
            if duplicates:
                errors.append(f"{rel}: duplicate IDs across shards: {sorted(duplicates)[:5]}")
            all_ids.update(ids)
            total += len(records)
            index_entries.append(make_index_entry(part, path, records, ("config_id", "configuration_id", "id"), raw))
        except (KeyError, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"config shard audit error: {exc}")
    if total != manifest.get("configuration_count"):
        errors.append(f"config total mismatch; manifest={manifest.get('configuration_count')} actual={total}")
    if total != 8000 or len(all_ids) != 8000:
        errors.append(f"config total/uniqueness mismatch; expected=8000 records and IDs, actual={total}/{len(all_ids)}")
    return total, all_ids, index_entries


def audit_index(errors: list[str], method_entries: list[dict[str, Any]], config_entries: list[dict[str, Any]]) -> None:
    try:
        index = load_json(INDEX_PATH)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read shard index: {exc}")
        return
    if not isinstance(index, dict) or index.get("schema_version") != "prediction-registry-shard-index-v2-r2":
        errors.append("shard index schema/version invalid")
        return
    if index.get("method_record_count") != 1000 or index.get("configuration_record_count") != 8000:
        errors.append("shard index aggregate record counts are invalid")
    if index.get("method_shards") != method_entries:
        errors.append("method shard index does not exactly match recomputed paths/bytes/counts/ranges/hashes")
    if index.get("config_shards") != config_entries:
        errors.append("config shard index does not exactly match recomputed paths/bytes/counts/ranges/hashes")
    if index.get("status") != "DATA_INTEGRITY_ONLY_SCIENTIFIC_GATE_BLOCKED":
        errors.append("shard index must preserve blocked scientific status")


def main() -> int:
    errors: list[str] = []
    method_count, method_ids, master_summary, method_entries = audit_method_shards(errors)
    config_count, config_ids, config_entries = audit_config_shards(errors)
    if method_count != 1000 or len(method_ids) != 1000:
        errors.append(f"method shard total/uniqueness mismatch; expected=1000/1000 actual={method_count}/{len(method_ids)}")
    audit_index(errors, method_entries, config_entries)
    report = {
        "method_shards": {"shard_records": method_count, "unique_shard_ids": len(method_ids), **master_summary},
        "config_shards": {"records": config_count, "unique_ids": len(config_ids), "shard_count": len(config_entries)},
        "shard_index": INDEX_PATH.relative_to(ROOT).as_posix(),
        "errors": errors,
        "scientific_status": "UNREVIEWED; data integrity checks do not establish compatibility or predictive validity",
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
