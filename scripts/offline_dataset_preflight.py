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
TIMESTAMP_NAMES = ("timestamp_epoch", "timestamp", "datetime", "date_time", "timestamp_ist")
ROWTYPE_NAMES = ("row_type", "instrument_type", "record_type", "data_type")
KEY_GROUPS = (
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
        expected_rows: int, expected_cols: int) -> dict:
    if not path.is_file():
        raise ValueError("INPUT_FILE_NOT_FOUND")
    digest = sha256_file(path)
    if expected_sha and digest != expected_sha:
        raise ValueError("INPUT_SHA256_MISMATCH")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    nulls = Counter()
    timestamp_min = timestamp_max = None
    timestamp_parse_errors = 0
    header = None
    width_errors = 0
    duplicate_keys = None
    key_cols = None
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
            key_cols = next(
                (tuple(indexes[n] for n in group)
                 for group in KEY_GROUPS if all(n in indexes for n in group)),
                None,
            )
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
                    key_values = [row[i].strip() for i in key_cols]
                    # Incomplete identifiers are not treated as unique or duplicate.
                    if all(key_values):
                        key = json.dumps(key_values, separators=(",", ":"), ensure_ascii=False)
                        try:
                            db.execute("INSERT INTO keys_seen(k) VALUES (?)", (key,))
                        except sqlite3.IntegrityError:
                            duplicate_keys += 1
                if counts["data_rows"] % 250_000 == 0 and db is not None:
                    db.commit()

        if width_errors:
            raise ValueError("ROW_WIDTH_MISMATCH")
        if counts["data_rows"] != expected_rows:
            raise ValueError("ROW_COUNT_MISMATCH")
        if db is not None:
            db.commit()

        duplicate_status = (
            "NOT_ESTIMABLE_NO_RECOGNIZED_COMPOSITE_KEY" if not key_cols
            else ("FAIL_DUPLICATE_KEYS_FOUND" if duplicate_keys else "PASS")
        )
        overall_status = (
            "PREFLIGHT_FAIL_DUPLICATE_KEYS" if key_cols and duplicate_keys
            else "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS"
        )
        report = {
            "status": overall_status,
            "file_name": path.name,
            "file_size_bytes": path.stat().st_size,
            "sha256": digest,
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
            "duplicate_key_fields": [header[i] for i in key_cols] if key_cols else [],
            "duplicate_key_count": duplicate_keys,
            "limitations": [
                "This is structural preflight only, not modelling-readiness approval.",
                "Unparseable timestamps and incomplete composite identifiers are reported but not repaired.",
                "This scan does not establish session-calendar correctness, target validity, leakage safety, exact spot joins, or OHLC semantics.",
                "No market row values are emitted in this report."
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
    parser.add_argument("--expected-sha256", default=EXPECTED_SHA256)
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS)
    parser.add_argument("--expected-columns", type=int, default=EXPECTED_COLUMNS)
    args = parser.parse_args()
    try:
        report = run(Path(args.input), Path(args.report), args.expected_sha256,
                     args.expected_rows, args.expected_columns)
        print(json.dumps({key: report[key] for key in (
            "status", "sha256", "data_rows", "columns", "gzip_integrity",
            "duplicate_key_check", "timestamp_parse_errors")}, sort_keys=True))
        if report["status"] != "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS":
            sys.exit(2)
    except (OSError, EOFError, gzip.BadGzipFile, csv.Error, ValueError, sqlite3.Error) as exc:
        code = str(exc) if str(exc) else type(exc).__name__
        print(json.dumps({"status": "FAIL_CLOSED", "error_code": code}, sort_keys=True), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
