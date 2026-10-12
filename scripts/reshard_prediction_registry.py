#!/usr/bin/env python3
"""Rebuild R2 registries into independently auditable, small deterministic shards.

This is data-manifest tooling only. It does not approve compatibility or authorize model fitting.
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
METHOD_DIR = REGISTRY / "method_shards"
CONFIG_DIR = REGISTRY / "config_shards"
METHOD_SIZE = 25
CONFIG_SIZE = 100
METHOD_TOTAL = 1000
CONFIG_TOTAL = 8000
CONFIG_KEYS = ("configs", "configurations", "records")
CONFIG_ID_KEYS = ("config_id", "configuration_id", "id")
METHOD_ID_RE = re.compile(r"^PM\d{4}$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_list(obj: Any, keys: tuple[str, ...], path: Path) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        records = obj
    elif isinstance(obj, dict):
        found = [key for key in keys if isinstance(obj.get(key), list)]
        if len(found) != 1:
            raise SystemExit(f"BLOCKED: expected exactly one record array in {path}; found {found}")
        records = obj[found[0]]
    else:
        raise SystemExit(f"BLOCKED: expected JSON object/list in {path}")
    if not all(isinstance(record, dict) for record in records):
        raise SystemExit(f"BLOCKED: non-object record in {path}")
    return records


def record_id(record: dict[str, Any], keys: tuple[str, ...], path: Path) -> str:
    found = [key for key in keys if key in record]
    if len(found) != 1:
        raise SystemExit(f"BLOCKED: expected exactly one ID key {keys} in {path}; found {found}")
    value = record[found[0]]
    if not isinstance(value, (str, int)) or isinstance(value, bool) or not str(value).strip():
        raise SystemExit(f"BLOCKED: invalid ID {value!r} in {path}")
    return str(value)


def shard_entry(path: Path, records: list[dict[str, Any]], id_keys: tuple[str, ...], part: int) -> dict[str, Any]:
    raw = path.read_bytes()
    ids = [record_id(row, id_keys, path) for row in records]
    return {
        "part": part,
        "path": path.relative_to(ROOT).as_posix(),
        "byte_count": len(raw),
        "record_count": len(records),
        "first_id": ids[0],
        "last_id": ids[-1],
        "sha256": sha256(raw),
    }


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def chunks(records: list[dict[str, Any]], size: int):
    for start in range(0, len(records), size):
        yield start // size + 1, records[start:start + size]


def validate_existing_method_shards(master_by_id: dict[str, dict[str, Any]]) -> None:
    pattern = re.compile(r"^METHODS_V2_R2_PART(\d+)\.json$")
    paths = sorted(METHOD_DIR.glob("METHODS_V2_R2_PART*.json"))
    seen_in_each_file: set[str] = set()
    for path in paths:
        if not pattern.fullmatch(path.name):
            raise SystemExit(f"BLOCKED: ambiguous method shard filename {path.name}")
        obj = load_json(path)
        records = record_list(obj, ("methods",), path)
        file_ids: set[str] = set()
        for record in records:
            method_id = record_id(record, ("method_id",), path)
            if method_id in file_ids:
                raise SystemExit(f"BLOCKED: duplicate method ID inside existing shard {path.name}: {method_id}")
            file_ids.add(method_id)
            if method_id not in master_by_id:
                raise SystemExit(f"BLOCKED: existing shard contains unknown method ID {method_id}")
            if record != master_by_id[method_id]:
                raise SystemExit(f"BLOCKED: existing method record differs from master for {method_id}")
            # Overlap between differently named legacy shard sets is allowed only
            # when each repeated record is byte-semantically equal to the master.
            seen_in_each_file.add(method_id)


def load_and_validate_configs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    old_shards = manifest.get("config_shards")
    if not isinstance(old_shards, list) or not old_shards:
        raise SystemExit("BLOCKED: config manifest has no shard list")
    if manifest.get("config_hash_rule") != "SHA-256 over exact committed shard file bytes; UTF-8 JSON bytes, including any final newline":
        raise SystemExit("BLOCKED: existing config hashes do not declare the exact-file-byte contract")
    all_records: list[dict[str, Any]] = []
    all_ids: set[str] = set()
    for declaration in old_shards:
        if not isinstance(declaration, dict) or not isinstance(declaration.get("path"), str):
            raise SystemExit("BLOCKED: malformed existing config shard declaration")
        rel = declaration["path"]
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise SystemExit(f"BLOCKED: unsafe config path {rel}")
        path = (ROOT / rel).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise SystemExit(f"BLOCKED: missing or unsafe config file {rel}")
        raw = path.read_bytes()
        actual_sha = sha256(raw)
        if declaration.get("sha256") != actual_sha:
            raise SystemExit(f"BLOCKED: config source hash mismatch for {rel}; will not re-shard unverified input")
        obj = json.loads(raw.decode("utf-8"))
        records = record_list(obj, CONFIG_KEYS, path)
        ids = [record_id(row, CONFIG_ID_KEYS, path) for row in records]
        if len(records) != declaration.get("count"):
            raise SystemExit(f"BLOCKED: config source count mismatch in {rel}")
        if not ids or ids[0] != declaration.get("first_id") or ids[-1] != declaration.get("last_id"):
            raise SystemExit(f"BLOCKED: config source range mismatch in {rel}")
        if len(ids) != len(set(ids)):
            raise SystemExit(f"BLOCKED: duplicate config IDs within {rel}")
        duplicates = all_ids.intersection(ids)
        if duplicates:
            raise SystemExit(f"BLOCKED: duplicate config IDs across source shards: {sorted(duplicates)[:5]}")
        all_ids.update(ids)
        all_records.extend(records)
    if len(all_records) != CONFIG_TOTAL or len(all_ids) != CONFIG_TOTAL:
        raise SystemExit(f"BLOCKED: expected {CONFIG_TOTAL} unique configs; found {len(all_records)} records/{len(all_ids)} unique IDs")
    return all_records


def main() -> int:
    master_obj = load_json(METHOD_MASTER)
    methods = record_list(master_obj, ("methods", "method_registry", "registry"), METHOD_MASTER)
    expected_method_ids = [f"PM{i:04d}" for i in range(1, METHOD_TOTAL + 1)]
    method_ids = [record_id(record, ("method_id",), METHOD_MASTER) for record in methods]
    if len(methods) != METHOD_TOTAL or method_ids != expected_method_ids:
        raise SystemExit("BLOCKED: master must contain ordered unique PM0001–PM1000")
    master_by_id = dict(zip(method_ids, methods))
    validate_existing_method_shards(master_by_id)

    manifest = load_json(CONFIG_MANIFEST)
    if not isinstance(manifest, dict) or manifest.get("configuration_count") != CONFIG_TOTAL:
        raise SystemExit("BLOCKED: config manifest must declare exactly 8000 configurations")
    configs = load_and_validate_configs(manifest)

    method_paths_expected: set[str] = set()
    method_index = []
    for part, records in chunks(methods, METHOD_SIZE):
        filename = f"METHODS_V2_R2_PART{part:03d}.json"
        path = METHOD_DIR / filename
        payload = {"schema_version": "prediction-method-shard-v2-r2", "part": part, "count": len(records), "methods": records}
        atomic_write(path, json_bytes(payload))
        entry = shard_entry(path, records, ("method_id",), part)
        method_index.append(entry)
        method_paths_expected.add(path.name)

    config_shards = []
    config_index = []
    config_paths_expected: set[str] = set()
    for part, records in chunks(configs, CONFIG_SIZE):
        filename = f"PREDICTION_CONFIGS_V2_R2_PART{part:03d}.json"
        path = CONFIG_DIR / filename
        payload = {"schema_version": "prediction-config-shard-v2-r2", "part": part, "count": len(records), "configs": records}
        atomic_write(path, json_bytes(payload))
        entry = shard_entry(path, records, CONFIG_ID_KEYS, part)
        config_index.append(entry)
        config_paths_expected.add(path.name)
        config_shards.append({
            "path": entry["path"],
            "sha256": entry["sha256"],
            "byte_count": entry["byte_count"],
            "count": entry["record_count"],
            "first_id": entry["first_id"],
            "last_id": entry["last_id"],
        })

    # Remove only superseded files that match the registry shard name patterns.
    for path in METHOD_DIR.glob("METHODS_V2_R2_PART*.json"):
        if path.name not in method_paths_expected:
            path.unlink()
    for path in CONFIG_DIR.glob("PREDICTION_CONFIGS_V2_R2_PART*.json"):
        if path.name not in config_paths_expected:
            path.unlink()

    manifest["config_hash_rule"] = "SHA-256 over exact committed shard file bytes; UTF-8 JSON bytes, including any final newline"
    manifest["config_shards"] = config_shards
    atomic_write(CONFIG_MANIFEST, json_bytes(manifest))

    index = {
        "schema_version": "prediction-registry-shard-index-v2-r2",
        "status": "DATA_INTEGRITY_ONLY_SCIENTIFIC_GATE_BLOCKED",
        "method_record_count": METHOD_TOTAL,
        "configuration_record_count": CONFIG_TOTAL,
        "method_shards": method_index,
        "config_shards": config_index,
    }
    atomic_write(INDEX_PATH, json_bytes(index))
    print(json.dumps({
        "result": "RESHARDED",
        "method_records": METHOD_TOTAL,
        "method_shards": len(method_index),
        "method_records_per_shard": METHOD_SIZE,
        "config_records": CONFIG_TOTAL,
        "config_shards": len(config_index),
        "config_records_per_shard": CONFIG_SIZE,
        "index_path": INDEX_PATH.relative_to(ROOT).as_posix(),
        "scientific_gate": "STILL_BLOCKED_PENDING_INDEPENDENT_TESTER",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
