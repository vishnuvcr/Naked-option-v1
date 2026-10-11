#!/usr/bin/env python3
"""Bounded-memory structural preflight for the verified local NIFTY CSV.GZ."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_ROWS = 8_999_865
EXPECTED_COLUMNS = 47
EXPECTED_SHA256 = "f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5"
EXPECTED_UNCOMPRESSED_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
EXPECTED_UNCOMPRESSED_BYTES = 4_747_892_392
TIMESTAMP_NAMES = ("timestamp_epoch", "timestamp", "datetime", "date_time", "timestamp_ist")
ROWTYPE_NAMES = ("row_type", "instrument_type", "record_type", "data_type")
KEY_GROUPS = (
    # Canonical groups for the actual repaired composite CSV schema.
    ("timestamp_epoch", "row_type", "underlying", "expiry_code", "returned_strike", "option_type"),
    ("timestamp_epoch", "row_type", "underlying"),
    # Compatibility groups retained for older/synthetic schemas.
    ("timestamp_epoch", "instrument_type", "symbol", "expiry", "strike", "option_type"),
    ("timestamp_epoch", "row_type", "symbol", "expiry", "strike", "option_type"),
    ("timestamp_epoch", "instrument_type", "security_id"),
    ("timestamp_epoch", "row_type", "security_id"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_gzip_payload(path: Path) -> tuple[str, int]:
    """Hash decompressed CSV bytes, independent of gzip container metadata."""
    digest = hashlib.sha256()
    size_bytes = 0
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
            size_bytes += len(block)
    return digest.hexdigest(), size_bytes


def normalize_timestamp(value: str, column_name: str):
    """Return sortable numeric seconds where possible; None for blank/unparseable values."""
    value = value.strip()
    if not value:
        return None
    if column_name.strip().lower() == "timestamp_epoch":
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except ValueError:
            return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def run(path: Path, report_path: Path, expected_sha: str,
        expected_rows: int, expected_cols: int,
        expected_uncompressed_sha: str = "",
        expected_uncompressed_bytes: int = 0) -> dict:
    if not path.is_file():
        raise ValueError("INPUT_FILE_NOT_FOUND")
    digest = sha256_file(path)
    compressed_match = digest == expected_sha if expected_sha else None
    # Gzip creation timestamps can change the compressed SHA when the exact same
    # monthly gzip parts are re-merged. Verify the content SHA separately.
    uncompressed_digest, uncompressed_bytes = sha256_gzip_payload(path)
    uncompressed_match = (
        uncompressed_digest == expected_uncompressed_sha
        if expected_uncompressed_sha else None
    )
    uncompressed_size_match = (
        uncompressed_bytes == expected_uncompressed_bytes
        if expected_uncompressed_bytes else None
    )
    if expected_sha and not compressed_match and not expected_uncompressed_sha:
        raise ValueError("INPUT_SHA256_MISMATCH")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    nulls = Counter()
    timestamp_min = timestamp_max = None
    timestamp_parse_errors = 0
    header = None
    width_errors = 0
    duplicate_keys = None
    incomplete_key_rows = 0
    key_group_row_counts = Counter()
    key_cols = None
    key_batch = []
    db = None
    db_path = None
    try:
        # Reading to EOF validates the gzip CRC/trailer as well as CSV syntax.
        with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            try:
                header = next(reader)
            except StopIteration as exc:
                raise ValueError("EMPTY_CSV") from exc
            if len(header) != len(set(header)):
                raise ValueError("DUPLICATE_COLUMN_NAMES")
            if len(header) != expected_cols:
                raise ValueError("COLUMN_COUNT_MISMATCH")

            indexes = {name.strip().lower(): i for i, name in enumerate(header)}
            ts_col = next((indexes[n] for n in TIMESTAMP_NAMES if n in indexes), None)
            rowtype_col = next((indexes[n] for n in ROWTYPE_NAMES if n in indexes), None)
            key_cols = [
                (tuple(group), tuple(indexes[n] for n in group))
                for group in KEY_GROUPS if all(n in indexes for n in group)
            ] or None
            if key_cols:
                # SQLite keeps the duplicate index on disk rather than retaining all rows in RAM.
                db_path = report_path.with_name(report_path.name + ".sqlite.tmp")
                db = sqlite3.connect(str(db_path))
                db.execute("CREATE TABLE keys_seen (k TEXT PRIMARY KEY)")
                duplicate_keys = 0
                db.commit()

            for row in reader:
                counts["data_rows"] += 1
                if len(row) != len(header):
                    width_errors += 1
                    continue

                for i, value in enumerate(row):
                    if value is None or not value.strip() or value.strip().lower() in ("nan", "null", "none"):
                        nulls[header[i]] += 1

                if rowtype_col is not None:
                    counts["row_type:" + (row[rowtype_col].strip() or "MISSING")] += 1

                if ts_col is not None:
                    raw_ts = row[ts_col].strip()
                    normalized = normalize_timestamp(raw_ts, header[ts_col])
                    if raw_ts and normalized is None:
                        timestamp_parse_errors += 1
                    elif normalized is not None:
                        timestamp_min = normalized if timestamp_min is None else min(timestamp_min, normalized)
                        timestamp_max = normalized if timestamp_max is None else max(timestamp_max, normalized)

                if key_cols and db is not None:
                    # Select the first usable key schema per row. For example, spot rows
                    # may lack option expiry/strike/type but still have a security_id key.
                    selected_key = None
                    for group_number, (group_names, column_indexes) in enumerate(key_cols):
                        # On the repaired schema, OPTION and SPOT rows must use their
                        # own key definition; an incomplete OPTION key must not fall
                        # back to the shorter SPOT key.
                        if rowtype_col is not None and header[rowtype_col].strip().lower() == "row_type":
                            row_kind = row[rowtype_col].strip().upper()
                            if row_kind == "OPTION" and "expiry_code" not in group_names:
                                continue
                            if row_kind == "SPOT" and tuple(group_names) != ("timestamp_epoch", "row_type", "underlying"):
                                continue
                        candidate_values = []
                        complete = True
                        for column_index in column_indexes:
                            value = row[column_index].strip()
                            column_name = header[column_index].strip().lower()
                            if column_name == "timestamp_epoch":
                                normalized_epoch = normalize_timestamp(value, header[column_index])
                                if normalized_epoch is None:
                                    complete = False
                                    break
                                value = format(normalized_epoch, ".15g")
                            elif column_name == "returned_strike":
                                try:
                                    normalized_strike = float(value)
                                except ValueError:
                                    complete = False
                                    break
                                if not math.isfinite(normalized_strike):
                                    complete = False
                                    break
                                value = format(normalized_strike, ".15g")
                            elif column_name in ("row_type", "instrument_type", "option_type", "underlying", "symbol"):
                                value = value.upper()
                            if not value:
                                complete = False
                                break
                            candidate_values.append(value)
                        if complete:
                            selected_key = (group_number, candidate_values)
                            break
                    if selected_key is None:
                        incomplete_key_rows += 1
                    else:
                        group_number, candidate_values = selected_key
                        key_group_row_counts[group_number] += 1
                        key = json.dumps([group_number, *candidate_values], separators=(",", ":"), ensure_ascii=False)
                        key_batch.append((key,))
                        if len(key_batch) >= 10_000:
                            before = db.total_changes
                            db.executemany("INSERT OR IGNORE INTO keys_seen(k) VALUES (?)", key_batch)
                            duplicate_keys += len(key_batch) - (db.total_changes - before)
                            key_batch.clear()
                if counts["data_rows"] % 250_000 == 0 and db is not None:
                    if key_batch:
                        before = db.total_changes
                        db.executemany("INSERT OR IGNORE INTO keys_seen(k) VALUES (?)", key_batch)
                        duplicate_keys += len(key_batch) - (db.total_changes - before)
                        key_batch.clear()
                    db.commit()

        if width_errors:
            raise ValueError("ROW_WIDTH_MISMATCH")
        if counts["data_rows"] != expected_rows:
            raise ValueError("ROW_COUNT_MISMATCH")
        if db is not None:
            if key_batch:
                before = db.total_changes
                db.executemany("INSERT OR IGNORE INTO keys_seen(k) VALUES (?)", key_batch)
                duplicate_keys += len(key_batch) - (db.total_changes - before)
                key_batch.clear()
            db.commit()

        if expected_uncompressed_sha and not uncompressed_match:
            duplicate_status = "NOT_EVALUATED_CONTENT_HASH_FAILED"
            overall_status = "PREFLIGHT_FAIL_UNCOMPRESSED_SHA256"
        elif expected_uncompressed_bytes and not uncompressed_size_match:
            duplicate_status = "NOT_EVALUATED_CONTENT_SIZE_FAILED"
            overall_status = "PREFLIGHT_FAIL_UNCOMPRESSED_SIZE"
        elif not key_cols:
            duplicate_status = "NOT_ESTIMABLE_NO_RECOGNIZED_COMPOSITE_KEY"
            overall_status = "PREFLIGHT_REVIEW_DUPLICATE_CHECK_NOT_ESTIMABLE"
        elif duplicate_keys:
            duplicate_status = "FAIL_DUPLICATE_KEYS_FOUND"
            overall_status = "PREFLIGHT_FAIL_DUPLICATE_KEYS"
        elif timestamp_parse_errors:
            duplicate_status = "PASS"
            overall_status = "PREFLIGHT_REVIEW_TIMESTAMP_PARSE_ERRORS"
        elif incomplete_key_rows:
            duplicate_status = "PARTIAL_INCOMPLETE_COMPOSITE_KEYS"
            overall_status = "PREFLIGHT_REVIEW_INCOMPLETE_COMPOSITE_KEYS"
        else:
            duplicate_status = "PASS"
            overall_status = "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS"
        report = {
            "status": overall_status,
            "file_name": path.name,
            "file_size_bytes": path.stat().st_size,
            "sha256": digest,
            "expected_compressed_sha256": expected_sha or None,
            "compressed_sha256_matches_expected": compressed_match,
            "uncompressed_sha256": uncompressed_digest,
            "expected_uncompressed_sha256": expected_uncompressed_sha or None,
            "uncompressed_sha256_matches_expected": uncompressed_match,
            "uncompressed_size_bytes": uncompressed_bytes,
            "expected_uncompressed_size_bytes": expected_uncompressed_bytes or None,
            "uncompressed_size_matches_expected": uncompressed_size_match,
            "gzip_integrity": "PASS",
            "data_rows": counts["data_rows"],
            "columns": len(header),
            "column_names": header,
            "recognized_timestamp_column": header[ts_col] if ts_col is not None else None,
            "timestamp_epoch_min": timestamp_min,
            "timestamp_epoch_max": timestamp_max,
            "timestamp_parse_errors": timestamp_parse_errors,
            "recognized_row_type_counts": {
                key.split(":", 1)[1]: value for key, value in counts.items()
                if key.startswith("row_type:")
            },
            "null_or_blank_counts_by_column": dict(nulls),
            "row_width_errors": width_errors,
            "duplicate_key_check": duplicate_status,
            "duplicate_key_fields": [[header[i] for i in column_indexes] for _group, column_indexes in key_cols] if key_cols else [],
            "duplicate_key_count": duplicate_keys,
            "incomplete_composite_key_rows": incomplete_key_rows,
            "key_group_row_counts": {
                str(group_number): {
                    "fields": [header[i] for i in key_cols[group_number][1]],
                    "rows_assigned": row_count,
                }
                for group_number, row_count in sorted(key_group_row_counts.items())
            } if key_cols else {},
            "limitations": [
                "This is structural preflight only, not modelling-readiness approval.",
                "Unparseable timestamps and incomplete composite identifiers are reported but not repaired.",
                "This scan does not establish session-calendar correctness, target validity, leakage safety, exact spot joins, or OHLC semantics.",
                "No market row values are emitted in this report.",
                "Gzip container metadata may change on recompression; the exact uncompressed CSV byte hash and byte count are checked separately."
            ]
        }
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
    finally:
        if db is not None:
            try:
                db.close()
            except sqlite3.Error:
                pass
        if db_path is not None:
            try:
                db_path.unlink(missing_ok=True)
            except OSError:
                # Never mask the primary audit failure; the report/tester must flag residue.
                pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--expected-sha256", default=EXPECTED_SHA256,
                        help="reference SHA-256 of the previously exported gzip container")
    parser.add_argument("--expected-uncompressed-sha256", default=EXPECTED_UNCOMPRESSED_SHA256)
    parser.add_argument("--expected-uncompressed-bytes", type=int, default=EXPECTED_UNCOMPRESSED_BYTES)
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS)
    parser.add_argument("--expected-columns", type=int, default=EXPECTED_COLUMNS)
    args = parser.parse_args()
    try:
        report = run(Path(args.input), Path(args.report), args.expected_sha256,
                     args.expected_rows, args.expected_columns,
                     args.expected_uncompressed_sha256, args.expected_uncompressed_bytes)
        print(json.dumps({key: report[key] for key in (
            "status", "sha256", "compressed_sha256_matches_expected",
            "uncompressed_sha256", "uncompressed_sha256_matches_expected",
            "uncompressed_size_bytes", "data_rows", "columns", "gzip_integrity",
            "duplicate_key_check", "timestamp_parse_errors")}, sort_keys=True))
        if report["status"] != "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS":
            sys.exit(2)
    except (OSError, EOFError, gzip.BadGzipFile, csv.Error, ValueError, sqlite3.Error) as exc:
        code = str(exc) if str(exc) else type(exc).__name__
        print(json.dumps({"status": "FAIL_CLOSED", "error_code": code}, sort_keys=True), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
