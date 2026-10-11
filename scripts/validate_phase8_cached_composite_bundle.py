from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_DATASET_ID = "NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_SPOT_GAPFILL_DERIVED_REPAIR_V1"
EXPECTED_PARENT_ARTIFACT_ID = 11696937921
EXPECTED_PARENT_RUN_ID = 38126168547
EXPECTED_PARENT_ARTIFACT_SHA256 = "5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_part_path(name: Any) -> str:
    if not isinstance(name, str) or not name.endswith(".csv.gz.enc") or Path(name).name != name:
        raise ValueError("BUNDLE_BLOCKED: unsafe encrypted-part filename")
    return name


def validate_bundle(bundle_dir: Path, reference_manifest_path: Path) -> dict[str, Any]:
    """Verify encrypted artifacts against a checked-in immutable reference manifest.

    This function hashes only encrypted payload bytes and public metadata. It never
    decrypts a part or reads market observations.
    """
    if not bundle_dir.is_dir():
        raise ValueError("BUNDLE_BLOCKED: bundle directory is missing")
    candidates = list(bundle_dir.rglob("dataset_manifest.json"))
    if len(candidates) != 1:
        raise ValueError(f"BUNDLE_BLOCKED: expected exactly one dataset_manifest.json, found {len(candidates)}")
    bundle_manifest_path = candidates[0]
    bundle_manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_manifest_path.read_text(encoding="utf-8"))

    if reference.get("dataset_id") != EXPECTED_DATASET_ID:
        raise ValueError("BUNDLE_BLOCKED: checked-in reference dataset ID mismatch")
    if reference.get("encrypted_only") is not True:
        raise ValueError("BUNDLE_BLOCKED: reference is not marked encrypted-only")
    if reference.get("parent_artifact_id") != EXPECTED_PARENT_ARTIFACT_ID:
        raise ValueError("BUNDLE_BLOCKED: reference parent artifact ID mismatch")
    if reference.get("parent_artifact_run_id") != EXPECTED_PARENT_RUN_ID:
        raise ValueError("BUNDLE_BLOCKED: reference parent run ID mismatch")
    if reference.get("parent_artifact_sha256") != EXPECTED_PARENT_ARTIFACT_SHA256:
        raise ValueError("BUNDLE_BLOCKED: reference parent artifact SHA-256 mismatch")

    if bundle_manifest.get("dataset_id") != reference.get("dataset_id"):
        raise ValueError("BUNDLE_BLOCKED: downloaded dataset ID differs from checked-in manifest")
    if bundle_manifest.get("download_bundle_contains_encrypted_data_only") is not True:
        raise ValueError("BUNDLE_BLOCKED: downloaded artifact lacks encrypted-only marker")
    derived = bundle_manifest.get("derived_from")
    if not isinstance(derived, dict):
        raise ValueError("BUNDLE_BLOCKED: downloaded derived_from record missing")
    if derived.get("parent_artifact_id") != EXPECTED_PARENT_ARTIFACT_ID:
        raise ValueError("BUNDLE_BLOCKED: downloaded parent artifact ID mismatch")
    if derived.get("parent_artifact_run_id") != EXPECTED_PARENT_RUN_ID:
        raise ValueError("BUNDLE_BLOCKED: downloaded parent run ID mismatch")
    if derived.get("parent_artifact_sha256") != EXPECTED_PARENT_ARTIFACT_SHA256:
        raise ValueError("BUNDLE_BLOCKED: downloaded parent artifact SHA-256 mismatch")

    expected_parts = reference.get("part_hashes")
    actual_parts = bundle_manifest.get("parts")
    expected_count = int(reference.get("part_count", -1))
    if not isinstance(expected_parts, list) or not isinstance(actual_parts, list):
        raise ValueError("BUNDLE_BLOCKED: part records missing")
    if expected_count <= 0 or len(expected_parts) != expected_count or len(actual_parts) != expected_count:
        raise ValueError("BUNDLE_BLOCKED: encrypted part count mismatch")

    expected_by_name = {}
    for item in expected_parts:
        name = _safe_part_path(item.get("file"))
        if name in expected_by_name:
            raise ValueError("BUNDLE_BLOCKED: duplicate filename in pinned reference manifest")
        expected_by_name[name] = item
    actual_by_name = {}
    for item in actual_parts:
        name = _safe_part_path(item.get("file"))
        if name in actual_by_name:
            raise ValueError("BUNDLE_BLOCKED: duplicate filename in downloaded manifest")
        actual_by_name[name] = item
    if set(actual_by_name) != set(expected_by_name):
        raise ValueError("BUNDLE_BLOCKED: downloaded filenames differ from pinned part set")

    expected_total_rows = 0
    verified_bytes = 0
    verified_parts = []
    for name, ref_part in expected_by_name.items():
        part = actual_by_name[name]
        for field in ("row_count", "encrypted_bytes", "encrypted_sha256", "plain_gzip_sha256"):
            if part.get(field) != ref_part.get(field):
                raise ValueError(f"BUNDLE_BLOCKED: downloaded manifest {field} mismatch for {name}")
        path = bundle_manifest_path.parent / name
        if not path.is_file():
            raise ValueError(f"BUNDLE_BLOCKED: encrypted part missing: {name}")
        expected_bytes = int(ref_part.get("encrypted_bytes", -1))
        if path.stat().st_size != expected_bytes:
            raise ValueError(f"BUNDLE_BLOCKED: encrypted byte count mismatch: {name}")
        digest = sha256_file(path)
        if digest != ref_part.get("encrypted_sha256"):
            raise ValueError(f"BUNDLE_BLOCKED: encrypted SHA-256 mismatch: {name}")
        rows = int(ref_part.get("row_count", -1))
        if rows < 0:
            raise ValueError(f"BUNDLE_BLOCKED: invalid row count: {name}")
        expected_total_rows += rows
        verified_bytes += expected_bytes
        verified_parts.append({"file": name, "rows": rows, "encrypted_bytes": expected_bytes, "sha256": digest})

    if expected_total_rows != 8_999_865:
        raise ValueError(f"BUNDLE_BLOCKED: pinned part row sum mismatch: {expected_total_rows}")
    if len(list(bundle_manifest_path.parent.glob("*.csv.gz.enc"))) != expected_count:
        raise ValueError("BUNDLE_BLOCKED: encrypted payload count does not match manifest")

    return {
        "status": "PASS_ENCRYPTED_BUNDLE_INTEGRITY",
        "dataset_id": reference["dataset_id"],
        "manifest_path": str(bundle_manifest_path),
        "encrypted_part_count": expected_count,
        "verified_encrypted_bytes": verified_bytes,
        "expected_data_rows": expected_total_rows,
        "all_encrypted_part_hashes_match": True,
        "all_names_and_sizes_match": True,
        "plaintext_opened": False,
        "market_rows_read": False,
        "part_hashes": verified_parts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify pinned encrypted NIFTY composite bundle before decryption.")
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate_bundle(args.bundle_dir, args.reference_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "part_hashes"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
