#!/usr/bin/env python3
"""Manifest-bound, aggregate-only diagnosis of repeated economic contract-time rows.

The only permitted real-data output is aggregate counts, hashes, and conflicting field
names. This diagnostic does not deduplicate source rows, emit row/key values, fit a model,
or access prediction holdouts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
import tempfile
import time
import zlib
import zipfile
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np
import pandas as pd

from phase8p_greek_prediction import (
    ALLOWED_CONTRACT_PROVENANCE_VARIANCE,
    CONTRACT_REQUIRED_MANIFEST_FIELDS,
    GREEK_SOURCE_PIN,
    GateBlocked,
    _canonical_contract_value,
    _economic_contract_key,
    iter_encrypted_composite_parts,
    validate_greek_manifest_columns,
    validate_greek_part_columns,
    verify_pinned_artifact_identity,
)


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_manifest_columns(greek_zip: Path) -> tuple[str, ...]:
    """Read only the schema metadata; the caller must pin the whole artifact first."""
    with zipfile.ZipFile(greek_zip, "r") as archive:
        names = archive.namelist()
        manifests = [name for name in names if name.endswith("dataset_manifest.json")]
        if len(manifests) != 1:
            raise GateBlocked("GREEK_DATASET_MANIFEST_MISSING_OR_DUPLICATE")
        try:
            manifest = json.loads(archive.read(manifests[0]))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise GateBlocked("GREEK_DATASET_MANIFEST_JSON_INVALID") from exc
    return validate_greek_manifest_columns(manifest.get("columns"))


def _normalized_option_row(row: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
    """Canonicalize the source epoch and enforce the registered 60-second valuation."""
    clean = dict(row)
    start = pd.to_numeric(pd.Series([row.get("timestamp_epoch")]), errors="coerce").iloc[0]
    offset = pd.to_numeric(pd.Series([row.get("greek_valuation_offset_seconds")]), errors="coerce").iloc[0]
    if not np.isfinite(start):
        raise GateBlocked("DUPLICATE_DIAGNOSTIC_SOURCE_EPOCH_INVALID")
    if start > 1e12:
        start = math.floor(float(start) / 1000.0)
    if float(start) != math.floor(float(start)):
        raise GateBlocked("DUPLICATE_DIAGNOSTIC_SOURCE_EPOCH_NOT_INTEGER_SECONDS")
    if not np.isfinite(offset) or not math.isclose(float(offset), 60.0, rel_tol=0.0, abs_tol=1e-9):
        raise GateBlocked("DUPLICATE_DIAGNOSTIC_UNREGISTERED_VALUATION_OFFSET")
    clean["timestamp_epoch"] = int(start)
    return clean, int(start) + 60


def scan_frames(
    frames: Iterable[pd.DataFrame],
    manifest_columns: Iterable[str],
    progress: Callable[[dict[str, int]], None] | None = None,
) -> dict[str, Any]:
    """Manifest-bound scan with disk-backed state; memory stays bounded by one source part.

    Only key/signature hashes and a compressed first-signature representation are persisted
    in a temporary SQLite database. The temporary database is always deleted and is never
    included in the aggregate receipt.
    """
    columns = validate_greek_manifest_columns(list(manifest_columns))
    signature_fields = tuple(
        field for field in columns if field not in ALLOWED_CONTRACT_PROVENANCE_VARIANCE
    )
    parts_scanned = 0
    rows_scanned = 0
    option_rows_scanned = 0
    started_at = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="phase8p-duplicate-scan-") as temp_dir:
        db_path = Path(temp_dir) / "aggregate.sqlite3"
        connection = sqlite3.connect(str(db_path))
        try:
            connection.execute("PRAGMA journal_mode=OFF")
            connection.execute("PRAGMA synchronous=OFF")
            connection.execute("PRAGMA temp_store=FILE")
            connection.execute("PRAGMA cache_size=-65536")
            connection.execute(
                """CREATE TABLE entries (
                    key_hash TEXT PRIMARY KEY,
                    row_count INTEGER NOT NULL,
                    signature_hash TEXT NOT NULL,
                    signature_blob BLOB NOT NULL,
                    first_part INTEGER NOT NULL,
                    multi_part INTEGER NOT NULL DEFAULT 0,
                    conflicting_fields TEXT NOT NULL DEFAULT '[]'
                )"""
            )
            connection.execute("CREATE INDEX idx_entries_duplicate ON entries(row_count)")
            connection.commit()

            for part_number, frame in enumerate(frames):
                parts_scanned += 1
                if not isinstance(frame, pd.DataFrame):
                    raise GateBlocked("DUPLICATE_DIAGNOSTIC_PART_SCHEMA_INVALID")
                validate_greek_part_columns(list(frame.columns), columns)
                rows_scanned += int(len(frame))
                # Iterate rows lazily. Avoid materializing a second DataFrame and a list
                # of dictionaries for every encrypted part (the composite is ~9M rows).
                names = list(frame.columns)
                row_type_index = names.index("row_type")
                connection.execute("BEGIN")
                for values in frame.itertuples(index=False, name=None):
                    row_type = values[row_type_index]
                    if pd.isna(row_type) or str(row_type).strip().upper() != "OPTION":
                        continue
                    option_rows_scanned += 1
                    record = dict(zip(names, values))
                    row, valuation_epoch = _normalized_option_row(record)
                    key, signature = _economic_contract_key(row, valuation_epoch, signature_fields)
                    key_hash = _sha256_json(list(key))
                    signature_json = json.dumps(
                        signature, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=True, allow_nan=False,
                    )
                    signature_hash = hashlib.sha256(signature_json.encode("utf-8")).hexdigest()
                    signature_blob = zlib.compress(signature_json.encode("utf-8"), level=1)
                    inserted = connection.execute(
                        """INSERT OR IGNORE INTO entries
                           (key_hash, row_count, signature_hash, signature_blob, first_part, multi_part, conflicting_fields)
                           VALUES (?, 1, ?, ?, ?, 0, '[]')""",
                        (key_hash, signature_hash, signature_blob, part_number),
                    ).rowcount
                    if inserted:
                        continue

                    previous = connection.execute(
                        """SELECT row_count, signature_hash, signature_blob, first_part,
                                  multi_part, conflicting_fields
                           FROM entries WHERE key_hash=?""",
                        (key_hash,),
                    ).fetchone()
                    if previous is None:
                        raise GateBlocked("DUPLICATE_DIAGNOSTIC_SQLITE_LOOKUP_MISSING")
                    old_count, old_hash, old_blob, first_part, old_multi_part, old_fields_json = previous
                    multi_part = int(bool(old_multi_part) or int(first_part) != part_number)
                    conflict_fields = set(json.loads(old_fields_json))
                    if old_hash != signature_hash:
                        try:
                            old_signature = json.loads(zlib.decompress(old_blob).decode("utf-8"))
                        except (zlib.error, UnicodeDecodeError, json.JSONDecodeError) as exc:
                            raise GateBlocked("DUPLICATE_DIAGNOSTIC_STORED_SIGNATURE_INVALID") from exc
                        for field in signature_fields:
                            if old_signature.get(field) != signature.get(field):
                                conflict_fields.add(field)
                        if not conflict_fields:
                            raise GateBlocked("DUPLICATE_DIAGNOSTIC_SIGNATURE_HASH_VALUE_MISMATCH")
                    connection.execute(
                        """UPDATE entries SET row_count=?, multi_part=?, conflicting_fields=?
                           WHERE key_hash=?""",
                        (int(old_count) + 1, multi_part, json.dumps(sorted(conflict_fields)), key_hash),
                    )

                connection.commit()
                if progress is not None:
                    progress({
                        "parts_scanned": int(parts_scanned),
                        "rows_scanned": int(rows_scanned),
                        "option_rows_scanned": int(option_rows_scanned),
                        "elapsed_seconds": int(time.monotonic() - started_at),
                        "temporary_database_bytes": int(db_path.stat().st_size if db_path.exists() else 0),
                    })

            duplicate_row = connection.execute(
                """SELECT
                     COUNT(*),
                     COALESCE(SUM(row_count - 1), 0),
                     COALESCE(SUM(CASE WHEN conflicting_fields='[]' THEN 1 ELSE 0 END), 0),
                     COALESCE(SUM(CASE WHEN conflicting_fields='[]' THEN row_count - 1 ELSE 0 END), 0),
                     COALESCE(SUM(CASE WHEN conflicting_fields!='[]' THEN 1 ELSE 0 END), 0),
                     COALESCE(SUM(CASE WHEN conflicting_fields!='[]' THEN row_count - 1 ELSE 0 END), 0),
                     COALESCE(SUM(CASE WHEN multi_part=1 THEN 1 ELSE 0 END), 0),
                     COALESCE(SUM(CASE WHEN multi_part=0 THEN 1 ELSE 0 END), 0)
                   FROM entries WHERE row_count > 1"""
            ).fetchone()
            (
                duplicate_groups, duplicate_extra_rows,
                identical_groups, identical_extra_rows,
                conflicting_groups, conflicting_extra_rows,
                spanning_groups, within_part_groups,
            ) = (int(value) for value in duplicate_row)
            conflict_fields: set[str] = set()
            for (fields_json,) in connection.execute(
                "SELECT conflicting_fields FROM entries WHERE row_count > 1 AND conflicting_fields!='[]'"
            ):
                conflict_fields.update(json.loads(fields_json))
            unique_keys = int(connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0])
        finally:
            connection.close()

    return {
        "parts_scanned": int(parts_scanned),
        "rows_scanned": int(rows_scanned),
        "option_rows_scanned": int(option_rows_scanned),
        "manifest_column_count": int(len(columns)),
        "manifest_columns_sha256": _sha256_json(list(columns)),
        "signature_column_count": int(len(signature_fields)),
        "signature_columns_sha256": _sha256_json(list(signature_fields)),
        "unique_economic_contract_keys": int(unique_keys),
        "duplicate_contract_groups": duplicate_groups,
        "duplicate_extra_rows": duplicate_extra_rows,
        "identical_signature_duplicate_groups": identical_groups,
        "identical_signature_duplicate_extra_rows": identical_extra_rows,
        "conflicting_signature_duplicate_groups": conflicting_groups,
        "conflicting_signature_duplicate_extra_rows": conflicting_extra_rows,
        "conflicting_signature_fields": sorted(conflict_fields),
        "groups_spanning_multiple_parts": spanning_groups,
        "groups_within_one_part": within_part_groups,
        "economic_key_policy": [
            "underlying", "greek_valuation_epoch_seconds", "normalized_expiry_date",
            "returned_strike", "normalized_option_type",
        ],
        "allowed_provenance_variance_fields": list(ALLOWED_CONTRACT_PROVENANCE_VARIANCE),
        "diagnostic_scope": "MANIFEST_BOUND_HASH_AND_COUNT_ONLY_NO_DEDUPLICATION",
        "deduplication_performed": False,
        "raw_keys_or_rows_emitted": False,
        "raw_or_decrypted_data_uploaded": False,
    }

def run_diagnostic(greek_zip: Path, artifact_id: int, output: Path) -> dict[str, Any]:
    # Artifact identity is verified before even opening the ZIP for schema metadata.
    receipt = verify_pinned_artifact_identity(greek_zip, "greek", artifact_id)
    manifest_columns = read_manifest_columns(greek_zip)
    def progress(counters: dict[str, int]) -> None:
        print(
            "DUP_DIAG_PROGRESS "
            + " ".join(f"{key}={value}" for key, value in sorted(counters.items())),
            file=sys.stderr,
            flush=True,
        )

    scan = scan_frames(iter_encrypted_composite_parts(greek_zip), manifest_columns, progress=progress)
    result = {
        "schema_version": 2,
        "gate": "PHASE8P_DUPLICATE_OPTION_KEY_DIAGNOSTIC_R4",
        "status": "DIAGNOSTIC_COMPLETE",
        "input_artifact_id": receipt["artifact_id"],
        "input_artifact_sha256": receipt["sha256"],
        "source_revision": GREEK_SOURCE_PIN["revision"],
        "source_license": GREEK_SOURCE_PIN["license"],
        **scan,
        "model_fitted": False,
        "holdout_accessed": False,
        "external_market_source_requested": False,
        "model_fit_authorized": False,
        "strategy_promotion_authorized": False,
        "option_pnl_run": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def synthetic_self_test() -> dict[str, Any]:
    epoch = 1760000000
    ts_utc = pd.Timestamp(epoch, unit="s", tz="UTC").isoformat()
    ts_ist = pd.Timestamp(epoch, unit="s", tz="UTC").tz_convert("Asia/Kolkata").isoformat()
    base = {
        "row_type": "OPTION", "underlying": "NIFTY 50", "timestamp_epoch": epoch,
        "timestamp_utc": ts_utc, "timestamp_ist": ts_ist, "session_date": "2025-10-09",
        "expiry_date": "2026-10-29", "expiry_flag": "WEEKLY", "expiry_code": "W1",
        "expiry_mapping_source": "SYNTHETIC", "returned_strike": 25000.0, "option_type": "CE",
        "time_to_expiry_years": 0.01, "greek_valuation_offset_seconds": 60,
        "risk_free_rate_decimal": 0.06, "dividend_yield_decimal": 0.01,
        "data_quality_flags": "", "greek_status": "SYNTHETIC_PASS",
        "option_open": 100.0, "option_high": 102.0, "option_low": 99.0, "option_close": 100.0,
        "option_volume": 10, "open_interest": 100, "implied_volatility": 0.2,
        "rolling_spot": 25000.0, "nifty_close": 25000.0, "spot_join_status": "EXACT",
        "greek_implied_volatility": 0.2, "greek_iv_source": "SYNTHETIC_IV",
        "delta": 0.5, "gamma": 0.01, "theta_per_day": -1.0, "vega_per_1pct_iv": 0.2,
        "rho_per_1pct_rate": 0.01, "greek_model": "SYNTHETIC_MODEL",
        "source_request_id": "request-a", "requested_relative_strike": 0,
        "request_scope_sha256": "scope-a", "response_sha256": "response-a",
        "unmodeled_manifest_column": "fixed-extra-value",
    }
    columns = list(base.keys())
    columns.extend([
        "greek_assumption", "risk_free_rate_source", "dividend_yield_source",
        "source_provider", "source_endpoint", "cache_status",
    ])
    full_base = dict(base)
    full_base.update({
        "greek_assumption": "SYNTHETIC", "risk_free_rate_source": "FIXED",
        "dividend_yield_source": "FIXED", "source_provider": "FIXTURE",
        "source_endpoint": "FIXTURE", "cache_status": "SYNTHETIC",
    })
    # Include any fixed required fields in the actual frame schema; extra fields are retained.
    columns = list(full_base.keys())
    manifest_columns = validate_greek_manifest_columns(columns)
    exact = dict(full_base, source_request_id="request-b", requested_relative_strike=1,
                 request_scope_sha256="scope-b", response_sha256="response-b")
    conflicting_base = dict(full_base, returned_strike=25050.0)
    conflicting = dict(conflicting_base, option_close=101.0)
    seconds_row = dict(full_base, returned_strike=25100.0)
    millis_row = dict(seconds_row, timestamp_epoch=epoch * 1000)

    first_part = pd.DataFrame([full_base, conflicting_base, seconds_row], columns=columns)
    second_part = pd.DataFrame([exact, conflicting, millis_row], columns=columns)
    progress_events: list[dict[str, int]] = []
    result = scan_frames([first_part, second_part], manifest_columns, progress=progress_events.append)
    assert len(progress_events) == 2
    assert {
        key: progress_events[-1][key]
        for key in ("parts_scanned", "rows_scanned", "option_rows_scanned")
    } == {
        "parts_scanned": 2,
        "rows_scanned": 6,
        "option_rows_scanned": 6,
    }
    assert progress_events[-1]["elapsed_seconds"] >= 0
    assert progress_events[-1]["temporary_database_bytes"] >= 0
    assert result["parts_scanned"] == 2
    assert result["option_rows_scanned"] == 6
    assert result["duplicate_contract_groups"] == 3
    assert result["duplicate_extra_rows"] == 3
    assert result["identical_signature_duplicate_groups"] == 2
    assert result["conflicting_signature_duplicate_groups"] == 1
    assert result["conflicting_signature_fields"] == ["option_close"]

    # Classification must be invariant to part order and row order.
    permuted = scan_frames([second_part.iloc[::-1], first_part.iloc[::-1]], manifest_columns)
    assert permuted == result

    # Any timestamp representation present in the schema must match the source epoch.
    bad_timestamp = dict(full_base, timestamp_utc=pd.Timestamp(epoch + 60, unit="s", tz="UTC").isoformat())
    try:
        scan_frames([pd.DataFrame([bad_timestamp], columns=columns)], manifest_columns)
    except GateBlocked as exc:
        assert "CONTRACT_DUPLICATE_TIMESTAMP_FIELDS_DISAGREE:timestamp_utc" in str(exc)
    else:
        raise AssertionError("timestamp text disagreeing with the epoch was accepted")

    try:
        validate_greek_manifest_columns([column for column in columns if column != "option_close"])
    except GateBlocked as exc:
        assert "GREEK_MANIFEST_REQUIRED_COLUMNS_MISSING" in str(exc)
    else:
        raise AssertionError("missing required manifest column was accepted")

    try:
        scan_frames([first_part[columns[::-1]]], manifest_columns)
    except GateBlocked as exc:
        assert "GREEK_PART_ORDERED_COLUMNS_DO_NOT_MATCH_MANIFEST" in str(exc)
    else:
        raise AssertionError("reordered part header was accepted")

    try:
        scan_frames([first_part.assign(extra_unmanifested_column=1)], manifest_columns)
    except GateBlocked as exc:
        assert "GREEK_PART_ORDERED_COLUMNS_DO_NOT_MATCH_MANIFEST" in str(exc)
    else:
        raise AssertionError("extra unmanifested column was accepted")

    try:
        scan_frames([pd.DataFrame([{"row_type": "OPTION"}])], manifest_columns)
    except GateBlocked:
        pass
    else:
        raise AssertionError("malformed part schema was accepted")

    serialized = json.dumps(result, sort_keys=True)
    assert "25000" not in serialized and "request-a" not in serialized and "fixed-extra-value" not in serialized
    assert result["deduplication_performed"] is False
    assert result["raw_keys_or_rows_emitted"] is False
    return {
        "status": "PASS",
        "mode": "SYNTHETIC_ONLY",
        "manifest_bound_schema": "PASS",
        "exact_duplicates_excluding_provenance": "PASS",
        "conflicting_signature_field_detection": "PASS",
        "seconds_milliseconds_timestamp_normalization": "PASS",
        "ordered_header_fail_closed": "PASS",
        "no_deduplication_or_raw_output": "PASS",
        "disk_backed_aggregation": "PASS",
        "per_part_progress_reporting": "PASS",
        "real_artifact_opened": False,
        "model_fitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--greek-zip", type=Path)
    parser.add_argument("--artifact-id", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(synthetic_self_test(), sort_keys=True))
        return
    if args.greek_zip is None or args.artifact_id is None or args.output is None:
        parser.error("real diagnostic requires --greek-zip, --artifact-id and --output")
    report = run_diagnostic(args.greek_zip, args.artifact_id, args.output)
    print(json.dumps({
        "status": report["status"],
        "input_artifact_id": report["input_artifact_id"],
        "input_artifact_sha256": report["input_artifact_sha256"],
        "parts_scanned": report["parts_scanned"],
        "option_rows_scanned": report["option_rows_scanned"],
        "duplicate_contract_groups": report["duplicate_contract_groups"],
        "identical_signature_duplicate_groups": report["identical_signature_duplicate_groups"],
        "conflicting_signature_duplicate_groups": report["conflicting_signature_duplicate_groups"],
        "conflicting_signature_fields": report["conflicting_signature_fields"],
        "deduplication_performed": False,
        "model_fitted": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
