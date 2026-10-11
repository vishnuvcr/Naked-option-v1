from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SOURCE_PATHS = {
    "daily_csv": "data/cache/raw/phase3/nifty50_daily.csv",
    "intraday_parquet": "data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet",
}


class SourceCacheError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_cached_source_inputs(
    manifest_path: Path,
    root: Path = ROOT,
    *,
    allow_missing: bool = False,
) -> dict:
    """Verify only local, frozen Phase 7 source files; never access the network."""
    if not manifest_path.is_file():
        raise SourceCacheError(f"frozen reference manifest is missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceCacheError(f"cannot read frozen reference manifest: {exc}") from exc

    sources = manifest.get("source_files")
    if not isinstance(sources, dict) or set(sources) != set(EXPECTED_SOURCE_PATHS):
        raise SourceCacheError("reference manifest has unexpected/missing source-file entries")

    checked = []
    missing = []
    mismatches = []
    for name, expected_rel in EXPECTED_SOURCE_PATHS.items():
        record = sources.get(name)
        if not isinstance(record, dict):
            raise SourceCacheError(f"malformed source manifest entry: {name}")
        if record.get("path") != expected_rel:
            raise SourceCacheError(
                f"source path pin changed for {name}: expected {expected_rel!r}, "
                f"got {record.get('path')!r}"
            )
        expected_sha = str(record.get("sha256", "")).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            raise SourceCacheError(f"malformed SHA-256 for frozen source {name}")

        resolved_root = root.resolve()
        local_path = (root / expected_rel).resolve()
        if local_path != resolved_root and resolved_root not in local_path.parents:
            raise SourceCacheError(f"source path escapes repository root: {expected_rel}")
        if not local_path.is_file():
            missing.append({"name": name, "path": expected_rel, "expected_sha256": expected_sha})
            continue

        actual_sha = _sha256(local_path)
        item = {
            "name": name,
            "path": expected_rel,
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "matches": actual_sha == expected_sha,
            "size_bytes": local_path.stat().st_size,
        }
        checked.append(item)
        if actual_sha != expected_sha:
            mismatches.append(item)

    if mismatches:
        # Never overwrite or silently reacquire a present but wrong source file.
        return {
            "schema_version": 1,
            "status": "HASH_MISMATCH",
            "network_accessed": False,
            "checked": checked,
            "missing": missing,
            "mismatches": mismatches,
        }
    if missing:
        return {
            "schema_version": 1,
            "status": "MISSING",
            "network_accessed": False,
            "checked": checked,
            "missing": missing,
            "mismatches": [],
        }
    return {
        "schema_version": 1,
        "status": "PASS",
        "network_accessed": False,
        "checked": checked,
        "missing": [],
        "mismatches": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify frozen Phase 7 input files from local cache; this script never downloads data."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data/cache/reference/phase7_run994/unpacked/phase7_reference/phase7_reference_manifest.json",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "data/reports/phase8/source_cache_verification.json")
    parser.add_argument("--allow-missing", action="store_true", help="report MISSING with exit 0; useful only before an independently authorized bootstrap")
    args = parser.parse_args(argv)

    try:
        report = verify_cached_source_inputs(args.manifest, args.root, allow_missing=args.allow_missing)
    except SourceCacheError as exc:
        report = {
            "schema_version": 1,
            "status": "ERROR",
            "network_accessed": False,
            "error": str(exc),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

    status = report["status"]
    if status == "PASS":
        return 0
    if status == "MISSING" and args.allow_missing:
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
