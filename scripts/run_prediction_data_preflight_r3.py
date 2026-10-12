#!/usr/bin/env python3
"""Developer-side R3 encrypted-source reconciliation and ten-horizon label preflight.

The script runs only on a private hosted runner after decryption to RUNNER_TEMP. It
writes aggregate metadata only; it never writes market rows or a plaintext feature panel.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "research" / "registry"
DATA_MANIFEST = ROOT / "research" / "data" / "DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json"
DATA_PIN = ROOT / "research" / "data" / "PREDICTION_DATA_ARTIFACT_PIN_R3_2026-10-13.json"
CALENDAR = ROOT / "research" / "data" / "NSE_EQUITY_TRADING_CALENDAR_2021_2026_R3.json"
LABEL_MANIFEST = REG / "PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json"
CONFIG_MANIFEST = REG / "PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json"
REGISTRY_INDEX = REG / "PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
PREREG = REG / "PREDICTION_PREREGISTRATION_R3_2026-10-13.json"

IST = ZoneInfo("Asia/Kolkata")
EXPECTED_ROWS = 8_999_865
EXPECTED_COLUMNS = 47
EXPECTED_ROW_TYPES = {"OPTION": 8_490_723, "SPOT": 509_142}
CANONICAL_CSV_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
KEY_FIELDS = (
    "timestamp_epoch", "row_type", "source_request_id", "option_type",
    "nifty_open", "nifty_high", "nifty_low", "nifty_close",
)
OPTION_FEATURE_FIELDS = (
    "option_open", "option_high", "option_low", "option_close", "option_volume",
    "open_interest", "implied_volatility", "returned_strike", "rolling_spot",
    "delta", "gamma", "theta_per_day", "vega_per_1pct_iv", "rho_per_1pct_rate",
)
SESSION_OPEN = time(9, 15)
LAST_BAR_START = time(15, 29)
CLOSE_DECISION_BAR = time(15, 29)


def raw_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_csv_hash(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    byte_count = 0
    with gzip.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
            byte_count += len(chunk)
    return h.hexdigest(), byte_count


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return obj


def finite_positive(value: str) -> float | None:
    if not value or value.strip().lower() in {"", "na", "nan", "null", "none"}:
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 0 else None


def epoch_seconds(value: str) -> int:
    try:
        x = int(float(value))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid timestamp_epoch") from exc
    # Explicitly normalize only the standard Unix seconds or milliseconds encodings.
    if x >= 100_000_000_000:
        x //= 1000
    if x < 1_600_000_000 or x > 2_000_000_000:
        raise ValueError("timestamp_epoch outside the pinned dataset's valid epoch-second range")
    if x % 60 != 0:
        raise ValueError("timestamp_epoch is not aligned to a one-minute bar start")
    return x


def build_session_dates(calendar: dict[str, Any]) -> list[date]:
    bounds = calendar["date_bounds"]
    start = date.fromisoformat(bounds["start"])
    end = date.fromisoformat(bounds["end_inclusive"])
    holidays = {
        item["date"]
        for entries in calendar["regular_session_holidays_by_year"].values()
        for item in entries
    }
    holidays.update(item["date"] for item in calendar.get("supplements", []))
    result = []
    d = start
    while d <= end:
        if d.weekday() < 5 and d.isoformat() not in holidays:
            result.append(d)
        d += timedelta(days=1)
    if not result or result[0] < start or result[-1] > end:
        raise ValueError("calendar generated an invalid exchange-session range")
    return result


def fold_for_day(day: date, windows: list[dict[str, Any]]) -> str | None:
    s = day.isoformat()
    for w in windows:
        if w["start"] <= s <= w["end_inclusive"]:
            return w["id"]
    return None


def validate_source_pins(data_manifest_path: Path, encrypted_report_path: Path) -> tuple[dict, dict, dict, dict, dict]:
    data_manifest = read_json(data_manifest_path)
    data_pin = read_json(DATA_PIN)
    calendar = read_json(CALENDAR)
    labels = read_json(LABEL_MANIFEST)
    configs = read_json(CONFIG_MANIFEST)
    index = read_json(REGISTRY_INDEX)
    prereg = read_json(PREREG)
    enc = read_json(encrypted_report_path)

    if data_pin["current_derived_artifact"]["artifact_id"] != 11698879857:
        raise ValueError("DATA_PREFLIGHT_BLOCKED: current derived artifact ID changed")
    if data_pin["current_derived_artifact"]["archive_sha256"] != "40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b":
        raise ValueError("DATA_PREFLIGHT_BLOCKED: current derived archive SHA-256 pin changed")
    if data_pin["source_manifest"]["git_blob_sha1"] != git_blob_sha1(data_manifest_path.read_bytes()):
        raise ValueError("DATA_PREFLIGHT_BLOCKED: data manifest Git blob pin mismatch")
    if data_manifest.get("dataset_id") != data_pin.get("dataset_id") or data_manifest.get("encrypted_only") is not True:
        raise ValueError("DATA_PREFLIGHT_BLOCKED: data manifest identity/encryption scope mismatch")
    if enc.get("status") != "PASS_ENCRYPTED_BUNDLE_INTEGRITY" or enc.get("encrypted_part_count") != 61 or enc.get("all_encrypted_part_hashes_match") is not True:
        raise ValueError("DATA_PREFLIGHT_BLOCKED: pre-decryption encrypted bundle report is not PASS")

    scope = prereg.get("scope", {})
    for key, path in (
        ("derived_encrypted_artifact_pin_git_blob_sha1", DATA_PIN),
        ("session_calendar_git_blob_sha1", CALENDAR),
        ("label_manifest_git_blob_sha1", LABEL_MANIFEST),
        ("config_manifest_git_blob_sha1", CONFIG_MANIFEST),
        ("registry_index_git_blob_sha1", REGISTRY_INDEX),
    ):
        if scope.get(key) != git_blob_sha1(path.read_bytes()):
            raise ValueError(f"DATA_PREFLIGHT_BLOCKED: R3 preregistration pin mismatch for {key}")
    if scope.get("session_calendar_sha256") != raw_sha256(CALENDAR):
        raise ValueError("DATA_PREFLIGHT_BLOCKED: NSE calendar SHA-256 pin mismatch")
    if labels.get("common_rules", {}).get("session_calendar_git_blob_sha1") != git_blob_sha1(CALENDAR.read_bytes()):
        raise ValueError("DATA_PREFLIGHT_BLOCKED: label manifest does not pin the exact NSE calendar")
    if len(labels.get("labels", [])) != 10 or len(configs.get("config_shards", [])) != 400 or configs.get("configuration_count") != 40000:
        raise ValueError("DATA_PREFLIGHT_BLOCKED: full ten-horizon R3 registry is not complete")
    if index.get("configuration_record_count") != 40000 or index.get("configuration_shard_count") != 400:
        raise ValueError("DATA_PREFLIGHT_BLOCKED: R3 registry index count mismatch")
    return data_manifest, data_pin, calendar, labels, prereg


def collect_spot_and_structure(csv_gz: Path, embedded_manifest_path: Path) -> dict[str, Any]:
    canonical_hash, canonical_bytes = canonical_csv_hash(csv_gz)
    if canonical_hash != CANONICAL_CSV_SHA256:
        raise ValueError(f"DATA_PREFLIGHT_BLOCKED: canonical CSV SHA-256 mismatch: {canonical_hash}")
    embedded = read_json(embedded_manifest_path)
    declared_columns = embedded.get("columns")
    if not isinstance(declared_columns, list) or len(declared_columns) != EXPECTED_COLUMNS:
        raise ValueError("DATA_PREFLIGHT_BLOCKED: embedded dataset manifest lacks the pinned 47-column schema")

    row_types: Counter[str] = Counter()
    blanks: dict[str, Counter[str]] = defaultdict(Counter)
    rows = 0
    width_errors = 0
    header: list[str] | None = None
    close_by_epoch: dict[int, float] = {}
    row_by_epoch_digest: dict[int, str] = {}
    conflict_epochs: set[int] = set()
    all_spot_epochs: set[int] = set()
    spot_sessions: set[date] = set()
    spot_timestamps_by_day: dict[date, set[int]] = defaultdict(set)
    max_time_by_day: dict[date, str] = {}
    duplicate_identical = 0
    duplicate_conflicting = 0
    timestamp_parse_errors = 0
    epoch_text_mismatch = 0
    spot_rows_outside_regular_hours = 0
    date_field_mismatch = 0
    sample_rows = 0

    with gzip.open(csv_gz, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if header != declared_columns or len(header or []) != EXPECTED_COLUMNS or len(set(header or [])) != EXPECTED_COLUMNS:
            raise ValueError("DATA_PREFLIGHT_BLOCKED: canonical CSV header differs from the embedded pinned schema")
        index = {name: i for i, name in enumerate(header)}
        required = set(KEY_FIELDS) | set(OPTION_FEATURE_FIELDS) | {"timestamp_ist", "session_date", "nifty_volume"}
        missing_columns = sorted(required - set(index))
        if missing_columns:
            raise ValueError(f"DATA_PREFLIGHT_BLOCKED: required columns absent: {missing_columns}")

        for row in reader:
            rows += 1
            if len(row) != len(header):
                width_errors += 1
                continue
            kind = row[index["row_type"]].strip().upper()
            row_types[kind or "(blank)"] += 1
            for field in KEY_FIELDS + OPTION_FEATURE_FIELDS:
                if not row[index[field]].strip():
                    blanks[kind][field] += 1
            if kind != "SPOT":
                continue
            sample_rows += 1
            try:
                ts = epoch_seconds(row[index["timestamp_epoch"]])
                local = datetime.fromtimestamp(ts, IST)
                dtext = row[index["session_date"]].strip()
                d = date.fromisoformat(dtext)
                if d != local.date():
                    date_field_mismatch += 1
                if row[index["timestamp_ist"]].strip():
                    try:
                        provided = datetime.fromisoformat(row[index["timestamp_ist"]].strip().replace("Z", "+00:00"))
                        if provided.tzinfo is None:
                            provided = provided.replace(tzinfo=IST)
                        provided = provided.astimezone(IST)
                        if abs((provided - local).total_seconds()) > 1:
                            epoch_text_mismatch += 1
                    except ValueError:
                        epoch_text_mismatch += 1
            except Exception:
                timestamp_parse_errors += 1
                continue
            all_spot_epochs.add(ts)
            spot_timestamps_by_day[d].add(ts)
            if local.time() < SESSION_OPEN or local.time() > LAST_BAR_START:
                spot_rows_outside_regular_hours += 1
                continue
            close = finite_positive(row[index["nifty_close"]])
            raw_row_hash = hashlib.sha256(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
            if ts in row_by_epoch_digest:
                if row_by_epoch_digest[ts] == raw_row_hash:
                    duplicate_identical += 1
                else:
                    duplicate_conflicting += 1
                    conflict_epochs.add(ts)
                    close_by_epoch.pop(ts, None)
                continue
            row_by_epoch_digest[ts] = raw_row_hash
            if close is not None:
                close_by_epoch[ts] = close
            spot_sessions.add(d)
            max_time_by_day[d] = max(max_time_by_day.get(d, ""), local.strftime("%H:%M:%S"))

    if rows != EXPECTED_ROWS or width_errors or dict(row_types) != EXPECTED_ROW_TYPES:
        raise ValueError(
            f"DATA_PREFLIGHT_BLOCKED: structure mismatch rows={rows} width_errors={width_errors} "
            f"row_types={dict(row_types)}"
        )
    if timestamp_parse_errors or epoch_text_mismatch or date_field_mismatch:
        raise ValueError(
            f"DATA_PREFLIGHT_BLOCKED: timestamp/session mismatch parse_errors={timestamp_parse_errors}, "
            f"epoch_text_mismatch={epoch_text_mismatch}, session_date_mismatch={date_field_mismatch}"
        )

    # Never allow a timestamp marked as conflicting to supply a target price.
    for ts in conflict_epochs:
        close_by_epoch.pop(ts, None)

    feature_missingness = {}
    total = rows
    for kind, counter in blanks.items():
        denom = row_types.get(kind, 0)
        feature_missingness[kind] = {
            field: {"blank_count": int(count), "row_count": int(denom), "fraction": (count / denom if denom else None)}
            for field, count in sorted(counter.items())
        }

    return {
        "canonical_csv_sha256": canonical_hash,
        "canonical_csv_uncompressed_bytes": canonical_bytes,
        "rows": rows,
        "columns": len(header or []),
        "row_types": dict(row_types),
        "row_width_errors": width_errors,
        "spot_row_count": sample_rows,
        "spot_regular_session_timestamp_count": sum(len(v) for v in spot_timestamps_by_day.values()),
        "spot_date_count": len(spot_sessions),
        "spot_session_date_min": min(spot_sessions).isoformat() if spot_sessions else None,
        "spot_session_date_max": max(spot_sessions).isoformat() if spot_sessions else None,
        "spot_rows_outside_regular_hours": spot_rows_outside_regular_hours,
        "spot_rows_with_timestamp_parse_errors": timestamp_parse_errors,
        "spot_timestamp_epoch_text_mismatches": epoch_text_mismatch,
        "spot_session_date_mismatches": date_field_mismatch,
        "exact_duplicate_spot_rows": duplicate_identical,
        "conflicting_duplicate_spot_timestamps": duplicate_conflicting,
        "conflicting_spot_epoch_count": len(conflict_epochs),
        "feature_missingness_by_row_type": feature_missingness,
        "close_by_epoch": close_by_epoch,
        "spot_timestamps_by_day": spot_timestamps_by_day,
        "spot_sessions": spot_sessions,
        "max_time_by_day": max_time_by_day,
        "conflict_epochs": conflict_epochs,
    }


def pair_counts_for_timestamps(
    timestamps: list[int],
    prices: dict[int, float],
    conflicts: set[int],
    horizon_minutes: int,
) -> dict[str, Any]:
    counts = Counter()
    theoretical = len(timestamps)
    for ts in timestamps:
        target = ts + horizon_minutes * 60
        if ts in conflicts or target in conflicts or ts not in prices or target not in prices:
            counts["missing_pairs"] += 1
            continue
        change = prices[target] / prices[ts] - 1.0
        if not math.isfinite(change):
            counts["missing_pairs"] += 1
        elif abs(change) <= 1e-8:
            counts["flat"] += 1
        elif change > 0:
            counts["up"] += 1
        else:
            counts["down"] += 1
    counts["theoretical_pairs"] = theoretical
    counts["scored_directional"] = counts["up"] + counts["down"]
    counts["missing_fraction"] = counts["missing_pairs"] / theoretical if theoretical else 1.0
    return dict(counts)


def positional_pair_counts(
    decision_dates: list[date],
    date_index: dict[date, int],
    sessions: list[date],
    close_by_epoch: dict[int, float],
    conflicts: set[int],
) -> dict[str, Any]:
    counts = Counter()
    for d in decision_dates:
        i = date_index[d]
        target_i = i + _POSITIONAL_HORIZON
        if target_i >= len(sessions):
            counts["missing_pairs"] += 1
            continue
        target_d = sessions[target_i]
        start_ts = local_epoch(d, CLOSE_DECISION_BAR)
        target_ts = local_epoch(target_d, CLOSE_DECISION_BAR)
        if start_ts in conflicts or target_ts in conflicts or start_ts not in close_by_epoch or target_ts not in close_by_epoch:
            counts["missing_pairs"] += 1
            continue
        change = close_by_epoch[target_ts] / close_by_epoch[start_ts] - 1.0
        if not math.isfinite(change):
            counts["missing_pairs"] += 1
        elif abs(change) <= 1e-8:
            counts["flat"] += 1
        elif change > 0:
            counts["up"] += 1
        else:
            counts["down"] += 1
    counts["theoretical_pairs"] = len(decision_dates)
    counts["scored_directional"] = counts["up"] + counts["down"]
    counts["missing_fraction"] = counts["missing_pairs"] / len(decision_dates) if decision_dates else 1.0
    return dict(counts)


def local_epoch(d: date, t: time) -> int:
    return int(datetime.combine(d, t, tzinfo=IST).timestamp())


def evaluate_label_folds(
    sessions: list[date],
    close_by_epoch: dict[int, float],
    conflicts: set[int],
    prereg: dict[str, Any],
) -> list[dict[str, Any]]:
    date_index = {d: i for i, d in enumerate(sessions)}
    windows = prereg["chronological_validation"]["fold_calendar_windows"]
    min_train = prereg["sample_eligibility"]["minimum_train_rows"]
    min_valid = prereg["sample_eligibility"]["minimum_validation_rows"]
    min_train_class = prereg["sample_eligibility"]["minimum_class_support_each_direction_training"]
    min_valid_class = prereg["sample_eligibility"]["minimum_class_support_each_direction_per_validation_fold"]
    max_missing = prereg["sample_eligibility"]["target_pair_missing_fraction_max"]
    results = []
    for win in windows:
        fold_dates = [d for d in sessions if win["start"] <= d.isoformat() <= win["end_inclusive"]]
        if not fold_dates:
            for label in prereg["labels"]:
                results.append({"label_id": label, "fold_id": win["id"], "status": "BLOCKED_NO_FOLD_SESSIONS"})
            continue
        start_index = date_index[fold_dates[0]]
        end_index = date_index[fold_dates[-1]]
        for label_id, meta in prereg["labels"].items():
            is_intraday = "label_horizon_minutes" in meta
            if is_intraday:
                horizon = int(meta["label_horizon_minutes"])
                # One-minute candles are timestamped by bar start. A decision uses the
                # close at the bar's end; matching t and t+h starts gives exactly h minutes.
                train_dates = sessions[:max(0, start_index - int(meta["purge_exchange_sessions"]))]
                valid_dates = fold_dates
                width = (datetime.combine(date(2000,1,1), LAST_BAR_START) - datetime.combine(date(2000,1,1), SESSION_OPEN)).seconds // 60 + 1
                time_slots = width - horizon
                train_times = [
                    local_epoch(d, time(9, 15) + timedelta(minutes=m))
                    for d in train_dates
                    for m in range(max(0, time_slots))
                ]
                # Validation labels are scored only if the target bar remains inside the fold and regular session.
                valid_times = [
                    local_epoch(d, time(9, 15) + timedelta(minutes=m))
                    for d in valid_dates
                    for m in range(max(0, time_slots))
                ]
                train_stats = pair_counts_for_timestamps(train_times, close_by_epoch, conflicts, horizon)
                valid_stats = pair_counts_for_timestamps(valid_times, close_by_epoch, conflicts, horizon)
            else:
                _POSITIONAL_HORIZON = int(meta["label_horizon_exchange_sessions"])
                global _POSITIONAL_HORIZON
                train_idx_stop = max(0, start_index - int(meta["purge_exchange_sessions"]))
                train_dates = [d for d in sessions[:train_idx_stop] if date_index[d] + _POSITIONAL_HORIZON < start_index]
                valid_dates = [d for d in fold_dates if date_index[d] + _POSITIONAL_HORIZON <= end_index]
                train_stats = positional_pair_counts(train_dates, date_index, sessions, close_by_epoch, conflicts)
                valid_stats = positional_pair_counts(valid_dates, date_index, sessions, close_by_epoch, conflicts)
            train_rows = int(train_stats.get("scored_directional", 0))
            valid_rows = int(valid_stats.get("scored_directional", 0))
            reasons = []
            if float(train_stats.get("missing_fraction", 1.0)) > float(max_missing):
                reasons.append("TRAIN_TARGET_PAIR_MISSINGNESS_OVER_1PCT")
            if float(valid_stats.get("missing_fraction", 1.0)) > float(max_missing):
                reasons.append("VALIDATION_TARGET_PAIR_MISSINGNESS_OVER_1PCT")
            if train_rows < int(min_train[label_id]):
                reasons.append("TRAIN_ROWS_BELOW_FROZEN_MINIMUM")
            if valid_rows < int(min_valid[label_id]):
                reasons.append("VALIDATION_ROWS_BELOW_FROZEN_MINIMUM")
            if int(train_stats.get("up", 0)) < int(min_train_class[label_id]) or int(train_stats.get("down", 0)) < int(min_train_class[label_id]):
                reasons.append("TRAIN_CLASS_SUPPORT_BELOW_FROZEN_MINIMUM")
            if int(valid_stats.get("up", 0)) < int(min_valid_class[label_id]) or int(valid_stats.get("down", 0)) < int(min_valid_class[label_id]):
                reasons.append("VALIDATION_CLASS_SUPPORT_BELOW_FROZEN_MINIMUM")
            if len(conflicts) > 0:
                # The actual affected endpoints are counted as missing above; this is informational, not blanket blocking.
                reasons.append("CONFLICTING_DUPLICATE_SPOT_TIMESTAMPS_PRESENT_CHECK_MISSINGNESS")
            results.append({
                "label_id": label_id,
                "fold_id": win["id"],
                "status": "ELIGIBLE_FOR_FEATURE_PANEL_PREFLIGHT" if not reasons else "BLOCKED_DATA_OR_SAMPLE_MINIMUMS",
                "block_reasons": reasons,
                "training": train_stats,
                "validation": valid_stats,
                "training_directional_rows": train_rows,
                "validation_directional_rows": valid_rows,
                "horizon": int(meta.get("label_horizon_minutes", meta.get("label_horizon_exchange_sessions", 0))),
                "purge_exchange_sessions": int(meta["purge_exchange_sessions"]),
                "embargo_exchange_sessions": int(meta["embargo_exchange_sessions"]),
            })
    return results


def run_preflight(
    csv_gz: Path,
    embedded_manifest_path: Path,
    encrypted_report_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    data_manifest, data_pin, calendar, labels_manifest, prereg = validate_source_pins(DATA_MANIFEST, encrypted_report_path)
    structural = collect_spot_and_structure(csv_gz, embedded_manifest_path)
    sessions = build_session_dates(calendar)
    all_holidays = {
        item["date"]
        for entries in calendar["regular_session_holidays_by_year"].values()
        for item in entries
    }
    all_holidays.update(item["date"] for item in calendar.get("supplements", []))
    expected_dates = set(sessions)
    observed = structural["spot_sessions"]
    missing_sessions = sorted(d.isoformat() for d in expected_dates - observed)
    unexpected_dates = sorted(d.isoformat() for d in observed if d not in expected_dates)
    # Every observed timestamp outside official regular session is recorded; it is never used as an intraday predictor/label.
    fold_rows = evaluate_label_folds(sessions, structural["close_by_epoch"], structural["conflict_epochs"], prereg)
    passed = [x for x in fold_rows if x["status"] == "ELIGIBLE_FOR_FEATURE_PANEL_PREFLIGHT"]
    blocked = [x for x in fold_rows if x["status"] != "ELIGIBLE_FOR_FEATURE_PANEL_PREFLIGHT"]
    observed_expected_sessions = len(expected_dates & observed)
    missing_session_fraction = len(missing_sessions) / len(expected_dates) if expected_dates else 1.0
    status = (
        "DATA_PREFLIGHT_HAS_ELIGIBLE_LABEL_FOLDS"
        if passed
        else "DATA_PREFLIGHT_NO_LABEL_FOLDS_MEET_FROZEN_MINIMA"
    )
    report = {
        "schema_version": 1,
        "gate": "PREDICTION_DATA_PREFLIGHT_R3",
        "status": status,
        "created_at_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
        "source": {
            "dataset_id": data_manifest["dataset_id"],
            "derived_artifact_id": data_pin["current_derived_artifact"]["artifact_id"],
            "derived_artifact_run_id": data_pin["current_derived_artifact"]["workflow_run_id"],
            "derived_artifact_archive_sha256": data_pin["current_derived_artifact"]["archive_sha256"],
            "embedded_manifest_sha256": data_pin["current_derived_artifact"]["embedded_manifest_sha256"],
            "reference_data_manifest_git_blob_sha1": git_blob_sha1(DATA_MANIFEST.read_bytes()),
            "calendar_git_blob_sha1": git_blob_sha1(CALENDAR.read_bytes()),
            "calendar_sha256": raw_sha256(CALENDAR),
            "label_manifest_git_blob_sha1": git_blob_sha1(LABEL_MANIFEST.read_bytes()),
            "config_manifest_git_blob_sha1": git_blob_sha1(CONFIG_MANIFEST.read_bytes()),
            "registry_index_git_blob_sha1": git_blob_sha1(REGISTRY_INDEX.read_bytes()),
            "preregistration_git_blob_sha1": git_blob_sha1(PREREG.read_bytes()),
        },
        "structural": {k: v for k, v in structural.items() if k not in {"close_by_epoch","spot_timestamps_by_day","spot_sessions","max_time_by_day","conflict_epochs"}},
        "session_calendar": {
            "calendar_id": calendar["calendar_id"],
            "date_bounds": calendar["date_bounds"],
            "scheduled_sessions": len(sessions),
            "observed_expected_sessions": observed_expected_sessions,
            "missing_expected_session_count": len(missing_sessions),
            "missing_expected_session_dates": missing_sessions[:100],
            "missing_expected_session_dates_truncated": len(missing_sessions) > 100,
            "missing_expected_session_fraction": missing_session_fraction,
            "unexpected_observed_session_count": len(unexpected_dates),
            "unexpected_observed_session_dates": unexpected_dates[:100],
            "unexpected_observed_session_dates_truncated": len(unexpected_dates) > 100,
        },
        "label_fold_eligibility": fold_rows,
        "label_fold_counts": {
            "eligible_for_feature_panel_preflight": len(passed),
            "blocked_data_or_sample_minimums": len(blocked),
            "total": len(fold_rows),
        },
        "model_fit_authorized_by_data_preflight": False,
        "holdout_accessed": False,
        "option_pnl_generated": False,
        "plaintext_or_raw_market_rows_uploaded": False,
        "notes": [
            "This is a data/label-eligibility report only; no estimator was fitted, no target was used for model selection, and no holdout was opened.",
            "A fold can be eligible for feature-panel construction only when missing target-pair fraction and all frozen row/class-support minima pass.",
            "Feature-panel quality and causal feature-availability checks are a separate mandatory developer gate before empirical fitting.",
            "The source option chain remains PARTIAL_GRID, 19,021 option observations had no exact spot join in the source summary, and expiry/rate/dividend inputs are partly rule-derived or absent. These are feature-level scoped restrictions, not grounds to invent values.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--composite-csv-gz", type=Path, required=True)
    parser.add_argument("--embedded-manifest", type=Path, required=True)
    parser.add_argument("--encrypted-integrity-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_preflight(args.composite_csv_gz, args.embedded_manifest, args.encrypted_integrity_report, args.output)
    print(json.dumps({k: v for k, v in report.items() if k not in {"label_fold_eligibility"}}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
