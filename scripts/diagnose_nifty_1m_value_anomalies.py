#!/usr/bin/env python3
"""Diagnose price/volume anomalies in the already-decrypted composite dataset.

No market values are written to the report. Records are represented by stable
SHA-256 fingerprints, session dates, issue categories, and hashed source IDs.
This script never edits source rows or authorizes model/holdout/strategy access.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
import pathlib
from decimal import Decimal, InvalidOperation
from typing import Any


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dec(value: str) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        x = Decimal(value.strip())
    except (InvalidOperation, ValueError):
        return None
    return x if x.is_finite() else None


def ohlc_issues(row: dict[str, str], prefix: str) -> list[str]:
    names = [prefix + suffix for suffix in ("open", "high", "low", "close")]
    values = {name: dec(row.get(name, "")) for name in names}
    if any(v is None for v in values.values()):
        return ["OHLC_MISSING_OR_NONFINITE"]
    op, hi, lo, cl = (values[n] for n in names)
    issues: list[str] = []
    if min(op, hi, lo, cl) <= 0:
        issues.append("OHLC_NONPOSITIVE")
    if hi < lo:
        issues.append("HIGH_BELOW_LOW")
    if hi < op:
        issues.append("HIGH_BELOW_OPEN")
    if hi < cl:
        issues.append("HIGH_BELOW_CLOSE")
    if lo > op:
        issues.append("LOW_ABOVE_OPEN")
    if lo > cl:
        issues.append("LOW_ABOVE_CLOSE")
    return issues


def row_fingerprint(row: dict[str, str]) -> str:
    # Deliberately exclude all price/volume fields from the fingerprint input.
    fields = (
        "timestamp_epoch", "row_type", "source_request_id", "expiry_flag",
        "expiry_code", "requested_relative_strike", "option_type", "returned_strike",
    )
    return digest("|".join(str(row.get(k, "") or "") for k in fields))


def analyze(input_dir: pathlib.Path) -> dict[str, Any]:
    parts = sorted(input_dir.glob("nifty_1m_composite_*.csv.gz"))
    if not parts:
        raise ValueError("decrypted_monthly_parts_missing")

    counters: collections.Counter[str] = collections.Counter()
    by_date: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    by_source: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    records: list[dict[str, Any]] = []
    bad_dates = 0
    matched_epoch_values: dict[int, tuple[str, dict[str, str]]] = {}
    spot_epoch_rows: dict[int, dict[str, str]] = {}
    option_rows = 0
    spot_rows = 0
    unmatched_rows = 0
    matched_option_nifty_issue_epochs: set[int] = set()
    matched_option_nifty_issue_signatures: set[str] = set()
    standalone_spot_issue_epochs: set[int] = set()
    duplicate_spot_epochs = 0

    # First pass: retain only one SPOT row per epoch for cross-checks. Duplicate
    # epochs are separately counted; the source audit already reports zero.
    for path in parts:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"timestamp_epoch", "row_type", "session_date", "source_request_id"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError("monthly_csv_required_columns_missing")
            for row in reader:
                typ = row.get("row_type", "")
                try:
                    epoch = int(row.get("timestamp_epoch", ""))
                except (TypeError, ValueError):
                    continue
                if typ == "SPOT":
                    spot_rows += 1
                    if epoch in spot_epoch_rows:
                        duplicate_spot_epochs += 1
                    else:
                        spot_epoch_rows[epoch] = row
                elif typ == "OPTION":
                    option_rows += 1
                    if row.get("spot_join_status") == "NO_EXACT_TIMESTAMP_SPOT_MATCH":
                        unmatched_rows += 1
                    if row.get("spot_join_status") == "EXACT_TIMESTAMP_MATCH":
                        sig = digest("|".join(row.get("nifty_" + k, "") for k in ("open", "high", "low", "close")))
                        matched_epoch_values.setdefault(epoch, (sig, row))

    def record(row: dict[str, str], issue: str, epoch: int, *, subject: str) -> None:
        nonlocal bad_dates
        day = str(row.get("session_date", "") or "")
        try:
            dt.date.fromisoformat(day)
        except ValueError:
            day = "(invalid_or_missing)"
            bad_dates += 1
        src = digest(str(row.get("source_request_id", "") or "(blank)"))
        counters[f"{subject}:{issue}"] += 1
        by_date[day][f"{subject}:{issue}"] += 1
        by_source[src][f"{subject}:{issue}"] += 1
        if len(records) < 1500:
            records.append({
                "row_fingerprint_sha256_16": row_fingerprint(row),
                "session_date": day,
                "timestamp_epoch": epoch,
                "row_type": row.get("row_type", ""),
                "source_request_id_sha256_16": src,
                "issue": issue,
                "subject": subject,
            })

    # Second pass: classify all anomalies by source lineage and row fingerprint.
    for path in parts:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                typ = row.get("row_type", "")
                try:
                    epoch = int(row.get("timestamp_epoch", ""))
                except (TypeError, ValueError):
                    counters["INVALID_TIMESTAMP_EPOCH"] += 1
                    continue

                if typ == "SPOT":
                    for issue in ohlc_issues(row, "nifty_"):
                        standalone_spot_issue_epochs.add(epoch)
                        record(row, issue, epoch, subject="SPOT_OHLC")
                    vol = dec(row.get("nifty_volume", ""))
                    if vol is not None and vol < 0:
                        record(row, "NEGATIVE_VOLUME", epoch, subject="SPOT_VOLUME")
                    elif row.get("nifty_volume", "").strip() and vol is None:
                        record(row, "NONFINITE_OR_UNPARSEABLE_VOLUME", epoch, subject="SPOT_VOLUME")

                elif typ == "OPTION":
                    for issue in ohlc_issues(row, "option_"):
                        record(row, issue, epoch, subject="OPTION_OHLC")
                    vol = dec(row.get("option_volume", ""))
                    if vol is not None and vol < 0:
                        record(row, "NEGATIVE_VOLUME", epoch, subject="OPTION_VOLUME")
                    elif row.get("option_volume", "").strip() and vol is None:
                        record(row, "NONFINITE_OR_UNPARSEABLE_VOLUME", epoch, subject="OPTION_VOLUME")

                    nvol = dec(row.get("nifty_volume", ""))
                    if row.get("spot_join_status") == "EXACT_TIMESTAMP_MATCH":
                        if nvol is not None and nvol < 0:
                            record(row, "NEGATIVE_VOLUME", epoch, subject="MATCHED_NIFTY_VOLUME")
                        elif row.get("nifty_volume", "").strip() and nvol is None:
                            record(row, "NONFINITE_OR_UNPARSEABLE_VOLUME", epoch, subject="MATCHED_NIFTY_VOLUME")
                        for issue in ohlc_issues(row, "nifty_"):
                            matched_option_nifty_issue_epochs.add(epoch)
                            sig = digest("|".join(row.get("nifty_" + k, "") for k in ("open", "high", "low", "close")))
                            matched_option_nifty_issue_signatures.add(sig)
                            record(row, issue, epoch, subject="MATCHED_NIFTY_OHLC")
                        # Compare the option row's joined NIFTY OHLC with the standalone
                        # spot record at the same exact epoch, without exposing values.
                        spot = spot_epoch_rows.get(epoch)
                        if spot is not None:
                            for suffix in ("open", "high", "low", "close", "volume"):
                                left = dec(row.get("nifty_" + suffix, ""))
                                right = dec(spot.get("nifty_" + suffix, ""))
                                if left != right:
                                    record(row, "JOINED_VALUE_DIFFERS_FROM_SPOT_ROW_" + suffix.upper(),
                                           epoch, subject="JOINED_SPOT_COMPARISON")
                    elif row.get("spot_join_status") == "NO_EXACT_TIMESTAMP_SPOT_MATCH":
                        # Missing underlying values are expected for unmatched rows, not
                        # reclassified as OHLC corruption.
                        pass

    # Cross-check counts of distinct bad epochs against row-level occurrence counts.
    report = {
        "schema_version": 1,
        "audit_type": "OFFLINE_VALUE_ANOMALY_PROVENANCE_DIAGNOSTIC",
        "status": "DIAGNOSTIC_COMPLETE",
        "row_counts": {
            "option_rows": option_rows,
            "spot_rows": spot_rows,
            "total_rows": option_rows + spot_rows,
            "unmatched_option_rows": unmatched_rows,
        },
        "issue_occurrence_counts": dict(sorted(counters.items())),
        "issue_counts_by_session_date": {
            day: dict(sorted(counts.items())) for day, counts in sorted(by_date.items())
        },
        "issue_counts_by_source_request_hash": {
            source: dict(sorted(counts.items())) for source, counts in sorted(by_source.items())
        },
        "distinct_timestamp_diagnostics": {
            "matched_option_epochs_with_invalid_joined_nifty_ohlc": len(matched_option_nifty_issue_epochs),
            "distinct_joined_nifty_ohlc_signatures_with_violations": len(matched_option_nifty_issue_signatures),
            "standalone_spot_epochs_with_ohlc_violations": len(standalone_spot_issue_epochs),
            "duplicate_spot_timestamps": duplicate_spot_epochs,
            "invalid_or_missing_session_dates_seen": bad_dates,
        },
        "flagged_row_fingerprints": records,
        "flagged_row_fingerprints_truncated": max(0, sum(counters.values()) - len(records)),
        "limitations": [
            "No raw market values are emitted.",
            "Fingerprints exclude prices and volumes and are for locating records inside the controlled runner only.",
            "This is diagnostic evidence, not a correction or exclusion decision.",
            "The original encrypted source parts remain immutable.",
            "No live requests, model fitting/scoring, holdout access or strategy/P&L tests were performed."
        ],
        "permissions": {
            "source_requests_made": False,
            "source_rows_modified": False,
            "model_fitting_or_scoring_performed": False,
            "holdout_accessed": False,
            "strategy_or_pnl_tested": False,
            "permission_conclusion": "NO_MODEL_AUTHORIZATION_FROM_ANOMALY_DIAGNOSTIC",
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=pathlib.Path)
    parser.add_argument("--output-json", required=True, type=pathlib.Path)
    args = parser.parse_args()
    report = analyze(args.input_dir.resolve())
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "row_counts": report["row_counts"],
        "issue_occurrence_counts": report["issue_occurrence_counts"],
        "prices_emitted": False,
        "source_rows_modified": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
