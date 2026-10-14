"""Pre-result feature builder for the frozen Phase 8P R3 raw lag-stack representation.

No model fitting, ranking, holdout access, or persistent storage of raw observations occurs here.
The public input API accepts SPOT records already read from a locally verified canonical file.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research" / "registry" / "PREDICTION_FEATURE_CONSTRUCTION_CONTRACT_R3_2026-10-13.json"
CORRECTION_PATH = ROOT / "research" / "registry" / "PREDICTION_FEATURE_CONSTRUCTION_CORRECTION_R3A_2026-10-14.json"
EXPECTED_CORRECTION_ID = "PHASE8P_FEATURE_CONSTRUCTION_CORRECTION_R3A_2026-10-14"
CALENDAR_PATH = ROOT / "research" / "data" / "NSE_CAPITAL_MARKET_SESSION_CALENDAR_R3_2026-10-13.json"
EXPECTED_DATA_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
EXPECTED_CALENDAR_SHA256 = "ddce75f70f39e390e3d68fc6662ed31b3b85b9ecbc78d71178eedb7a34b9ae26"
EXPECTED_CALENDAR_ID = "NSE_CAPITAL_MARKET_EQUITIES_2021_2026_R3"
FLAT_TOLERANCE = 1e-8
OPEN = time(9, 15)
CLOSE = time(15, 30)
INTRADAY_MINUTES = {
    "INTRA_5M_UP_DOWN": 5,
    "INTRA_15M_UP_DOWN": 15,
    "INTRA_30M_UP_DOWN": 30,
    "INTRA_60M_UP_DOWN": 60,
    "INTRA_120M_UP_DOWN": 120,
}
POSITIONAL_SESSIONS = {
    "POS_1D_UP_DOWN": 1,
    "POS_2D_UP_DOWN": 2,
    "POS_3D_UP_DOWN": 3,
    "POS_5D_UP_DOWN": 5,
    "POS_10D_UP_DOWN": 10,
}


class FeatureBuildError(ValueError):
    """Frozen source or feature-construction contract failed."""


@dataclass(frozen=True)
class SpotBar:
    timestamp: datetime
    session_date: str
    close: float
    session_index: int


@dataclass(frozen=True)
class FeatureSample:
    label_id: str
    decision_timestamp: str
    target_endpoint_timestamp: str
    decision_session_index: int
    target_endpoint_session_index: int
    y: int
    features: tuple[float, ...]


@dataclass(frozen=True)
class FeatureBatch:
    samples: tuple[FeatureSample, ...]
    diagnostics: dict[str, Any]


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_frozen_correction(contract_sha256: str) -> tuple[dict[str, Any], str]:
    if not CORRECTION_PATH.is_file():
        raise FeatureBuildError("FEATURE_CONSTRUCTION_CORRECTION_FILE_MISSING")
    raw = CORRECTION_PATH.read_bytes()
    try:
        correction = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FeatureBuildError("FEATURE_CONSTRUCTION_CORRECTION_INVALID_JSON") from exc
    if correction.get("status") != "FROZEN_PRE_RESULTS_IMPLEMENTATION_CORRECTION":
        raise FeatureBuildError("FEATURE_CONSTRUCTION_CORRECTION_NOT_FROZEN_PRE_RESULTS")
    if correction.get("amendment_id") != EXPECTED_CORRECTION_ID:
        raise FeatureBuildError("FEATURE_CONSTRUCTION_CORRECTION_ID_MISMATCH")
    if correction.get("supersedes_contract_sha256") != contract_sha256:
        raise FeatureBuildError("FEATURE_CONSTRUCTION_CORRECTION_CONTRACT_PIN_MISMATCH")
    rule = correction.get("corrected_rule", {})
    if rule.get("positional_close_candidate_source_times_ist") != ["15:29:00", "15:30:00"]:
        raise FeatureBuildError("POSITIONAL_CLOSE_CORRECTION_CANDIDATE_TIMES_INVALID")
    if rule.get("effective_decision_and_target_timestamp_ist") != "Normalize a selected 15:29 source row to its interval-end instant, 15:30, for decision/target endpoint timestamps. A source row timestamped 15:30 remains 15:30.":
        raise FeatureBuildError("POSITIONAL_CLOSE_CORRECTION_NORMALIZATION_RULE_INVALID")
    if not str(rule.get("missing_close", "")).startswith("If neither 15:29 nor 15:30 exists"):
        raise FeatureBuildError("POSITIONAL_CLOSE_CORRECTION_MISSING_RULE_INVALID")
    if correction.get("verification", {}).get("holdout_accessed") is not False or correction.get("verification", {}).get("model_fitting_performed") is not False:
        raise FeatureBuildError("POSITIONAL_CLOSE_CORRECTION_SCOPE_FLAGS_INVALID")
    return correction, hashlib.sha256(raw).hexdigest()


def read_frozen_contract(path: Path = CONTRACT_PATH) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise FeatureBuildError("FEATURE_CONTRACT_FILE_MISSING")
    raw = path.read_bytes()
    try:
        contract = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FeatureBuildError("FEATURE_CONTRACT_INVALID_JSON") from exc
    if contract.get("status") != "FROZEN_PRE_RESULTS_IMPLEMENTATION_SUPPLEMENT":
        raise FeatureBuildError("FEATURE_CONTRACT_NOT_FROZEN_PRE_RESULTS")
    if contract.get("amendment_id") != "PHASE8P_FEATURE_CONSTRUCTION_SUPPLEMENT_R3_2026-10-13":
        raise FeatureBuildError("FEATURE_CONTRACT_ID_MISMATCH")
    contract_sha = sha256_bytes(raw)
    read_frozen_correction(contract_sha)
    return contract, contract_sha


def verify_source_pins(source_csv_sha256: str, calendar_path: Path = CALENDAR_PATH,
                       contract_path: Path = CONTRACT_PATH) -> dict[str, str]:
    contract, contract_sha = read_frozen_contract(contract_path)
    if source_csv_sha256 != contract["scope"]["canonical_csv_sha256"]:
        raise FeatureBuildError("CANONICAL_DATA_HASH_PIN_MISMATCH")
    if not calendar_path.is_file():
        raise FeatureBuildError("FROZEN_CALENDAR_MISSING")
    calendar_hash = sha256_bytes(calendar_path.read_bytes())
    if calendar_hash != EXPECTED_CALENDAR_SHA256:
        raise FeatureBuildError("FROZEN_CALENDAR_SHA256_MISMATCH")
    calendar = json.loads(calendar_path.read_text(encoding="utf-8"))
    calendar_id = calendar.get("calendar_id", calendar.get("session_calendar_id"))
    if calendar_id is not None and calendar_id != EXPECTED_CALENDAR_ID:
        raise FeatureBuildError("FROZEN_CALENDAR_ID_MISMATCH")
    if contract["scope"]["calendar_path"] != calendar_path.relative_to(ROOT).as_posix():
        raise FeatureBuildError("FEATURE_CONTRACT_CALENDAR_PATH_MISMATCH")
    _, correction_sha = read_frozen_correction(contract_sha)
    return {
        "source_csv_sha256": source_csv_sha256,
        "calendar_sha256": calendar_hash,
        "contract_sha256": contract_sha,
        "feature_correction_sha256": correction_sha,
        "feature_correction_git_blob_sha1": hashlib.sha1(
            b"blob " + str(CORRECTION_PATH.stat().st_size).encode("ascii") + b"\0" + CORRECTION_PATH.read_bytes()
        ).hexdigest(),
    }


def parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise FeatureBuildError("SPOT_TIMESTAMP_MISSING")
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise FeatureBuildError("SPOT_TIMESTAMP_INVALID") from exc
    if stamp.tzinfo is None:
        raise FeatureBuildError("SPOT_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    local = stamp
    # Canonical timestamps are expected in Asia/Kolkata; enforce +05:30 explicitly.
    offset = local.utcoffset()
    if offset is None or offset.total_seconds() != 19800:
        raise FeatureBuildError("SPOT_TIMESTAMP_NOT_IST_OFFSET")
    return local


def load_eligible_session_dates(calendar: Mapping[str, Any], label_id: str) -> list[str]:
    calendar_id = calendar.get("calendar_id", calendar.get("session_calendar_id"))
    if calendar_id is not None and calendar_id != EXPECTED_CALENDAR_ID:
        raise FeatureBuildError("CALENDAR_ID_MISMATCH")
    if label_id not in INTRADAY_MINUTES and label_id not in POSITIONAL_SESSIONS:
        raise FeatureBuildError(f"UNKNOWN_LABEL_ID:{label_id}")
    field = "intraday_label_eligible" if label_id in INTRADAY_MINUTES else "positional_label_eligible"
    rows = calendar.get("calendar_day_rows")
    if not isinstance(rows, list):
        raise FeatureBuildError("CALENDAR_DAY_ROWS_MISSING")
    dates: list[str] = []
    seen: set[str] = set()
    for row in rows:
        day = row.get("date")
        if not isinstance(day, str):
            raise FeatureBuildError("CALENDAR_DATE_MISSING")
        if row.get("is_exchange_trading_session") and row.get("regular_hours_compatible") and row.get(field):
            if day in seen:
                raise FeatureBuildError(f"DUPLICATE_CALENDAR_SESSION:{day}")
            seen.add(day)
            dates.append(day)
    dates.sort()
    if not dates:
        raise FeatureBuildError("NO_ELIGIBLE_SESSIONS_IN_CALENDAR")
    return dates


def _parse_close(row: Mapping[str, Any]) -> float:
    value = row.get("nifty_close")
    try:
        close = float(value)
    except (TypeError, ValueError) as exc:
        raise FeatureBuildError("ELIGIBLE_SPOT_CLOSE_INVALID") from exc
    if not math.isfinite(close) or close <= 0:
        raise FeatureBuildError("ELIGIBLE_SPOT_CLOSE_NONPOSITIVE_OR_NONFINITE")
    return close


def collect_eligible_spot_bars(
    records: Iterable[Mapping[str, Any]],
    eligible_session_dates: Sequence[str],
) -> tuple[dict[str, list[SpotBar]], dict[str, int]]:
    """Retain only PIT-eligible SPOT bars; never forward-fill or value-deduplicate."""
    session_idx = {d: i for i, d in enumerate(eligible_session_dates)}
    bars: dict[str, list[SpotBar]] = defaultdict(list)
    counts: Counter[str] = Counter()
    seen_timestamps: set[str] = set()

    for row in records:
        if str(row.get("row_type", "")).strip().upper() != "SPOT":
            continue
        counts["input_SPOT_rows"] += 1
        raw_ts = row.get("timestamp_ist")
        try:
            stamp = parse_timestamp(raw_ts)
        except FeatureBuildError as exc:
            counts[f"quarantined_{exc.args[0]}"] += 1
            continue
        local_day = stamp.date().isoformat()
        if local_day not in session_idx:
            counts["quarantined_CLOSED_OR_UNMAPPED_SESSION"] += 1
            continue
        if row.get("session_date") != local_day:
            counts["quarantined_SESSION_DATE_MISMATCH"] += 1
            continue
        local_time = stamp.timetz().replace(tzinfo=None)
        if local_time < OPEN or local_time > CLOSE:
            counts["quarantined_OUTSIDE_REGULAR_SESSION"] += 1
            continue
        if stamp.second != 0 or stamp.microsecond != 0:
            counts["quarantined_NON_MINUTE_TIMESTAMP"] += 1
            continue
        try:
            close = _parse_close(row)
        except FeatureBuildError as exc:
            counts[f"quarantined_{exc.args[0]}"] += 1
            continue
        ts_key = stamp.isoformat()
        if ts_key in seen_timestamps:
            counts["duplicate_eligible_timestamps"] += 1
            raise FeatureBuildError(f"DUPLICATE_ELIGIBLE_SPOT_TIMESTAMP:{ts_key}")
        seen_timestamps.add(ts_key)
        bars[local_day].append(SpotBar(stamp, local_day, close, session_idx[local_day]))
        counts["eligible_SPOT_rows"] += 1

    for day in bars:
        bars[day].sort(key=lambda item: item.timestamp)
    return dict(bars), dict(counts)


def ordered_lagged_returns_and_levels(closes: Sequence[float], lookback_bars: int) -> tuple[float, ...]:
    """Build L simple returns then L close levels, newest-to-oldest, from L+1 closes."""
    if isinstance(lookback_bars, bool) or lookback_bars not in (20, 60):
        raise FeatureBuildError("LOOKBACK_NOT_IN_FROZEN_REGISTRY")
    if len(closes) < lookback_bars + 1:
        raise FeatureBuildError("FEATURE_HISTORY_TOO_SHORT")
    values = [float(x) for x in closes[-(lookback_bars + 1):]]
    if any(not math.isfinite(x) or x <= 0 for x in values):
        raise FeatureBuildError("FEATURE_CLOSES_NONPOSITIVE_OR_NONFINITE")
    returns = []
    latest_to_oldest = list(reversed(values))
    for j in range(lookback_bars):
        now, prev = latest_to_oldest[j], latest_to_oldest[j + 1]
        returns.append(now / prev - 1.0)
    levels = latest_to_oldest[:lookback_bars]
    feature_vector = tuple(returns + levels)
    if len(feature_vector) != 2 * lookback_bars or not all(math.isfinite(x) for x in feature_vector):
        raise FeatureBuildError("FEATURE_VECTOR_DIMENSION_OR_FINITE_CHECK_FAILED")
    return feature_vector


def _session_close_map(bars_by_day: Mapping[str, Sequence[SpotBar]]) -> dict[str, SpotBar]:
    """Select the latest documented final-minute close source, never a nearest bar."""
    candidate_times = {time(15, 29), CLOSE}
    out: dict[str, SpotBar] = {}
    for day, bars in bars_by_day.items():
        candidates = [
            bar for bar in bars
            if bar.timestamp.timetz().replace(tzinfo=None) in candidate_times
        ]
        if candidates:
            # Duplicate timestamps are already rejected by collect_eligible_spot_bars.
            # If both final-minute and explicit-close rows exist, explicit 15:30 wins.
            out[day] = max(candidates, key=lambda bar: bar.timestamp)
    return out


def _effective_session_close_timestamp(bar: SpotBar) -> datetime:
    source_time = bar.timestamp.timetz().replace(tzinfo=None)
    if source_time == time(15, 29):
        return bar.timestamp + timedelta(minutes=1)
    if source_time == CLOSE:
        return bar.timestamp
    raise FeatureBuildError("SESSION_CLOSE_SOURCE_TIMESTAMP_NOT_ALLOWED")


def build_feature_batch(
    records: Iterable[Mapping[str, Any]],
    calendar: Mapping[str, Any],
    label_id: str,
    lookback_bars: int,
    *,
    source_csv_sha256: str = EXPECTED_DATA_SHA256,
    calendar_sha256: str = EXPECTED_CALENDAR_SHA256,
    contract_sha256: str | None = None,
) -> FeatureBatch:
    """Build a single frozen label/lookback sample batch and aggregate diagnostics.

    Production callers must run verify_source_pins() on the actual source archive,
    calendar, and contract before invoking this function.
    """
    if label_id not in INTRADAY_MINUTES and label_id not in POSITIONAL_SESSIONS:
        raise FeatureBuildError(f"UNKNOWN_LABEL_ID:{label_id}")
    if lookback_bars not in (20, 60):
        raise FeatureBuildError("LOOKBACK_NOT_IN_FROZEN_REGISTRY")
    if source_csv_sha256 != EXPECTED_DATA_SHA256:
        raise FeatureBuildError("CANONICAL_DATA_HASH_PIN_MISMATCH")
    if calendar_sha256 != EXPECTED_CALENDAR_SHA256:
        raise FeatureBuildError("FROZEN_CALENDAR_SHA256_MISMATCH")
    _, actual_contract_hash = read_frozen_contract()
    if contract_sha256 is not None and contract_sha256 != actual_contract_hash:
        raise FeatureBuildError("FEATURE_CONTRACT_SHA256_MISMATCH")
    calendar_sha, eligible_sessions = (calendar_sha256, load_eligible_session_dates(calendar, label_id))
    calendar_close_set = set(eligible_sessions)
    bars_by_day, data_counts = collect_eligible_spot_bars(records, eligible_sessions)
    session_close = _session_close_map(bars_by_day)
    close_by_session_index = {
        bar.session_index: bar for day, bar in session_close.items()
        if day in calendar_close_set
    }
    session_index = {day: i for i, day in enumerate(eligible_sessions)}
    emitted: list[FeatureSample] = []
    diagnostics: Counter[str] = Counter(data_counts)
    diagnostics["samples_considered"] = 0
    diagnostics["target_pairs_possible"] = 0
    diagnostics["target_pairs_missing"] = 0
    diagnostics["endpoint_ineligible"] = 0
    diagnostics["flat_targets_excluded"] = 0
    diagnostics["feature_history_excluded"] = 0
    diagnostics["missing_decision_close_sessions"] = 0

    if label_id in INTRADAY_MINUTES:
        horizon = INTRADAY_MINUTES[label_id]
        for day in eligible_sessions:
            day_bars = bars_by_day.get(day, [])
            lookup = {bar.timestamp: bar for bar in day_bars}
            for i, decision in enumerate(day_bars):
                diagnostics["samples_considered"] += 1
                target_time = decision.timestamp + timedelta(minutes=horizon)
                # A target beyond the regular session is excluded from the possible-pair denominator.
                if target_time.date().isoformat() != day or target_time.timetz().replace(tzinfo=None) > CLOSE:
                    diagnostics["endpoint_ineligible"] += 1
                    continue
                diagnostics["target_pairs_possible"] += 1
                target = lookup.get(target_time)
                if target is None or target.session_date != decision.session_date:
                    diagnostics["target_pairs_missing"] += 1
                    continue
                simple_return = target.close / decision.close - 1.0
                if abs(simple_return) <= FLAT_TOLERANCE:
                    diagnostics["flat_targets_excluded"] += 1
                    continue
                if i < lookback_bars:
                    diagnostics["feature_history_excluded"] += 1
                    continue
                history = day_bars[i - lookback_bars:i + 1]
                try:
                    feature_vector = ordered_lagged_returns_and_levels([x.close for x in history], lookback_bars)
                except FeatureBuildError:
                    diagnostics["feature_history_excluded"] += 1
                    continue
                emitted.append(FeatureSample(
                    label_id=label_id,
                    decision_timestamp=decision.timestamp.isoformat(),
                    target_endpoint_timestamp=target.timestamp.isoformat(),
                    decision_session_index=session_index[day],
                    target_endpoint_session_index=session_index[day],
                    y=1 if simple_return > FLAT_TOLERANCE else 0,
                    features=feature_vector,
                ))
    else:
        horizon = POSITIONAL_SESSIONS[label_id]
        for i, day in enumerate(eligible_sessions):
            diagnostics["samples_considered"] += 1
            target_index = i + horizon
            if target_index >= len(eligible_sessions):
                diagnostics["endpoint_ineligible"] += 1
                continue
            diagnostics["target_pairs_possible"] += 1
            decision = session_close.get(day)
            if decision is None:
                diagnostics["missing_decision_close_sessions"] += 1
                diagnostics["target_pairs_missing"] += 1
                continue
            target = close_by_session_index.get(target_index)
            if target is None:
                diagnostics["target_pairs_missing"] += 1
                continue
            simple_return = target.close / decision.close - 1.0
            if abs(simple_return) <= FLAT_TOLERANCE:
                diagnostics["flat_targets_excluded"] += 1
                continue
            history_indices = list(range(i - lookback_bars, i + 1))
            if len(history_indices) != lookback_bars + 1 or history_indices[0] < 0:
                diagnostics["feature_history_excluded"] += 1
                continue
            history = [close_by_session_index.get(k) for k in history_indices]
            if any(x is None for x in history):
                diagnostics["feature_history_excluded"] += 1
                continue
            try:
                feature_vector = ordered_lagged_returns_and_levels([x.close for x in history if x is not None], lookback_bars)
            except FeatureBuildError:
                diagnostics["feature_history_excluded"] += 1
                continue
            emitted.append(FeatureSample(
                label_id=label_id,
                decision_timestamp=_effective_session_close_timestamp(decision).isoformat(),
                target_endpoint_timestamp=_effective_session_close_timestamp(target).isoformat(),
                decision_session_index=i,
                target_endpoint_session_index=target_index,
                y=1 if simple_return > FLAT_TOLERANCE else 0,
                features=feature_vector,
            ))

    diagnostics["samples_emitted"] = len(emitted)
    diagnostics["session_close_source_time_1529_count"] = sum(
        1 for bar in session_close.values() if bar.timestamp.timetz().replace(tzinfo=None) == time(15, 29)
    )
    diagnostics["session_close_source_time_1530_count"] = sum(
        1 for bar in session_close.values() if bar.timestamp.timetz().replace(tzinfo=None) == CLOSE
    )
    diagnostics["missing_session_close_count"] = len(eligible_sessions) - len(session_close)
    denominator = int(diagnostics["target_pairs_possible"])
    diagnostics["target_pair_missing_fraction"] = (diagnostics["target_pairs_missing"] / denominator) if denominator else None
    diagnostics["feature_dimension"] = 2 * lookback_bars
    diagnostics["source_csv_sha256"] = source_csv_sha256
    diagnostics["calendar_sha256"] = calendar_sha
    diagnostics["contract_sha256"] = actual_contract_hash
    _, correction_sha = read_frozen_correction(actual_contract_hash)
    diagnostics["feature_correction_sha256"] = correction_sha
    report = {k: int(v) if isinstance(v, (int,)) else v for k, v in diagnostics.items()}
    report["label_id"] = label_id
    report["lookback_bars"] = lookback_bars
    report["holdout_accessed"] = False
    report["model_fitting_performed"] = False
    report["raw_rows_persisted"] = False
    report["samples_persisted"] = False
    return FeatureBatch(tuple(emitted), report)
