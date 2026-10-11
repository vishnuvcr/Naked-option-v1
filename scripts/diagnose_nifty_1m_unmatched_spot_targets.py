#!/usr/bin/env python3
"""Offline, value-free distribution of unmatched option timestamps and spot coverage.

Reads only an already decrypted local composite dataset. It never requests market
data, outputs prices, shifts timestamps, repairs rows, or authorizes model access.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import datetime as dt
import gzip
import json
import pathlib
from typing import Any


PATCH_PREFIX = "GAPSPOT1M-PATCH-R2-"


def _session_date(row: dict[str, str]) -> str:
    value = str(row.get("session_date", "") or "")
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError:
        return ""


def _nearest_delta(epoch: int, sorted_epochs: list[int]) -> int | None:
    """Return nearest spot epoch minus option epoch, preferring earlier on ties."""
    if not sorted_epochs:
        return None
    pos = bisect.bisect_left(sorted_epochs, epoch)
    candidates = []
    if pos < len(sorted_epochs):
        candidates.append(sorted_epochs[pos])
    if pos > 0:
        candidates.append(sorted_epochs[pos - 1])
    nearest = min(candidates, key=lambda candidate: (abs(candidate - epoch), candidate))
    return int(nearest - epoch)


def analyze(input_dir: pathlib.Path) -> dict[str, Any]:
    parts = sorted(input_dir.glob("nifty_1m_composite_*.csv.gz"))
    if not parts:
        raise ValueError("decrypted_monthly_parts_missing")

    rows_options = 0
    rows_spot = 0
    bad_dates = 0
    duplicate_spot_epochs = 0
    options_by_date: collections.Counter[str] = collections.Counter()
    unmatched_by_date: collections.Counter[str] = collections.Counter()
    unmatched_epochs_by_date: dict[str, set[int]] = collections.defaultdict(set)
    missing_epoch_rows: collections.Counter[int] = collections.Counter()
    missing_epoch_dates: dict[int, str] = {}
    spot_by_date: dict[str, list[int]] = collections.defaultdict(list)
    all_spot_epochs: set[int] = set()
    patch_spot_epochs: set[int] = set()
    patch_rows_by_date: collections.Counter[str] = collections.Counter()
    patch_weekdays: collections.Counter[str] = collections.Counter()
    spot_rows_by_date: collections.Counter[str] = collections.Counter()
    spot_weekdays: collections.Counter[str] = collections.Counter()
    spot_rows_by_request: collections.Counter[str] = collections.Counter()
    row_type_counts: collections.Counter[str] = collections.Counter()

    for path in parts:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"timestamp_epoch", "row_type", "session_date", "spot_join_status", "source_request_id"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError("monthly_csv_required_columns_missing")
            for row in reader:
                row_type = str(row.get("row_type", "") or "")
                row_type_counts[row_type] += 1
                day = _session_date(row)
                if not day:
                    bad_dates += 1
                    continue
                try:
                    epoch = int(row["timestamp_epoch"])
                except (ValueError, TypeError, KeyError):
                    raise ValueError("timestamp_epoch_not_integer") from None
                if row_type == "SPOT":
                    rows_spot += 1
                    spot_rows_by_date[day] += 1
                    spot_by_date[day].append(epoch)
                    if epoch in all_spot_epochs:
                        duplicate_spot_epochs += 1
                    all_spot_epochs.add(epoch)
                    request_id = str(row.get("source_request_id", "") or "")
                    spot_rows_by_request[request_id] += 1
                    weekday = dt.date.fromisoformat(day).strftime("%A")
                    spot_weekdays[weekday] += 1
                    if request_id.startswith(PATCH_PREFIX):
                        patch_spot_epochs.add(epoch)
                        patch_rows_by_date[day] += 1
                        patch_weekdays[weekday] += 1
                elif row_type == "OPTION":
                    rows_options += 1
                    options_by_date[day] += 1
                    if str(row.get("spot_join_status", "") or "") == "NO_EXACT_TIMESTAMP_SPOT_MATCH":
                        unmatched_by_date[day] += 1
                        unmatched_epochs_by_date[day].add(epoch)
                        missing_epoch_rows[epoch] += 1
                        missing_epoch_dates.setdefault(epoch, day)

    for day in spot_by_date:
        spot_by_date[day] = sorted(spot_by_date[day])
    all_sorted_spot_epochs = sorted(all_spot_epochs)

    unmatched_epochs = set(missing_epoch_rows)
    exact_matches_any_spot = unmatched_epochs & all_spot_epochs
    exact_matches_patch = unmatched_epochs & patch_spot_epochs

    nearest_delta_all: collections.Counter[str] = collections.Counter()
    nearest_delta_same_day: collections.Counter[str] = collections.Counter()
    nearest_delta_by_date: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    nearest_within_60 = 0
    nearest_within_300 = 0
    no_same_day_spot = 0
    missing_rows_with_exact_existing_spot = 0

    for epoch in unmatched_epochs:
        day = missing_epoch_dates[epoch]
        same_day_spot_epochs = spot_by_date.get(day, [])
        delta = _nearest_delta(epoch, same_day_spot_epochs)
        if delta is None:
            no_same_day_spot += 1
            delta = _nearest_delta(epoch, all_sorted_spot_epochs)
        else:
            nearest_delta_same_day[str(delta)] += 1
            nearest_delta_by_date[day][str(delta)] += 1
        if delta is not None:
            nearest_delta_all[str(delta)] += 1
            nearest_within_60 += int(abs(delta) <= 60)
            nearest_within_300 += int(abs(delta) <= 300)
        if epoch in exact_matches_any_spot:
            missing_rows_with_exact_existing_spot += missing_epoch_rows[epoch]

    manifest_path = input_dir / "dataset_manifest.json"
    manifest_summary = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_summary = manifest.get("dataset_summary", {})
        if int(manifest.get("source_row_count_options", -1)) != rows_options:
            raise ValueError("manifest_option_row_count_mismatch")
        if int(manifest.get("source_row_count_spot", -1)) != rows_spot:
            raise ValueError("manifest_spot_row_count_mismatch")

    report = {
        "schema_version": 1,
        "audit_type": "OFFLINE_UNMATCHED_OPTION_TIMESTAMP_DISTRIBUTION",
        "source_artifact_id": "11696937921",
        "row_counts": {
            "option_rows": rows_options,
            "spot_rows": rows_spot,
            "total_rows": rows_options + rows_spot,
            "row_type_counts": dict(sorted(row_type_counts.items())),
            "invalid_session_date_rows": bad_dates,
            "duplicate_spot_epoch_occurrences": duplicate_spot_epochs,
            "manifest_option_rows": manifest_summary.get("rows_options"),
            "manifest_spot_rows": manifest_summary.get("rows_spot"),
        },
        "unmatched_option_rows": {
            "row_count": sum(missing_epoch_rows.values()),
            "distinct_option_timestamps": len(unmatched_epochs),
            "option_rows_by_session_date": dict(sorted(options_by_date.items())),
            "unmatched_rows_by_session_date": dict(sorted(unmatched_by_date.items())),
            "distinct_timestamps_by_session_date": {
                day: len(unmatched_epochs_by_date[day]) for day in sorted(unmatched_by_date)
            },
            "timestamps_marked_missing_but_present_in_existing_spot_rows": {
                "distinct_timestamps": len(exact_matches_any_spot),
                "option_rows": missing_rows_with_exact_existing_spot,
            },
            "new_r2_patch_exact_timestamp_overlap": {
                "distinct_unmatched_option_timestamps": len(exact_matches_patch),
                "option_rows": sum(missing_epoch_rows[epoch] for epoch in exact_matches_patch),
            },
        },
        "spot_coverage": {
            "spot_rows_by_session_date": dict(sorted(spot_rows_by_date.items())),
            "patch_r2_rows_by_session_date": dict(sorted(patch_rows_by_date.items())),
            "spot_rows_by_weekday": dict(sorted(spot_weekdays.items())),
            "patch_r2_rows_by_weekday": dict(sorted(patch_weekdays.items())),
            "patch_r2_rows_by_source_request_id": dict(sorted(
                (request_id, count) for request_id, count in spot_rows_by_request.items()
                if request_id.startswith(PATCH_PREFIX)
            )),
            "weekend_spot_rows": sum(count for day, count in spot_rows_by_date.items()
                                     if dt.date.fromisoformat(day).weekday() >= 5),
        },
        "nearest_timestamp_diagnostic_seconds": {
            "meaning": "nearest SPOT timestamp_epoch minus unmatched OPTION timestamp_epoch; diagnostic only, never used to join",
            "distinct_unmatched_timestamps_with_nearest_same_day_spot": sum(nearest_delta_same_day.values()),
            "distinct_unmatched_timestamps_without_same_day_spot": no_same_day_spot,
            "nearest_offset_within_60_seconds": nearest_within_60,
            "nearest_offset_within_300_seconds": nearest_within_300,
            "same_day_signed_offset_histogram_seconds": dict(sorted(
                nearest_delta_same_day.items(), key=lambda item: int(item[0])
            )),
            "all_nearest_signed_offset_histogram_seconds": dict(sorted(
                nearest_delta_all.items(), key=lambda item: int(item[0])
            )),
            "same_day_signed_offset_histogram_by_session_date": {
                day: dict(sorted(hist.items(), key=lambda item: int(item[0])))
                for day, hist in sorted(nearest_delta_by_date.items())
            },
        },
        "quality_and_permission_flags": {
            "source_requests_made": False,
            "prices_emitted": False,
            "source_rows_modified": False,
            "timestamps_shifted_or_imputed": False,
            "model_fitting_or_scoring_performed": False,
            "holdout_accessed": False,
            "strategy_or_pnl_tested": False,
            "permission_conclusion": "NO_MODEL_AUTHORIZATION_FROM_UNMATCHED_TIMESTAMP_DIAGNOSTIC",
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
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps({
        "status": "DIAGNOSTIC_COMPLETE",
        "option_rows": report["row_counts"]["option_rows"],
        "spot_rows": report["row_counts"]["spot_rows"],
        "unmatched_option_rows": report["unmatched_option_rows"]["row_count"],
        "distinct_unmatched_timestamps": report["unmatched_option_rows"]["distinct_option_timestamps"],
        "unmatched_epochs_existing_spot_overlap": report["unmatched_option_rows"]["timestamps_marked_missing_but_present_in_existing_spot_rows"]["distinct_timestamps"],
        "unmatched_epochs_r2_overlap": report["unmatched_option_rows"]["new_r2_patch_exact_timestamp_overlap"]["distinct_unmatched_option_timestamps"],
        "raw_prices_emitted": False,
        "live_requests_made": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
