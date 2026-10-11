#!/usr/bin/env python3
"""Independent structural audit for an encrypted derived NIFTY dataset after repair.

Input is already-decrypted local monthly CSV.GZ parts. The output contains only
counts and quality categories; no market prices, volumes, request IDs, or row
samples are emitted. This is a validation step, not model authorization.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import pathlib
import sqlite3
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

OHLC_FIELDS = {
    "OPTION": ("option_open", "option_high", "option_low", "option_close"),
    "SPOT": ("nifty_open", "nifty_high", "nifty_low", "nifty_close"),
}
VOLUME_FIELDS = {"OPTION": "option_volume", "SPOT": "nifty_volume"}
SPOT_FIELDS = ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume")


def number(value: str | None) -> Decimal | None:
    if value is None or not str(value).strip():
        return None
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def ohlc_state(row: dict[str, str], fields: tuple[str, ...]) -> str:
    vals = [number(row.get(field, "")) for field in fields]
    if all(v is None for v in vals):
        return "ALL_MISSING"
    if any(v is None for v in vals):
        return "PARTIAL_MISSING"
    op, hi, lo, cl = vals
    if min(op, hi, lo, cl) <= 0 or hi < max(op, cl) or lo > min(op, cl) or hi < lo:
        return "INVALID"
    return "VALID"


def audit(input_dir: pathlib.Path, report_path: pathlib.Path, sqlite_path: pathlib.Path) -> dict[str, Any]:
    input_dir = input_dir.resolve()
    report_path = report_path.resolve()
    sqlite_path = sqlite_path.resolve()
    manifest_path = input_dir / "dataset_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("derived_manifest_missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_id = str(manifest.get("dataset_id", ""))
    if not dataset_id.endswith("_DERIVED_REPAIR_V1"):
        raise ValueError("derived_dataset_id_invalid")
    parts = manifest.get("parts")
    columns = manifest.get("columns")
    if not isinstance(parts, list) or not parts or not isinstance(columns, list):
        raise ValueError("derived_manifest_parts_or_columns_invalid")
    required = set(sum((list(v) for v in OHLC_FIELDS.values()), [])) | {
        "timestamp_epoch", "row_type", "session_date", "spot_join_status",
        "data_quality_flags", "option_volume", "nifty_volume"
    }
    if not required.issubset(set(columns)):
        raise ValueError("derived_manifest_required_columns_missing")

    expected_files = {str(p.get("file", "")): p for p in parts}
    if len(expected_files) != len(parts) or any(pathlib.Path(n).name != n for n in expected_files):
        raise ValueError("derived_manifest_part_names_invalid")
    monthly_files = sorted(input_dir.glob("nifty_1m_composite_*.csv.gz"))
    if {p.name for p in monthly_files} != {n.removesuffix(".enc") for n in expected_files}:
        raise ValueError("decrypted_monthly_file_set_mismatch")

    report_counts: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    month_rows: Counter[str] = Counter()
    month_types: dict[str, Counter[str]] = {}
    option_dates: set[str] = set()
    spot_dates: set[str] = set()
    weekend_flags = 0
    unknown_types = 0
    invalid_timestamps = 0
    partial_ohlc = 0
    invalid_ohlc = 0
    negative_volumes = 0
    nonfinite_values = 0
    unmatched_rows_with_values = 0
    exact_rows_without_spot = 0
    exact_join_mismatches = 0
    spot_epoch_duplicates = 0
    duplicate_keys = 0
    unknown_join_status = 0
    expected_matched = int(manifest.get("dataset_summary", {}).get("spot_join_matched", -1))
    expected_missing = int(manifest.get("dataset_summary", {}).get("spot_join_missing", -1))
    spot_lookup: dict[int, dict[str, str]] = {}

    # First pass: create exact-epoch standalone spot lookup and count spot rows.
    for part_path in monthly_files:
        month = part_path.name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz")
        with gzip.open(part_path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != columns:
                raise ValueError("derived_monthly_schema_mismatch")
            for row in reader:
                if row.get("row_type") != "SPOT":
                    continue
                epoch_num = number(row.get("timestamp_epoch", ""))
                if epoch_num is None or epoch_num != epoch_num.to_integral_value():
                    invalid_timestamps += 1
                    continue
                epoch = int(epoch_num)
                if epoch in spot_lookup:
                    spot_epoch_duplicates += 1
                    continue
                spot_lookup[epoch] = {field: row.get(field, "") or "" for field in SPOT_FIELDS}

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()
    db = sqlite3.connect(str(sqlite_path))
    try:
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute("""CREATE TABLE keys (
          ts INTEGER NOT NULL, typ TEXT NOT NULL, req TEXT NOT NULL,
          expiry_flag TEXT NOT NULL, expiry_code TEXT NOT NULL,
          strike TEXT NOT NULL, opt TEXT NOT NULL,
          UNIQUE(ts, typ, req, expiry_flag, expiry_code, strike, opt)
        )""")
        key_cursor = db.cursor()
        pending = 0
        for part_path in monthly_files:
            month = part_path.name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz")
            local = Counter()
            with gzip.open(part_path, "rt", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != columns:
                    raise ValueError("derived_monthly_schema_mismatch")
                for row in reader:
                    report_counts["total_rows"] += 1
                    month_rows[month] += 1
                    typ = row.get("row_type", "")
                    local[typ or "(blank)"] += 1
                    if typ not in {"OPTION", "SPOT"}:
                        unknown_types += 1
                        continue
                    if typ == "SPOT":
                        report_counts["spot_rows"] += 1
                    epoch_num = number(row.get("timestamp_epoch", ""))
                    epoch = None
                    if epoch_num is None or epoch_num != epoch_num.to_integral_value():
                        invalid_timestamps += 1
                    else:
                        epoch = int(epoch_num)
                    session = row.get("session_date", "") or ""
                    try:
                        day = dt.date.fromisoformat(session)
                        (option_dates if typ == "OPTION" else spot_dates).add(session)
                        if day.weekday() >= 5 and "REPAIR_WEEKEND_SESSION_REVIEW_REQUIRED" in row.get("data_quality_flags", ""):
                            weekend_flags += 1
                    except ValueError:
                        report_counts["invalid_session_date"] += 1

                    state = ohlc_state(row, OHLC_FIELDS[typ])
                    if state == "INVALID":
                        invalid_ohlc += 1
                        report_counts[typ.lower() + "_ohlc_invalid_nonblank"] += 1
                    elif state == "PARTIAL_MISSING":
                        partial_ohlc += 1
                        report_counts[typ.lower() + "_ohlc_partial_missing"] += 1
                    elif state == "ALL_MISSING":
                        missing[typ.lower() + "_ohlc_all_missing"] += 1

                    vol_field = VOLUME_FIELDS[typ]
                    vol = number(row.get(vol_field, ""))
                    raw_vol = row.get(vol_field, "") or ""
                    if raw_vol.strip() and vol is None:
                        nonfinite_values += 1
                        report_counts[typ.lower() + "_volume_nonfinite"] += 1
                    elif vol is not None and vol < 0:
                        negative_volumes += 1
                        report_counts[typ.lower() + "_volume_negative"] += 1
                    elif not raw_vol.strip():
                        missing[typ.lower() + "_volume_missing"] += 1

                    if typ == "OPTION":
                        report_counts["option_rows"] += 1
                        join_status = row.get("spot_join_status", "")
                        has_values = any((row.get(field, "") or "").strip() for field in SPOT_FIELDS)
                        if join_status == "NO_EXACT_TIMESTAMP_SPOT_MATCH":
                            report_counts["unmatched_option_rows"] += 1
                            if has_values:
                                unmatched_rows_with_values += 1
                            if epoch is not None and epoch in spot_lookup:
                                report_counts["unmatched_epoch_exists_in_spot_set"] += 1
                        elif join_status == "EXACT_TIMESTAMP_MATCH":
                            report_counts["matched_option_rows"] += 1
                            source = spot_lookup.get(epoch) if epoch is not None else None
                            if source is None:
                                exact_rows_without_spot += 1
                            else:
                                source_state = ohlc_state(source, SPOT_FIELDS[:4])
                                expected_ohlc = source if source_state == "VALID" else {f: "" for f in SPOT_FIELDS[:4]}
                                for field in SPOT_FIELDS[:4]:
                                    if (row.get(field, "") or "") != (expected_ohlc.get(field, "") or ""):
                                        exact_join_mismatches += 1
                                        break
                                expected_volume = source.get("nifty_volume", "") if number(source.get("nifty_volume", "")) is not None and number(source.get("nifty_volume", "")) >= 0 else ""
                                if (row.get("nifty_volume", "") or "") != (expected_volume or ""):
                                    exact_join_mismatches += 1
                        else:
                            unknown_join_status += 1
                    if epoch is not None:
                        key = (
                            epoch, typ, row.get("source_request_id", "") or "",
                            row.get("expiry_flag", "") or "", row.get("expiry_code", "") or "",
                            row.get("requested_relative_strike", "") or "", row.get("option_type", "") or "",
                        )
                        if key_cursor.execute("INSERT OR IGNORE INTO keys VALUES (?,?,?,?,?,?,?)", key).rowcount == 0:
                            duplicate_keys += 1
                        pending += 1
                        if pending >= 10000:
                            db.commit()
                            pending = 0
            month_types[month] = local
            part = expected_files[part_path.name + ".enc"]
            if month_rows[month] != int(part.get("row_count", -1)):
                report_counts["monthly_row_count_mismatch"] += 1
        db.commit()

        summary = manifest.get("dataset_summary", {})
        if expected_matched >= 0 and expected_matched != report_counts["matched_option_rows"]:
            report_counts["manifest_matched_join_count_mismatch"] += 1
        if expected_missing >= 0 and expected_missing != report_counts["unmatched_option_rows"]:
            report_counts["manifest_unmatched_join_count_mismatch"] += 1
        total_expected = sum(int(p.get("row_count", -1)) for p in parts)
        if report_counts["total_rows"] != total_expected:
            report_counts["manifest_total_row_count_mismatch"] += 1

        hard_failures = (
            invalid_ohlc + partial_ohlc + negative_volumes + nonfinite_values +
            unmatched_rows_with_values + exact_rows_without_spot + exact_join_mismatches +
            spot_epoch_duplicates + duplicate_keys + unknown_types + invalid_timestamps +
            unknown_join_status + report_counts["invalid_session_date"] +
            report_counts["monthly_row_count_mismatch"] +
            report_counts["manifest_matched_join_count_mismatch"] +
            report_counts["manifest_unmatched_join_count_mismatch"] +
            report_counts["manifest_total_row_count_mismatch"]
        )
        result = {
            "schema_version": 1,
            "audit_type": "INDEPENDENT_DERIVED_DATASET_POST_REPAIR_AUDIT",
            "status": "PASS_WITH_COVERAGE_RESTRICTIONS" if hard_failures == 0 else "FAIL",
            "dataset_id": dataset_id,
            "parent_artifact_id": manifest.get("parent_artifact_id", manifest.get("derived_from", {}).get("parent_artifact_id")),
            "row_counts": {
                "total": int(report_counts["total_rows"]),
                "option": int(report_counts["option_rows"]),
                "spot": int(report_counts["spot_rows"]),
                "expected_total_from_manifest": total_expected,
            },
            "join_counts": {
                "matched_option_rows": int(report_counts["matched_option_rows"]),
                "unmatched_option_rows": int(report_counts["unmatched_option_rows"]),
                "expected_matched_from_manifest": expected_matched,
                "expected_unmatched_from_manifest": expected_missing,
                "unmatched_rows_with_underlying_values": int(unmatched_rows_with_values),
                "exact_join_rows_missing_source_epoch": int(exact_rows_without_spot),
                "exact_join_field_mismatches": int(exact_join_mismatches),
                "unmatched_epochs_also_in_spot_set": int(report_counts["unmatched_epoch_exists_in_spot_set"]),
            },
            "quality_counts": {
                "nonblank_invalid_ohlc_rows": int(invalid_ohlc),
                "partial_ohlc_missing_rows": int(partial_ohlc),
                "negative_nonblank_volumes": int(negative_volumes),
                "nonfinite_nonblank_volumes": int(nonfinite_values),
                "duplicate_spot_epochs": int(spot_epoch_duplicates),
                "duplicate_composite_keys": int(duplicate_keys),
                "unknown_row_types": int(unknown_types),
                "invalid_timestamps": int(invalid_timestamps),
                "unknown_join_statuses": int(unknown_join_status),
                "invalid_session_dates": int(report_counts["invalid_session_date"]),
                "weekend_session_rows_flagged": int(weekend_flags),
                "all_missing_ohlc_rows": dict(sorted(missing.items())),
                "monthly_row_count_mismatches": int(report_counts["monthly_row_count_mismatch"]),
                "manifest_reconciliation_findings": {
                    k: int(v) for k, v in report_counts.items() if "mismatch" in k
                },
            },
            "coverage_limitations": {
                "unmatched_option_rows_retained": int(report_counts["unmatched_option_rows"]),
                "spot_rows": len(spot_lookup),
                "greeks_and_time_to_expiry_populated": False,
                "unmatched_rows_filled_or_interpolated": False,
            },
            "sensitive_values_emitted": False,
            "plaintext_uploaded": False,
            "source_rows_modified": False,
            "live_requests_made": False,
            "model_fitting_or_scoring_performed": False,
            "holdout_accessed": False,
            "strategy_or_pnl_tested": False,
            "permission_conclusion": "NO_MODEL_AUTHORIZATION_FROM_POST_REPAIR_AUDIT",
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    finally:
        db.close()
        try:
            sqlite_path.unlink()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=pathlib.Path)
    parser.add_argument("--output-json", required=True, type=pathlib.Path)
    parser.add_argument("--sqlite-temp", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        result = audit(args.input_dir, args.output_json, args.sqlite_temp)
        print(json.dumps({
            "status": result["status"],
            "row_counts": result["row_counts"],
            "quality_counts": result["quality_counts"],
            "sensitive_values_emitted": False,
        }, sort_keys=True))
        return 0 if result["status"] == "PASS_WITH_COVERAGE_RESTRICTIONS" else 2
    except Exception as exc:
        safe = {
            "schema_version": 1,
            "audit_type": "INDEPENDENT_DERIVED_DATASET_POST_REPAIR_AUDIT",
            "status": "AUDIT_ERROR",
            "error_class": type(exc).__name__,
            "error_code": str(exc)[:120],
            "sensitive_values_emitted": False,
            "live_requests_made": False,
            "permission_conclusion": "NO_MODEL_AUTHORIZATION_FROM_POST_REPAIR_AUDIT",
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(safe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "AUDIT_ERROR", "error_class": type(exc).__name__}, sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
