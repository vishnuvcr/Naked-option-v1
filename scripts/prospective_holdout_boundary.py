#!/usr/bin/env python3
"""Synthetic-only implementation of a prospective metadata boundary scanner.

There is intentionally no real-file CLI mode. The function accepts a path so
offline tests can exercise byte boundaries using temporary synthetic CSV files.
Application logic accesses only row type, timestamp epoch and session date.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

HORIZONS = (1, 2, 3, 5, 10)
TRAIN_FRACTION = 0.70
VALIDATION_END_FRACTION = 0.85


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_uncompressed_suffix(path: str | Path, start: int, compressed: bool) -> str:
    digest = hashlib.sha256()
    opener = gzip.open if compressed else open
    with opener(path, "rb") as stream:
        remaining = start
        while remaining:
            block = stream.read(min(1024 * 1024, remaining))
            if not block:
                raise ValueError("HOLDOUT_OFFSET_OUT_OF_RANGE")
            remaining -= len(block)
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_date(value: str) -> dt.date:
    parsed = dt.date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("SESSION_DATE_INVALID")
    return parsed


def _parse_record(raw: bytes, expected_columns: int) -> list[str]:
    if not raw.endswith(b"\n"):
        raise ValueError("RECORD_BOUNDARY_INVALID")
    try:
        line = raw.decode("utf-8").rstrip("\r\n")
        row = next(csv.reader([line], strict=True))
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise ValueError("CSV_RECORD_INVALID") from exc
    if len(row) != expected_columns:
        raise ValueError("CSV_ROW_WIDTH_INVALID")
    return row


def scan_metadata_file(
    path: str | Path,
    *,
    expected_columns: int,
    column_map: Mapping[str, str],
    row_type_values: Mapping[str, str],
    horizons: tuple[int, ...] = HORIZONS,
) -> dict[str, Any]:
    """Scan only metadata fields; never index or emit value/feature columns."""
    if expected_columns < 3 or len(set(column_map.values())) != len(column_map):
        raise ValueError("COLUMN_MAP_INVALID")
    if set(("row_type", "timestamp_epoch", "session_date")) - set(column_map):
        raise ValueError("COLUMN_MAP_INCOMPLETE")
    if row_type_values != {"option": "OPTION", "spot": "SPOT"}:
        raise ValueError("ROW_TYPE_MAP_UNSUPPORTED")
    if not horizons or any(type(h) is not int or h <= 0 for h in horizons):
        raise ValueError("HORIZONS_INVALID")

    path = Path(path)
    whole_hash = hashlib.sha256()
    container_hash = sha256_file(path)
    with path.open("rb") as signature_stream:
        compressed = signature_stream.read(2) == b"\\x1f\\x8b"
    row_count = 0
    row_type_counts = {"OPTION": 0, "SPOT": 0}
    sessions: list[str] = []
    last_timestamp = -1
    last_session: dt.date | None = None
    header: list[str] | None = None
    offsets_by_session: dict[str, tuple[int, int]] = {}
    byte_offset = 0
    train_end_offset = validation_end_offset = holdout_start_offset = 0

    opener = gzip.open if compressed else open
    with opener(path, "rb") as stream:
        while True:
            start = byte_offset
            raw = stream.readline()
            if not raw:
                break
            byte_offset += len(raw)
            whole_hash.update(raw)
            row = _parse_record(raw, expected_columns if header is not None else expected_columns)
            if header is None:
                header = row
                if len(set(header)) != len(header):
                    raise ValueError("HEADER_DUPLICATE_COLUMN")
                required = set(column_map.values())
                if not required.issubset(set(header)):
                    raise ValueError("HEADER_COLUMN_MAP_MISMATCH")
                indices = {key: header.index(column_map[key]) for key in ("row_type", "timestamp_epoch", "session_date")}
                continue

            row_count += 1
            row_type = row[indices["row_type"]]
            if row_type not in row_type_counts:
                raise ValueError("ROW_TYPE_INVALID")
            try:
                timestamp = int(row[indices["timestamp_epoch"]])
            except (TypeError, ValueError) as exc:
                raise ValueError("TIMESTAMP_INVALID") from exc
            if timestamp < 0 or timestamp < last_timestamp:
                raise ValueError("TIMESTAMP_ORDER_INVALID")
            last_timestamp = timestamp
            session_text = row[indices["session_date"]]
            session_date = _parse_date(session_text)
            if last_session is not None and session_date < last_session:
                raise ValueError("SESSION_ORDER_INVALID")
            last_session = session_date
            row_type_counts[row_type] += 1

            if not sessions or sessions[-1] != session_text:
                sessions.append(session_text)
            prior = offsets_by_session.get(session_text)
            if prior is None:
                offsets_by_session[session_text] = (start, byte_offset)
            else:
                offsets_by_session[session_text] = (prior[0], byte_offset)

    if header is None or row_count == 0 or not sessions:
        raise ValueError("DATASET_EMPTY")
    if len(sessions) != len(set(sessions)):
        raise ValueError("SESSION_ORDER_INVALID")

    session_count = len(sessions)
    train_end_index = max(0, math.floor(session_count * TRAIN_FRACTION) - 1)
    validation_end_index = max(train_end_index, math.floor(session_count * VALIDATION_END_FRACTION) - 1)
    validation_end_index = min(validation_end_index, session_count - 2) if session_count >= 3 else train_end_index
    holdout_start_index = validation_end_index + 1
    if not (0 <= train_end_index < validation_end_index < holdout_start_index < session_count):
        raise ValueError("SESSION_COUNT_INSUFFICIENT_FOR_SPLIT")

    train_end_session = sessions[train_end_index]
    validation_end_session = sessions[validation_end_index]
    holdout_start_session = sessions[holdout_start_index]
    train_end_offset = offsets_by_session[train_end_session][1]
    validation_end_offset = offsets_by_session[validation_end_session][1]
    holdout_start_offset = offsets_by_session[holdout_start_session][0]

    # Metadata-only endpoint purge: no prices, quotes, features or labels are used.
    train_counts: list[int] = []
    validation_counts: list[int] = []
    validation_origin_sets: list[set[int]] = []
    purge_counts: dict[str, dict[str, int]] = {}
    for horizon in horizons:
        train_origins = 0
        validation_origins = 0
        purged_train = 0
        purged_validation = 0
        val_origins: set[int] = set()
        for origin in range(session_count):
            endpoint = origin + horizon
            if origin <= train_end_index:
                if endpoint <= train_end_index:
                    train_origins += 1
                elif endpoint < session_count:
                    purged_train += 1
            elif origin <= validation_end_index:
                if endpoint <= validation_end_index:
                    validation_origins += 1
                    val_origins.add(origin)
                elif endpoint < session_count:
                    purged_validation += 1
        train_counts.append(train_origins)
        validation_counts.append(validation_origins)
        validation_origin_sets.append(val_origins)
        purge_counts[str(horizon)] = {
            "train_cross_boundary_origins": purged_train,
            "validation_cross_boundary_origins": purged_validation,
            "train_metadata_eligible_origins": train_origins,
            "validation_metadata_eligible_origins": validation_origins,
        }
    min_train = min(train_counts, default=0)
    common_validation = len(set.intersection(*validation_origin_sets)) if validation_origin_sets else 0

    # Hash the suffix in a streaming binary pass; never decode or materialize its rows.
    holdout_hash = sha256_uncompressed_suffix(path, holdout_start_offset, compressed)
    status = "PASS_WITH_RESTRICTIONS" if min_train >= 252 and common_validation >= 250 else "NOT_ESTIMABLE"
    return {
        "schema_version": 1,
        "gate_id": "PROSPECTIVE_HOLDOUT_BOUNDARY_R1",
        "dataset_sha256": whole_hash.hexdigest(),
        "source_container_sha256": container_hash,
        "source_container_compressed": compressed,
        "expected_columns": expected_columns,
        "row_count": row_count,
        "row_type_counts": row_type_counts,
        "session_count": session_count,
        "train_session_count": train_end_index + 1,
        "validation_session_count": validation_end_index - train_end_index,
        "holdout_session_count": session_count - holdout_start_index,
        "train_end_session": train_end_session,
        "validation_end_session": validation_end_session,
        "holdout_start_session": holdout_start_session,
        "train_end_byte_offset": train_end_offset,
        "validation_end_byte_offset": validation_end_offset,
        "holdout_start_byte_offset": holdout_start_offset,
        "holdout_range_sha256": holdout_hash,
        "horizons": list(horizons),
        "purge_counts": purge_counts,
        "min_train_metadata_eligible_origins": min_train,
        "common_validation_metadata_eligible_origins": common_validation,
        "value_fields_accessed": False,
        "holdout_values_decoded": False,
        "status": status,
    }


def self_test() -> dict[str, Any]:
    # The real-data path is deliberately not exposed by this CLI.
    return {
        "suite": "prospective-holdout-boundary-synthetic-v1",
        "real_file_scan": "NOT_IMPLEMENTED",
        "market_value_access": "NOT_AUTHORIZED",
        "holdout_value_access": "NOT_AUTHORIZED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("only --self-test is available; real-file scanning is not implemented or authorized")
    print(json.dumps(self_test(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
