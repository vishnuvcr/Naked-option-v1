#!/usr/bin/env python3
"""Offline semantic audit for the encrypted NIFTY composite dataset.

Reads only already-decrypted local monthly CSV.GZ parts. Emits aggregate
counts and quality diagnostics; never writes or prints individual market rows.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import math
import pathlib
import sqlite3
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc
PRICE_GROUPS = (
    ("option_open", "option_high", "option_low", "option_close"),
    ("nifty_open", "nifty_high", "nifty_low", "nifty_close"),
)
NUMERIC_FIELDS = (
    "timestamp_epoch", "returned_strike", "option_open", "option_high",
    "option_low", "option_close", "option_volume", "open_interest",
    "implied_volatility", "rolling_spot", "nifty_open", "nifty_high",
    "nifty_low", "nifty_close", "nifty_volume", "time_to_expiry_years",
    "risk_free_rate_decimal", "dividend_yield_decimal", "delta", "gamma",
    "theta_per_day", "vega_per_1pct_iv", "rho_per_1pct_rate",
)
FEATURE_FIELDS = (
    "option_open", "option_high", "option_low", "option_close",
    "option_volume", "open_interest", "implied_volatility", "rolling_spot",
    "nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume",
    "expiry_date", "time_to_expiry_years", "delta", "gamma", "theta_per_day",
    "vega_per_1pct_iv", "rho_per_1pct_rate",
)
ROW_KEY_FIELDS = (
    "timestamp_epoch", "row_type", "source_request_id", "expiry_flag",
    "expiry_code", "requested_relative_strike", "option_type",
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("top_level_json_object_required")
    return obj


def _decimal(value: str) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = Decimal(value.strip())
    except (InvalidOperation, ValueError):
        raise ValueError("numeric_value_unparseable") from None
    if not parsed.is_finite():
        raise ValueError("numeric_value_nonfinite")
    return parsed


def _parse_iso(value: str) -> dt.datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp_timezone_missing")
    return parsed


def _check_ohlc(row: dict[str, str], fields: tuple[str, ...], key: str,
                counters: Counter[str], empty_counter: Counter[str]) -> None:
    try:
        vals = [_decimal(row.get(name, "")) for name in fields]
    except ValueError as exc:
        counters[key + "_" + str(exc)] += 1
        return
    if any(v is None for v in vals):
        counters[key + "_missing"] += 1
        empty_counter[key + "_missing_rows"] += 1
        return
    op, hi, lo, cl = vals
    if min(vals) <= 0 or hi < max(op, cl) or lo > min(op, cl) or lo > hi:
        counters[key] += 1


def audit_dataset(input_dir: pathlib.Path, output_path: pathlib.Path,
                  sqlite_path: pathlib.Path) -> dict[str, Any]:
    manifest_path = input_dir / "dataset_manifest.json"
    manifest = _read_json(manifest_path)
    columns = manifest.get("columns")
    parts = manifest.get("parts")
    if not isinstance(columns, list) or not columns or not isinstance(parts, list):
        raise ValueError("manifest_columns_or_parts_invalid")
    if manifest.get("download_bundle_contains_encrypted_data_only") is not True:
        raise ValueError("manifest_bundle_scope_marker_invalid")
    expected_cols = set(columns)
    missing_cols = sorted((set(FEATURE_FIELDS) | set(ROW_KEY_FIELDS)) - expected_cols)
    if missing_cols:
        raise ValueError("manifest_required_columns_missing")

    counts: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    invalid: Counter[str] = Counter()
    row_type_counts: Counter[str] = Counter()
    join_status_counts: Counter[str] = Counter()
    flag_counts: Counter[str] = Counter()
    spot_volume_flagged_rows = 0
    actual_month_rows: Counter[str] = Counter()
    actual_month_types: dict[str, Counter[str]] = {}
    session_dates: set[str] = set()
    option_sessions: set[str] = set()
    spot_sessions: set[str] = set()
    timestamp_epoch_min: int | None = None
    timestamp_epoch_max: int | None = None
    duplicate_option_keys = 0
    duplicate_spot_epochs = 0
    malformed_rows = 0
    first_fatal_schema_error = ""

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()
    db = sqlite3.connect(str(sqlite_path))
    try:
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute("PRAGMA temp_store=FILE")
        db.execute("""CREATE TABLE row_keys (
          ts INTEGER NOT NULL, typ TEXT NOT NULL, req TEXT NOT NULL,
          eflag TEXT NOT NULL, ecode TEXT NOT NULL, strike TEXT NOT NULL,
          opt TEXT NOT NULL,
          UNIQUE(ts, typ, req, eflag, ecode, strike, opt)
        )""")
        db.execute("CREATE TABLE spot_epochs (ts INTEGER PRIMARY KEY)")
        key_cursor = db.cursor()
        epoch_cursor = db.cursor()
        pending = 0
        manifest_parts = {str(p.get("file", "")): p for p in parts}
        if len(manifest_parts) != len(parts):
            raise ValueError("manifest_duplicate_or_blank_part_filename")
        if any(pathlib.Path(name).name != name or not name.endswith(".csv.gz.enc")
               for name in manifest_parts):
            raise ValueError("manifest_part_filename_invalid")

        for encrypted_name, part_meta in sorted(manifest_parts.items()):
            plain_name = encrypted_name.removesuffix(".enc")
            plain_path = input_dir / plain_name
            if not plain_path.is_file():
                raise ValueError("decrypted_month_part_missing")
            month = plain_name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz")
            if len(month) != 7 or month[4] != "-":
                raise ValueError("monthly_part_name_invalid")
            month_count = 0
            month_types: Counter[str] = Counter()
            with gzip.open(plain_path, "rt", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                try:
                    header = next(reader)
                except StopIteration:
                    raise ValueError("decrypted_csv_empty") from None
                if header != columns:
                    raise ValueError("decrypted_csv_schema_mismatch")
                for raw in reader:
                    if len(raw) != len(columns):
                        malformed_rows += 1
                        invalid["csv_row_width_mismatch"] += 1
                        continue
                    row = dict(zip(columns, raw))
                    counts["total_rows"] += 1
                    month_count += 1
                    actual_month_rows[month] += 1
                    typ = row.get("row_type", "")
                    row_type_counts[typ or "(blank)"] += 1
                    month_types[typ or "(blank)"] += 1
                    if typ not in {"OPTION", "SPOT"}:
                        invalid["unknown_row_type"] += 1
                        continue

                    try:
                        epoch_num = _decimal(row.get("timestamp_epoch", ""))
                        if epoch_num is None or epoch_num != epoch_num.to_integral_value():
                            raise ValueError("timestamp_epoch_not_integer")
                        epoch = int(epoch_num)
                        if epoch < 1600000000 or epoch > 1900000000:
                            invalid["timestamp_epoch_out_of_range"] += 1
                        utc_from_epoch = dt.datetime.fromtimestamp(epoch, tz=UTC)
                        ist_from_epoch = utc_from_epoch.astimezone(IST)
                        ts_utc = _parse_iso(row.get("timestamp_utc", ""))
                        ts_ist = _parse_iso(row.get("timestamp_ist", ""))
                        if int(ts_utc.astimezone(UTC).timestamp()) != epoch:
                            invalid["timestamp_utc_epoch_mismatch"] += 1
                        if abs((ts_utc.astimezone(UTC) - utc_from_epoch).total_seconds()) > 1:
                            invalid["timestamp_utc_value_mismatch"] += 1
                        if abs((ts_ist.astimezone(IST) - ist_from_epoch).total_seconds()) > 1:
                            invalid["timestamp_ist_value_mismatch"] += 1
                        if row.get("session_date", "") != ist_from_epoch.date().isoformat():
                            invalid["session_date_mismatch"] += 1
                        if ist_from_epoch.strftime("%Y-%m") != month:
                            invalid["row_in_wrong_month_part"] += 1
                        session = ist_from_epoch.date().isoformat()
                        session_dates.add(session)
                        (option_sessions if typ == "OPTION" else spot_sessions).add(session)
                        timestamp_epoch_min = epoch if timestamp_epoch_min is None else min(timestamp_epoch_min, epoch)
                        timestamp_epoch_max = epoch if timestamp_epoch_max is None else max(timestamp_epoch_max, epoch)
                    except (ValueError, OverflowError, OSError):
                        invalid["timestamp_parse_or_consistency_error"] += 1
                        epoch = None

                    # Audit numeric representations without materializing prices in the report.
                    decimals: dict[str, Decimal | None] = {}
                    for field in NUMERIC_FIELDS:
                        try:
                            value = _decimal(row.get(field, ""))
                            decimals[field] = value
                            if value is None and field in FEATURE_FIELDS:
                                applicable = (
                                    typ == "OPTION"
                                    or (typ == "SPOT" and field in {
                                        "nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"
                                    })
                                )
                                if applicable:
                                    missing[typ.lower() + ":" + field] += 1
                            elif value < 0 and field in {"option_volume", "open_interest", "nifty_volume", "time_to_expiry_years"}:
                                invalid[field + "_negative"] += 1
                        except ValueError as exc:
                            invalid[field + "_" + str(exc)] += 1

                    if typ == "OPTION":
                        counts["option_rows"] += 1
                        _check_ohlc(row, ("option_open", "option_high", "option_low", "option_close"),
                                    "option_ohlc_invalid", invalid, missing)
                        status = row.get("spot_join_status", "") or "(blank)"
                        join_status_counts[status] += 1
                        if status == "EXACT_TIMESTAMP_MATCH":
                            if all((row.get(f, "").strip() for f in
                                    ("nifty_open", "nifty_high", "nifty_low", "nifty_close"))):
                                _check_ohlc(row, ("nifty_open", "nifty_high", "nifty_low", "nifty_close"),
                                            "matched_nifty_ohlc_invalid", invalid, missing)
                            else:
                                invalid["matched_spot_row_missing_ohlc"] += 1
                        elif status == "NO_EXACT_TIMESTAMP_SPOT_MATCH":
                            if any(row.get(f, "").strip() for f in
                                   ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume")):
                                invalid["unmatched_option_has_spot_values"] += 1
                        else:
                            invalid["option_join_status_unknown_or_blank"] += 1
                        for field in ("option_volume", "open_interest"):
                            val = decimals.get(field)
                            if val is None:
                                # Count separately from general missingness to avoid silent feature fill.
                                missing["option_rows_" + field] += 1
                        if row.get("option_type", "") not in {"CE", "PE"}:
                            invalid["option_type_invalid"] += 1
                        if row.get("data_quality_flags", "").strip():
                            for flag in set(row["data_quality_flags"].split("|")):
                                if flag:
                                    flag_counts[flag] += 1
                    else:
                        counts["spot_rows"] += 1
                        _check_ohlc(row, ("nifty_open", "nifty_high", "nifty_low", "nifty_close"),
                                    "spot_ohlc_invalid", invalid, missing)
                        if "SPOT_VOLUME_MISSING_OR_MISALIGNED" in row.get("data_quality_flags", ""):
                            spot_volume_flagged_rows += 1
                        if not row.get("timestamp_utc", "").strip() or not row.get("session_date", "").strip():
                            invalid["spot_timestamp_fields_missing"] += 1
                        if epoch is not None:
                            before = epoch_cursor.execute(
                                "INSERT OR IGNORE INTO spot_epochs(ts) VALUES (?)", (epoch,)
                            ).rowcount
                            if before == 0:
                                duplicate_spot_epochs += 1

                    # Mirror the collector's official row-key definition for duplicates.
                    if epoch is not None:
                        key = (
                            epoch, typ, row.get("source_request_id", ""),
                            row.get("expiry_flag", ""), row.get("expiry_code", ""),
                            row.get("requested_relative_strike", ""), row.get("option_type", ""),
                        )
                        inserted = key_cursor.execute(
                            "INSERT OR IGNORE INTO row_keys VALUES (?,?,?,?,?,?,?)", key
                        ).rowcount
                        if inserted == 0:
                            duplicate_option_keys += 1
                        pending += 1
                        if pending >= 10000:
                            db.commit()
                            pending = 0
                    if month_count % 250000 == 0:
                        # A progress-free scanner: no row values or sampled records are emitted.
                        pass
            actual_month_types[month] = month_types
            counts["manifest_expected_rows"] += int(part_meta.get("row_count", -1))
            if month_count != int(part_meta.get("row_count", -1)):
                invalid["monthly_row_count_mismatch"] += 1
            if int(manifest.get("row_count_by_month", {}).get(month, -1)) != month_count:
                invalid["monthly_manifest_map_mismatch"] += 1
        db.commit()

        expected_summary = manifest.get("dataset_summary", {})
        for key, actual_key in (("original_rows_options", "option_rows"),
                                ("rows_options", "option_rows"),
                                ("rows_spot", "spot_rows")):
            expected = expected_summary.get(key)
            if expected is not None and int(expected) != counts[actual_key]:
                invalid["dataset_summary_" + key + "_mismatch"] += 1
        if counts["total_rows"] != counts["manifest_expected_rows"]:
            invalid["total_rows_vs_part_manifest_mismatch"] += 1
        if counts["total_rows"] != counts["option_rows"] + counts["spot_rows"]:
            invalid["row_type_total_mismatch"] += 1

        expected_matched = int(expected_summary.get("spot_join_matched", -1))
        expected_missing = int(expected_summary.get("spot_join_missing", -1))
        actual_matched = join_status_counts.get("EXACT_TIMESTAMP_MATCH", 0)
        actual_missing = join_status_counts.get("NO_EXACT_TIMESTAMP_SPOT_MATCH", 0)
        if expected_matched >= 0 and expected_matched != actual_matched:
            invalid["spot_join_matched_manifest_mismatch"] += 1
        if expected_missing >= 0 and expected_missing != actual_missing:
            invalid["spot_join_missing_manifest_mismatch"] += 1
        no_spot_sessions = sorted(option_sessions - spot_sessions)
        expected_session_count = expected_summary.get("observed_trading_session_count")
        if expected_session_count is not None and len(session_dates) != int(expected_session_count):
            invalid["observed_session_count_mismatch"] += 1
        unexpected_join_statuses = {
            k: v for k, v in join_status_counts.items()
            if k not in {"EXACT_TIMESTAMP_MATCH", "NO_EXACT_TIMESTAMP_SPOT_MATCH"}
        }
        structural_keys = [
            "csv_row_width_mismatch", "unknown_row_type", "timestamp_epoch_not_integer",
            "timestamp_epoch_out_of_range", "timestamp_utc_epoch_mismatch",
            "timestamp_utc_value_mismatch", "timestamp_ist_value_mismatch",
            "session_date_mismatch", "row_in_wrong_month_part",
            "timestamp_parse_or_consistency_error", "option_ohlc_invalid",
            "matched_nifty_ohlc_invalid", "spot_ohlc_invalid",
            "matched_spot_row_missing_ohlc", "unmatched_option_has_spot_values",
            "option_join_status_unknown_or_blank", "option_type_invalid",
            "duplicate_spot_epochs", "monthly_row_count_mismatch",
            "monthly_manifest_map_mismatch", "dataset_summary_original_rows_options_mismatch",
            "dataset_summary_rows_options_mismatch", "dataset_summary_rows_spot_mismatch",
            "total_rows_vs_part_manifest_mismatch", "row_type_total_mismatch",
            "spot_join_matched_manifest_mismatch", "spot_join_missing_manifest_mismatch",
        ]
        # Duplicate counters are held separately for clarity; the database enforces the
        # collector's composite key across all month parts.
        critical_counts = {k: int(invalid[k]) for k in structural_keys if invalid[k]}
        critical_counts["duplicate_option_row_keys"] = duplicate_option_keys
        critical_counts["duplicate_spot_timestamps"] = duplicate_spot_epochs
        semantic_error_count = sum(critical_counts.values())
        report: dict[str, Any] = {
            "schema_version": 1,
            "audit_type": "OFFLINE_DECRYPTED_VALUE_SEMANTIC_AUDIT",
            "status": "PASS_WITH_COVERAGE_RESTRICTIONS" if semantic_error_count == 0 else "FAIL",
            "dataset_id": manifest.get("dataset_id"),
            "archive_decryption": "SUCCESS",
            "part_count": len(parts),
            "rows": {
                "total": int(counts["total_rows"]),
                "option": int(counts["option_rows"]),
                "spot": int(counts["spot_rows"]),
            },
            "manifest_reconciliation": {
                "part_row_sum": int(counts["manifest_expected_rows"]),
                "row_counts_match": counts["total_rows"] == counts["manifest_expected_rows"],
                "monthly_counts_match": invalid["monthly_row_count_mismatch"] == 0 and invalid["monthly_manifest_map_mismatch"] == 0,
                "summary_counts_match": (
                    counts["option_rows"] == int(expected_summary.get("rows_options", counts["option_rows"])) and
                    counts["spot_rows"] == int(expected_summary.get("rows_spot", counts["spot_rows"]))
                ),
            },
            "timestamps": {
                "unique_session_dates": len(session_dates),
                "option_session_dates": len(option_sessions),
                "spot_session_dates": len(spot_sessions),
                "option_sessions_without_any_spot_row": len(no_spot_sessions),
                "manifest_observed_session_count": expected_session_count,
                "epoch_range_present": timestamp_epoch_min is not None and timestamp_epoch_max is not None,
            },
            "spot_join": {
                "join_status_counts": dict(sorted(join_status_counts.items())),
                "manifest_matched": expected_matched,
                "observed_matched": int(actual_matched),
                "manifest_missing": expected_missing,
                "observed_missing": int(actual_missing),
                "unexpected_join_status_counts": unexpected_join_statuses,
            },
            "duplicates": {
                "collector_composite_key_duplicates": int(duplicate_option_keys),
                "spot_timestamp_duplicates": int(duplicate_spot_epochs),
            },
            "row_integrity": {
                "timestamp_and_schema_findings": {
                    key: int(value) for key, value in invalid.items()
                    if "timestamp" in key or "schema" in key or key in {"csv_row_width_mismatch", "unknown_row_type", "row_in_wrong_month_part", "session_date_mismatch"}
                },
                "critical_findings": critical_counts,
                "semantic_error_count": int(semantic_error_count),
            },
            "missing_values": {
                key: int(value) for key, value in sorted(missing.items())
            },
            "negative_or_malformed_numeric_counts": {
                key: int(value) for key, value in sorted(invalid.items())
                if "negative" in key or "unparseable" in key or "nonfinite" in key
            },
            "quality_flag_row_occurrence_counts": dict(sorted(flag_counts.items())),
            "known_coverage_limitations": {
                "manifest_historical_option_grid": expected_summary.get("historical_option_request_grid_status"),
                "manifest_spot_recovery": expected_summary.get("spot_recovery_status"),
                "manifest_gapfill_failed_requests": expected_summary.get("gapfill_request_count_failed"),
                "manifest_gapfill_planned_requests": expected_summary.get("gapfill_request_count_planned"),
                "spot_rows_with_missing_or_misaligned_volume_flag": int(spot_volume_flagged_rows),
                "unmatched_option_rows": int(actual_missing),
                "option_sessions_without_spot_rows": len(no_spot_sessions),
            },
            "sensitive_market_values_in_report": False,
            "plaintext_uploaded": False,
            "live_source_requests_made": False,
            "model_fitting_or_scoring_performed": False,
            "holdout_accessed": False,
            "strategy_or_pnl_tested": False,
            "permission_conclusion": "NO_MODEL_AUTHORIZATION_FROM_DATA_AUDIT",
        }
        if semantic_error_count == 0:
            report["readiness_conclusion"] = "STRUCTURAL_CHECKS_PASS_WITH_RECORDED_COVERAGE_RESTRICTIONS; REQUIRE SEPARATE MODEL-GATE REVIEW"
        else:
            report["readiness_conclusion"] = "STRUCTURAL_CHECKS_FAIL; DO NOT FIT UNTIL FINDINGS ARE EXPLAINED AND TESTER-REVIEWED"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
    finally:
        db.close()
        try:
            sqlite_path.unlink()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=pathlib.Path,
                        help="Directory containing manifest and decrypted *.csv.gz monthly parts.")
    parser.add_argument("--output-json", required=True, type=pathlib.Path,
                        help="Sanitized aggregate report destination.")
    parser.add_argument("--sqlite-temp", required=True, type=pathlib.Path,
                        help="Ephemeral path for duplicate-key checking; deleted before exit.")
    args = parser.parse_args()
    try:
        report = audit_dataset(args.input_dir.resolve(), args.output_json.resolve(), args.sqlite_temp.resolve())
        print(json.dumps({
            "audit_status": report["status"],
            "rows": report.get("rows", {}),
            "semantic_error_count": report.get("row_integrity", {}).get("semantic_error_count"),
            "report_path": str(args.output_json),
            "plaintext_values_emitted": False,
        }, sort_keys=True))
        return 0 if report["status"] != "FAIL" else 2
    except Exception as exc:
        safe = {
            "schema_version": 1,
            "audit_type": "OFFLINE_DECRYPTED_VALUE_SEMANTIC_AUDIT",
            "status": "AUDIT_ERROR",
            "error_class": type(exc).__name__,
            "error_code": str(exc)[:120] if str(exc) and all(ord(c) >= 32 for c in str(exc)) else "unspecified",
            "plaintext_values_emitted": False,
            "live_source_requests_made": False,
            "permission_conclusion": "NO_MODEL_AUTHORIZATION_FROM_DATA_AUDIT",
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(safe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"audit_status": "AUDIT_ERROR", "error_class": type(exc).__name__,
                          "report_path": str(args.output_json), "plaintext_values_emitted": False}, sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
