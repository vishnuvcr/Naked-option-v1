#!/usr/bin/env python3
"""Build a separate encrypted, provenance-preserving repaired dataset.

The source artifact is never modified. Exact-epoch standalone SPOT rows are the
only source for repairing joined NIFTY OHLCV. Invalid values become missing;
unmatched timestamps stay unmatched; no nearest-time fill or invented values.
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import pathlib
import tempfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from decrypt_nifty_1m_composite import AAD, MAGIC, derive_key

OHLC_FIELDS = ("open", "high", "low", "close")
SPOT_FIELDS = tuple("nifty_" + f for f in OHLC_FIELDS) + ("nifty_volume",)
OPTION_FIELDS = tuple("option_" + f for f in OHLC_FIELDS)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decimal_or_none(value: str) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def valid_ohlc(row: dict[str, str], prefix: str) -> bool:
    values = [decimal_or_none(row.get(prefix + name, "")) for name in OHLC_FIELDS]
    if any(value is None for value in values):
        return False
    op, high, low, close = values
    return (
        min(op, high, low, close) > 0
        and high >= max(op, close)
        and low <= min(op, close)
        and high >= low
    )


def valid_nonnegative(value: str) -> bool:
    parsed = decimal_or_none(value)
    return parsed is not None and parsed >= 0


def append_flag(row: dict[str, str], flag: str) -> None:
    existing = [x for x in (row.get("data_quality_flags", "") or "").split("|") if x]
    if flag not in existing:
        existing.append(flag)
    row["data_quality_flags"] = "|".join(existing)


def row_epoch(row: dict[str, str]) -> int | None:
    try:
        return int(row.get("timestamp_epoch", ""))
    except (TypeError, ValueError):
        return None


def load_manifest(input_dir: pathlib.Path) -> dict[str, Any]:
    manifest = json.loads((input_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("parts"), list):
        raise ValueError("manifest_schema_invalid")
    if manifest.get("download_bundle_contains_encrypted_data_only") is not True:
        raise ValueError("source_manifest_encrypted_only_marker_missing")
    return manifest


def load_spot_lookup(input_dir: pathlib.Path, manifest: dict[str, Any]) -> tuple[dict[int, dict[str, str]], Counter[str]]:
    lookup: dict[int, dict[str, str]] = {}
    counts: Counter[str] = Counter()
    for part in manifest["parts"]:
        name = str(part.get("file", ""))
        if not name.endswith(".csv.gz.enc") or pathlib.Path(name).name != name:
            raise ValueError("unsafe_manifest_part_name")
        plain_path = input_dir / name.removesuffix(".enc")
        if not plain_path.is_file():
            raise FileNotFoundError("decrypted_month_part_missing")
        with gzip.open(plain_path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("row_type") != "SPOT":
                    continue
                epoch = row_epoch(row)
                if epoch is None:
                    counts["spot_rows_with_invalid_epoch"] += 1
                    continue
                if epoch in lookup:
                    counts["duplicate_spot_epochs"] += 1
                    continue
                lookup[epoch] = {field: row.get(field, "") or "" for field in SPOT_FIELDS}
                lookup[epoch]["data_quality_flags"] = row.get("data_quality_flags", "") or ""
                lookup[epoch]["session_date"] = row.get("session_date", "") or ""
    return lookup, counts


def repair_dataset(input_dir: pathlib.Path, output_dir: pathlib.Path, report_path: pathlib.Path,
                   secret: str) -> dict[str, Any]:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    report_path = report_path.resolve()
    if output_dir == input_dir or input_dir in output_dir.parents or output_dir in input_dir.parents:
        raise ValueError("input_and_output_directories_must_be_disjoint")
    manifest = load_manifest(input_dir)
    columns = manifest.get("columns")
    if not isinstance(columns, list) or not columns:
        raise ValueError("manifest_columns_missing")
    required = {"row_type", "timestamp_epoch", "session_date", "spot_join_status", "data_quality_flags"}
    if not required.issubset(set(columns)):
        raise ValueError("required_repair_columns_missing")
    for name in SPOT_FIELDS + OPTION_FIELDS + ("option_volume",):
        if name not in columns:
            raise ValueError("repair_column_missing_" + name)

    key = derive_key(secret)
    aes = AESGCM(key)
    spot_lookup, lookup_counts = load_spot_lookup(input_dir, manifest)
    output_dir.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    changed_fields: Counter[str] = Counter()
    output_parts: list[dict[str, Any]] = []
    total_rows = 0

    for part in sorted(manifest["parts"], key=lambda p: str(p.get("file", ""))):
        encrypted_name = str(part.get("file", ""))
        plain_name = encrypted_name.removesuffix(".enc")
        source_path = input_dir / plain_name
        if not source_path.is_file():
            raise FileNotFoundError("decrypted_month_part_missing")
        destination_path = output_dir / encrypted_name
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        row_count = 0
        with tempfile.NamedTemporaryFile(prefix="nifty-derived-", suffix=".csv.gz", dir=output_dir, delete=False) as tmp:
            temp_plain = pathlib.Path(tmp.name)
        try:
            with gzip.open(source_path, "rt", encoding="utf-8", newline="") as src:
                with temp_plain.open("wb") as raw_out:
                    with gzip.GzipFile(fileobj=raw_out, mode="wb", compresslevel=6, mtime=0) as gz_out:
                        with io.TextIOWrapper(gz_out, encoding="utf-8", newline="", write_through=True) as text_out:
                            reader = csv.DictReader(src)
                            if reader.fieldnames != columns:
                                raise ValueError("monthly_schema_mismatch")
                            writer = csv.DictWriter(text_out, fieldnames=columns, extrasaction="raise")
                            writer.writeheader()
                            for row in reader:
                                row_count += 1
                                total_rows += 1
                                before = {field: row.get(field, "") or "" for field in SPOT_FIELDS + OPTION_FIELDS + ("option_volume",)}
                                typ = row.get("row_type", "")
                                epoch = row_epoch(row)
                                flags_before = row.get("data_quality_flags", "") or ""

                                if typ == "SPOT":
                                    if not valid_ohlc(row, "nifty_"):
                                        for field in SPOT_FIELDS[:4]:
                                            if row.get(field, ""):
                                                row[field] = ""
                                                changed_fields[field] += 1
                                        counts["spot_rows_with_invalid_ohlc_masked"] += 1
                                        append_flag(row, "REPAIR_SPOT_OHLC_INVALID_MASKED")
                                    if not valid_nonnegative(row.get("nifty_volume", "")) and row.get("nifty_volume", "").strip():
                                        row["nifty_volume"] = ""
                                        changed_fields["nifty_volume"] += 1
                                        counts["spot_rows_with_invalid_volume_masked"] += 1
                                        append_flag(row, "REPAIR_SPOT_VOLUME_INVALID_MASKED")

                                elif typ == "OPTION":
                                    if not valid_ohlc(row, "option_"):
                                        if any(row.get(field, "").strip() for field in OPTION_FIELDS):
                                            for field in OPTION_FIELDS:
                                                if row.get(field, ""):
                                                    row[field] = ""
                                                    changed_fields[field] += 1
                                            counts["option_rows_with_invalid_ohlc_masked"] += 1
                                            append_flag(row, "REPAIR_OPTION_OHLC_INVALID_MASKED")
                                    option_volume = row.get("option_volume", "")
                                    if option_volume.strip() and not valid_nonnegative(option_volume):
                                        row["option_volume"] = ""
                                        changed_fields["option_volume"] += 1
                                        counts["option_rows_with_invalid_volume_masked"] += 1
                                        append_flag(row, "REPAIR_OPTION_VOLUME_INVALID_MASKED")

                                    join_status = row.get("spot_join_status", "")
                                    if join_status == "EXACT_TIMESTAMP_MATCH":
                                        spot = spot_lookup.get(epoch) if epoch is not None else None
                                        if spot is None:
                                            for field in SPOT_FIELDS:
                                                if row.get(field, ""):
                                                    row[field] = ""
                                                    changed_fields[field] += 1
                                            counts["exact_join_rows_missing_spot_source_masked"] += 1
                                            append_flag(row, "REPAIR_EXACT_JOIN_SOURCE_MISSING_MASKED")
                                        else:
                                            spot_row = {"nifty_" + name: spot.get("nifty_" + name, "") for name in OHLC_FIELDS}
                                            spot_ohlc_ok = valid_ohlc(spot_row, "nifty_")
                                            for field in SPOT_FIELDS[:4]:
                                                canonical = spot.get(field, "") if spot_ohlc_ok else ""
                                                if (row.get(field, "") or "") != canonical:
                                                    row[field] = canonical
                                                    changed_fields[field] += 1
                                                    counts["joined_nifty_fields_reconciled"] += 1
                                            spot_volume = spot.get("nifty_volume", "")
                                            canonical_volume = spot_volume if valid_nonnegative(spot_volume) else ""
                                            if (row.get("nifty_volume", "") or "") != canonical_volume:
                                                row["nifty_volume"] = canonical_volume
                                                changed_fields["nifty_volume"] += 1
                                                counts["joined_nifty_fields_reconciled"] += 1
                                            if not spot_ohlc_ok:
                                                counts["joined_rows_masked_due_to_invalid_spot_ohlc"] += 1
                                                append_flag(row, "REPAIR_JOINED_NIFTY_OHLC_MASKED_INVALID_SPOT")
                                            if not valid_nonnegative(spot_volume):
                                                counts["joined_rows_masked_due_to_invalid_spot_volume"] += 1
                                                append_flag(row, "REPAIR_JOINED_NIFTY_VOLUME_MASKED_INVALID_SPOT")
                                            if any((row.get(f, "") or "") != before[f] for f in SPOT_FIELDS):
                                                append_flag(row, "REPAIR_JOINED_NIFTY_FROM_EXACT_SPOT")
                                    elif join_status == "NO_EXACT_TIMESTAMP_SPOT_MATCH":
                                        # Never approximate-fill a target/feature without an exact epoch match.
                                        if any((row.get(field, "") or "") for field in SPOT_FIELDS):
                                            for field in SPOT_FIELDS:
                                                if row.get(field, ""):
                                                    row[field] = ""
                                                    changed_fields[field] += 1
                                            counts["unmatched_rows_with_values_cleared"] += 1
                                            append_flag(row, "REPAIR_UNMATCHED_NIFTY_VALUES_CLEARED")
                                        counts["unmatched_option_rows_preserved"] += 1
                                    else:
                                        if any(row.get(field, "") for field in SPOT_FIELDS):
                                            for field in SPOT_FIELDS:
                                                if row.get(field, ""):
                                                    row[field] = ""
                                                    changed_fields[field] += 1
                                            counts["unknown_join_rows_masked"] += 1
                                        append_flag(row, "REPAIR_UNKNOWN_JOIN_STATUS_MASKED")

                                if row.get("data_quality_flags", "") != flags_before:
                                    counts["rows_with_quality_flags_updated"] += 1
                                writer.writerow(row)

            compressed_plain = temp_plain.read_bytes()
            plain_sha = sha256_bytes(compressed_plain)
            nonce = os.urandom(12)
            encrypted = MAGIC + nonce + aes.encrypt(nonce, compressed_plain, AAD)
            destination_path.write_bytes(encrypted)
            output_parts.append({
                **part,
                "file": encrypted_name,
                "row_count": row_count,
                "encrypted_bytes": len(encrypted),
                "encrypted_sha256": sha256_bytes(encrypted),
                "plain_gzip_sha256": plain_sha,
            })
        finally:
            try:
                temp_plain.unlink()
            except OSError:
                pass

    derived_manifest = copy.deepcopy(manifest)
    derived_manifest["dataset_id"] = str(manifest.get("dataset_id", "dataset")) + "_DERIVED_REPAIR_V1"
    derived_manifest["parts"] = output_parts
    derived_manifest["download_bundle_contains_encrypted_data_only"] = True
    derived_manifest["derived_from"] = {
        "parent_dataset_id": manifest.get("dataset_id"),
        "parent_manifest_sha256": sha256_bytes((input_dir / "dataset_manifest.json").read_bytes()),
        "repair_policy": "EXACT_SPOT_EPOCH_RECONCILIATION_AND_INVALID_VALUE_MASKING_V1",
        "source_rows_modified": False,
    }
    derived_manifest["repair_summary"] = {
        "repair_status": "DERIVED_REPAIRED_WITH_EXPLICIT_MISSINGNESS",
        "row_count_preserved": total_rows,
        "source_rows_deleted": 0,
        "source_requests_made": 0,
        "counts": dict(sorted(counts.items())),
        "changed_field_counts": dict(sorted(changed_fields.items())),
        "lookup_counts": dict(sorted(lookup_counts.items())),
        "unmatched_option_rows_preserved_without_approximate_fill": int(counts["unmatched_option_rows_preserved"]),
        "no_price_values_in_summary": True,
    }
    (output_dir / "dataset_manifest.json").write_text(
        json.dumps(derived_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = {
        "schema_version": 1,
        "audit_type": "DERIVED_DATASET_REPAIR_REPORT",
        "status": "DERIVED_REPAIR_COMPLETE",
        "parent_dataset_id": manifest.get("dataset_id"),
        "derived_dataset_id": derived_manifest["dataset_id"],
        "row_counts": {
            "rows_preserved": total_rows,
            "rows_deleted": 0,
            "option_rows": int(manifest.get("dataset_summary", {}).get("rows_options", -1)),
            "spot_rows": int(manifest.get("dataset_summary", {}).get("rows_spot", -1)),
        },
        "repair_counts": dict(sorted(counts.items())),
        "changed_field_counts": dict(sorted(changed_fields.items())),
        "spot_lookup_counts": dict(sorted(lookup_counts.items())),
        "encrypted_part_count": len(output_parts),
        "plaintext_parts_emitted": False,
        "raw_market_values_emitted": False,
        "live_source_requests_made": False,
        "model_fitting_or_scoring_performed": False,
        "holdout_accessed": False,
        "strategy_or_pnl_tested": False,
        "policy": [
            "Joined NIFTY OHLCV values are reconciled only from a standalone SPOT row at the exact same epoch.",
            "Invalid standalone OHLC and negative/unparseable volume are masked to missing, never clamped or fabricated.",
            "Unmatched option rows remain unmatched; no nearest-time join, timestamp shift or interpolation is applied.",
            "Original source artifact and source rows are immutable; this is a separate encrypted derived dataset.",
            "Modeling eligibility still requires a separate exact-snapshot tester decision."
        ],
        "permission_conclusion": "NO_MODEL_AUTHORIZATION_FROM_REPAIR",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=pathlib.Path)
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    parser.add_argument("--report-json", required=True, type=pathlib.Path)
    args = parser.parse_args()
    secret = os.environ.get("HF_TOKEN", "")
    if not secret:
        raise ValueError("HF_TOKEN_environment_variable_required")
    report = repair_dataset(args.input_dir, args.output_dir, args.report_json, secret)
    print(json.dumps({
        "status": report["status"],
        "row_counts": report["row_counts"],
        "repair_counts": report["repair_counts"],
        "plaintext_parts_emitted": False,
        "raw_market_values_emitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
