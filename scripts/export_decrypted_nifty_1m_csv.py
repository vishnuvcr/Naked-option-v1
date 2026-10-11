#!/usr/bin/env python3
"""Export the tester-reviewed derived dataset as one unencrypted CSV for offline storage.

The source artifact and encrypted derived artifact are immutable. HF_TOKEN is only
read from the environment; it is never printed, serialized, or written to disk.
Only aggregate metadata is emitted to logs.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import pathlib
import shutil
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import decrypt_nifty_1m_composite as decryptor

SOURCE_RUN_ID = 38126168547
SOURCE_ARTIFACT_ID = 11696937921
SOURCE_ARTIFACT_SHA256 = "5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b"
DERIVED_RUN_ID = 38131641336
DERIVED_ARTIFACT_ID = 11698879857
EXPECTED_DATASET_ID = (
    "NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_"
    "SPOT_GAPFILL_DERIVED_REPAIR_V1"
)
EXPECTED_PARTS = 61
EXPECTED_ROWS = 8_999_865
EXPECTED_OPTION_ROWS = 8_490_723
EXPECTED_SPOT_ROWS = 509_142


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_manifest(bundle_dir: pathlib.Path) -> pathlib.Path:
    matches = list(bundle_dir.rglob("dataset_manifest.json"))
    if len(matches) != 1:
        raise ValueError("derived_dataset_manifest_count_invalid")
    return matches[0]


def verify_and_prepare(bundle_dir: pathlib.Path, input_dir: pathlib.Path) -> dict[str, Any]:
    manifest_path = locate_manifest(bundle_dir)
    part_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset_id") != EXPECTED_DATASET_ID:
        raise ValueError("derived_dataset_id_mismatch")
    if manifest.get("download_bundle_contains_encrypted_data_only") is not True:
        raise ValueError("encrypted_only_marker_missing")
    lineage = manifest.get("derived_from", {})
    if (
        lineage.get("parent_artifact_run_id") != SOURCE_RUN_ID
        or lineage.get("parent_artifact_id") != SOURCE_ARTIFACT_ID
        or lineage.get("parent_artifact_sha256") != SOURCE_ARTIFACT_SHA256
    ):
        raise ValueError("derived_source_lineage_mismatch")

    parts = manifest.get("parts")
    if not isinstance(parts, list) or len(parts) != EXPECTED_PARTS:
        raise ValueError("derived_part_count_mismatch")
    if sum(int(p.get("row_count", -1)) for p in parts) != EXPECTED_ROWS:
        raise ValueError("derived_expected_row_count_mismatch")

    names: set[str] = set()
    input_dir.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(manifest_path, input_dir / "dataset_manifest.json")
    for part in parts:
        name = str(part.get("file", ""))
        if pathlib.Path(name).name != name or not name.endswith(".csv.gz.enc") or not name:
            raise ValueError("unsafe_derived_part_name")
        if name in names:
            raise ValueError("duplicate_derived_part_name")
        names.add(name)
        path = part_dir / name
        if not path.is_file():
            raise ValueError("derived_encrypted_part_missing")
        if path.stat().st_size != int(part.get("encrypted_bytes", -1)):
            raise ValueError("derived_encrypted_part_size_mismatch")
        if sha256_file(path) != part.get("encrypted_sha256"):
            raise ValueError("derived_encrypted_part_hash_mismatch")
        (input_dir / name).symlink_to(path)

    observed = {p.name for p in part_dir.glob("*.csv.gz.enc")}
    if observed != names:
        raise ValueError("derived_encrypted_part_set_mismatch")
    return manifest


def merge_parts_to_csv(parts: list[pathlib.Path], expected_counts: dict[str, int],
                       output_csv: pathlib.Path, expected_total_rows: int) -> int:
    """Stream-decompress monthly parts into one CSV, validating every header and row width."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    first_header: list[str] | None = None
    temporary = output_csv.with_suffix(output_csv.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as out:
            writer = None
            for part_path in sorted(parts):
                month_count = 0
                with gzip.open(part_path, "rt", encoding="utf-8", newline="") as inp:
                    reader = csv.reader(inp)
                    try:
                        header = next(reader)
                    except StopIteration:
                        raise ValueError("monthly_csv_header_missing")
                    if not header or len(header) != len(set(header)):
                        raise ValueError("monthly_csv_header_invalid")
                    if first_header is None:
                        first_header = header
                        writer = csv.writer(out, lineterminator="\n")
                        writer.writerow(header)
                    elif header != first_header:
                        raise ValueError("monthly_csv_schema_mismatch")
                    assert writer is not None
                    for row in reader:
                        if len(row) != len(first_header):
                            raise ValueError("monthly_csv_row_width_mismatch")
                        writer.writerow(row)
                        month_count += 1
                        row_count += 1
                if month_count != expected_counts.get(part_path.name, -1):
                    raise ValueError("monthly_csv_row_count_mismatch")
        if row_count != expected_total_rows:
            raise ValueError("merged_csv_total_row_count_mismatch")
        temporary.replace(output_csv)
        return row_count
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        try:
            output_csv.unlink()
        except OSError:
            pass
        raise


def export(bundle_dir: pathlib.Path, work_dir: pathlib.Path, export_dir: pathlib.Path,
           secret: str) -> dict[str, Any]:
    manifest = verify_and_prepare(bundle_dir, work_dir / "encrypted-input")
    parts_plain_dir = work_dir / "decrypted-monthly-parts"
    parts_plain_dir.mkdir(parents=True, exist_ok=False)
    key = decryptor.derive_key(secret)
    encrypted_parts = decryptor.decrypt_dataset(
        work_dir / "encrypted-input", parts_plain_dir, key, overwrite=False
    )
    by_name = {str(p["file"]).removesuffix(".enc"): int(p["row_count"]) for p in manifest["parts"]}
    output_csv = export_dir / "nifty_1m_composite_repaired.csv"
    rows_written = merge_parts_to_csv(encrypted_parts, by_name, output_csv, EXPECTED_ROWS)
    counts_by_type: dict[str, int] = {}
    header = None
    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        if not header or "row_type" not in header:
            raise ValueError("merged_csv_row_type_column_missing")
        for row in reader:
            typ = row.get("row_type", "")
            counts_by_type[typ] = counts_by_type.get(typ, 0) + 1
    if counts_by_type != {"OPTION": EXPECTED_OPTION_ROWS, "SPOT": EXPECTED_SPOT_ROWS}:
        raise ValueError("merged_csv_row_type_count_mismatch")
    report = {
        "export_status": "PASS",
        "dataset_id": EXPECTED_DATASET_ID,
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_sha256": SOURCE_ARTIFACT_SHA256,
        "derived_run_id": DERIVED_RUN_ID,
        "derived_artifact_id": DERIVED_ARTIFACT_ID,
        "output_file": output_csv.name,
        "output_bytes": output_csv.stat().st_size,
        "output_sha256": sha256_file(output_csv),
        "data_rows": rows_written,
        "rows_by_type": counts_by_type,
        "csv_columns": len(header or []),
        "encrypted_monthly_parts_decrypted_and_verified": len(encrypted_parts),
        "payload_is_encrypted": False,
        "source_rows_modified": False,
        "source_api_requests_made": False,
        "plaintext_repo_commit": False,
        "research_coverage_restrictions": [
            "19,021 option rows remain unmatched and their underlying OHLCV remains blank.",
            "24,847 rows carry weekend-session review flags.",
            "Invalid source values were masked during the accepted repair; see the repair report and manifest.",
            "This is a research dataset, not a claim of prediction or trading profitability."
        ],
    }
    (export_dir / "EXPORT_MANIFEST.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (export_dir / "README_OFFLINE.txt").write_text(
        "NIFTY 1-minute repaired composite dataset\n"
        "==========================================\n"
        "File: nifty_1m_composite_repaired.csv\n"
        f"Data rows: {rows_written:,}\n"
        f"OPTION rows: {counts_by_type.get('OPTION', 0):,}\n"
        f"SPOT rows: {counts_by_type.get('SPOT', 0):,}\n"
        f"CSV columns: {len(header or [])}\n"
        f"SHA-256: {report['output_sha256']}\n\n"
        "This file is decrypted and unencrypted for offline storage. Keep it private\n"
        "according to your own storage practices. It was exported from the immutable,\n"
        "encrypted derived artifact after every encrypted monthly part passed its\n"
        "checksum/authentication checks and the merged row totals were verified.\n\n"
        "Coverage restrictions: 19,021 OPTION rows are still unmatched for underlying\n"
        "OHLCV; 24,847 rows retain weekend-session review flags. Invalid values are\n"
        "represented as blank, not guessed or interpolated. See EXPORT_MANIFEST.json\n"
        "and the repository's derived dataset repair report for details.\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", required=True, type=pathlib.Path)
    parser.add_argument("--work-dir", required=True, type=pathlib.Path)
    parser.add_argument("--export-dir", required=True, type=pathlib.Path)
    args = parser.parse_args()
    secret = os.environ.get("HF_TOKEN", "")
    if not secret:
        raise ValueError("HF_TOKEN_environment_variable_required")
    report = export(args.bundle_dir, args.work_dir, args.export_dir, secret)
    print(json.dumps({
        "export_status": report["export_status"],
        "output_file": report["output_file"],
        "output_bytes": report["output_bytes"],
        "output_sha256": report["output_sha256"],
        "data_rows": report["data_rows"],
        "rows_by_type": report["rows_by_type"],
        "csv_columns": report["csv_columns"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("EXPORT_ERROR " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        raise SystemExit(1)
