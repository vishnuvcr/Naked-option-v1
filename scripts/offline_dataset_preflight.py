#!/usr/bin/env python3
"""Bounded-memory audit for the verified local NIFTY CSV.GZ; emits metadata only."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, os, sqlite3, sys, tempfile
from collections import Counter
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
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def run(path: Path, report_path: Path, expected_sha: str, expected_rows: int, expected_cols: int) -> dict:
    if not path.is_file():
        raise ValueError("INPUT_FILE_NOT_FOUND")
    digest = sha256_file(path)
    if expected_sha and digest != expected_sha:
        raise ValueError("INPUT_SHA256_MISMATCH")
    # gzip CRC/trailer is verified by consuming the complete stream.
    report_path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    nulls = Counter()
    timestamp_min = timestamp_max = None
    header = None
    width_errors = 0
    samples = []
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("EMPTY_CSV")
        if len(header) != len(set(header)):
            raise ValueError("DUPLICATE_COLUMN_NAMES")
        if len(header) != expected_cols:
            raise ValueError("COLUMN_COUNT_MISMATCH")
        indexes = {name.strip().lower(): i for i, name in enumerate(header)}
        ts_col = next((indexes[n] for n in TIMESTAMP_NAMES if n in indexes), None)
        rowtype_col = next((indexes[n] for n in ROWTYPE_NAMES if n in indexes), None)
        # Use SQLite as a disk-backed duplicate detector only when a recognized
        # composite key is available; never retain market rows in memory.
        key_cols = next((tuple(indexes[n] for n in group) for group in KEY_GROUPS if all(n in indexes for n in group)), None)
        db = None
        duplicate_keys = None
        if key_cols:
            db_path = str(report_path) + ".sqlite.tmp"
            db = sqlite3.connect(db_path)
            db.execute("CREATE TABLE keys_seen (k TEXT PRIMARY KEY)")
            duplicate_keys = 0
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
                ts = row[ts_col].strip()
                if ts:
                    timestamp_min = ts if timestamp_min is None or ts < timestamp_min else timestamp_min
                    timestamp_max = ts if timestamp_max is None or ts > timestamp_max else timestamp_max
            if key_cols and db:
                key = json.dumps([row[i] for i in key_cols], separators=(",", ":"), ensure_ascii=False)
                try:
                    db.execute("INSERT INTO keys_seen(k) VALUES (?)", (key,))
                except sqlite3.IntegrityError:
                    duplicate_keys += 1
            if counts["data_rows"] % 250_000 == 0 and db:
                db.commit()
        if db:
            db.commit()
            db.close()
            os.unlink(str(report_path) + ".sqlite.tmp")
    if width_errors:
        raise ValueError("ROW_WIDTH_MISMATCH")
    if counts["data_rows"] != expected_rows:
        raise ValueError("ROW_COUNT_MISMATCH")
    report = {
        "status": "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS",
        "file_name": path.name,
        "file_size_bytes": path.stat().st_size,
        "sha256": digest,
        "gzip_integrity": "PASS",
        "data_rows": counts["data_rows"],
        "columns": len(header),
        "column_names": header,
        "recognized_timestamp_column": header[ts_col] if ts_col is not None else None,
        "timestamp_lexical_min": timestamp_min,
        "timestamp_lexical_max": timestamp_max,
        "recognized_row_type_counts": {k.split(":",1)[1]:v for k,v in counts.items() if k.startswith("row_type:")},
        "null_or_blank_counts_by_column": dict(nulls),
        "row_width_errors": width_errors,
        "duplicate_key_check": "PASS" if key_cols else "NOT_ESTIMABLE_NO_RECOGNIZED_COMPOSITE_KEY",
        "duplicate_key_fields": [header[i] for i in key_cols] if key_cols else [],
        "duplicate_key_count": duplicate_keys,
        "limitations": [
            "This is structural preflight only, not modelling-readiness approval.",
            "No target labels, feature eligibility, leakage safety, spot joins, or OHLC semantics are inferred by this generic CSV scan.",
            "No market row values are emitted in this report."
        ]
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--expected-sha256", default=EXPECTED_SHA256)
    p.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS)
    p.add_argument("--expected-columns", type=int, default=EXPECTED_COLUMNS)
    a = p.parse_args()
    try:
        report = run(Path(a.input), Path(a.report), a.expected_sha256, a.expected_rows, a.expected_columns)
        print(json.dumps({k: report[k] for k in ("status","sha256","data_rows","columns","gzip_integrity","duplicate_key_check")}, sort_keys=True))
    except (OSError, EOFError, gzip.BadGzipFile, csv.Error, ValueError, sqlite3.Error) as exc:
        code = str(exc) if str(exc) else type(exc).__name__
        print(json.dumps({"status":"FAIL_CLOSED","error_code":code}, sort_keys=True), file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
