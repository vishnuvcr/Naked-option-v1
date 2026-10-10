#!/usr/bin/env python3
"""Offline validation helpers for Dhan's documented instrument-master CSV.

This module deliberately contains no HTTP client and never makes a request.
A future live fetch requires a separately reviewed adapter/workflow/manifest.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import pathlib
import tempfile
from dataclasses import dataclass
from typing import Any

COMPACT_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
DETAILED_URL = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
ALLOWED_URLS = frozenset({COMPACT_URL, DETAILED_URL})
MAX_CSV_BYTES = 8 * 1024 * 1024
REQUIRED_COLUMNS = frozenset({
    "SEM_SMST_SECURITY_ID",
    "SEM_EXM_EXCH_ID",
    "SEM_SEGMENT",
    "SEM_INSTRUMENT_NAME",
    "SEM_TRADING_SYMBOL",
})


@dataclass(frozen=True)
class CsvValidation:
    row_count: int
    security_id_count: int
    sha256: str
    columns: tuple[str, ...]


def validate_instrument_csv(payload: bytes, *, max_bytes: int = MAX_CSV_BYTES) -> tuple[CsvValidation, list[dict[str, str]]]:
    """Validate bytes and identifiers without network access or persistent writes."""
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("csv_empty_or_not_bytes")
    if max_bytes <= 0 or len(payload) > max_bytes:
        raise ValueError("csv_byte_cap_exceeded")
    try:
        text = payload.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        raise ValueError("csv_encoding_invalid") from None
    if "\x00" in text:
        raise ValueError("csv_nul_byte")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        columns = tuple(reader.fieldnames or ())
        if not columns or len(columns) != len(set(columns)):
            raise ValueError("csv_header_missing_or_duplicate")
        missing = REQUIRED_COLUMNS.difference(columns)
        if missing:
            raise ValueError("csv_required_columns_missing")
        rows: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("csv_row_shape_invalid")
            security_id = (row.get("SEM_SMST_SECURITY_ID") or "").strip()
            segment = (row.get("SEM_SEGMENT") or "").strip()
            exchange = (row.get("SEM_EXM_EXCH_ID") or "").strip()
            instrument = (row.get("SEM_INSTRUMENT_NAME") or "").strip()
            symbol = (row.get("SEM_TRADING_SYMBOL") or "").strip()
            if not security_id or not segment or not exchange or not instrument or not symbol:
                raise ValueError("csv_required_value_missing")
            key = (segment, security_id)
            if key in seen:
                raise ValueError("csv_duplicate_segment_security_id")
            seen.add(key)
            rows.append({str(k): str(v).strip() for k, v in row.items()})
        if not rows:
            raise ValueError("csv_no_data_rows")
    except csv.Error:
        raise ValueError("csv_parse_error") from None
    result = CsvValidation(
        row_count=len(rows),
        security_id_count=len(seen),
        sha256=hashlib.sha256(payload).hexdigest(),
        columns=columns,
    )
    return result, rows


def atomic_cache(payload: bytes, destination: str | pathlib.Path, *, max_bytes: int = MAX_CSV_BYTES) -> dict[str, Any]:
    """Validate before atomically caching; failed validation leaves prior cache untouched."""
    validation, _ = validate_instrument_csv(payload, max_bytes=max_bytes)
    path = pathlib.Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return {
        "status": "CACHE_VALIDATED",
        "path": str(path),
        "row_count": validation.row_count,
        "security_id_count": validation.security_id_count,
        "sha256": validation.sha256,
        "bytes": len(payload),
    }


def main() -> int:
    # CLI intentionally performs no network operations. Live fetching is not implemented.
    print(json.dumps({
        "status": "OFFLINE_VALIDATION_ONLY",
        "network_enabled": False,
        "allowed_documented_urls": sorted(ALLOWED_URLS),
        "max_csv_bytes": MAX_CSV_BYTES,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
