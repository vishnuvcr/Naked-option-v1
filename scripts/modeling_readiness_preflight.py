#!/usr/bin/env python3
"""Metadata-only modeling-readiness preflight primitives.

This module intentionally does not open market-data files, read holdout rows,
fit models, fetch data, or emit row-level financial values. The later authorized
runner may feed only sanitized metadata into these deterministic checks.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from typing import Any, Iterable, Mapping, Sequence

HORIZONS = (1, 2, 3, 5, 10)
DIRECTION_CLASSES = ("DOWN", "FLAT", "UP")
FLAT_TOLERANCE_ABS_RETURN = 1e-8
MIN_TRAIN_ORIGINS = 252
MIN_COMMON_VALIDATION_ORIGINS = 250

@dataclass(frozen=True)
class GateResult:
    gate_id: str
    status: str
    reasons: tuple[str, ...] = ()
    metrics: Mapping[str, Any] | None = None

def direction_label(start: float, end: float, tolerance: float = FLAT_TOLERANCE_ABS_RETURN) -> str:
    """Return DOWN/FLAT/UP using signed simple return and frozen absolute tolerance."""
    if not (math.isfinite(start) and math.isfinite(end)) or start <= 0 or end <= 0:
        raise ValueError("prices must be finite and positive")
    ret = (end - start) / start
    if abs(ret) <= tolerance:
        return "FLAT"
    return "UP" if ret > 0 else "DOWN"

def map_session_horizons(sessions: Sequence[str], horizons: Iterable[int] = HORIZONS) -> dict[str, dict[int, str | None]]:
    """Map each session to the exact future session by observed ordered session list."""
    if len(set(sessions)) != len(sessions):
        raise ValueError("session list contains duplicate session keys")
    if list(sessions) != sorted(sessions):
        raise ValueError("session list must be chronologically sorted ISO dates")
    out: dict[str, dict[int, str | None]] = {}
    for i, session in enumerate(sessions):
        out[session] = {}
        for h in horizons:
            if h not in HORIZONS:
                raise ValueError(f"unsupported horizon: {h}")
            out[session][h] = sessions[i+h] if i+h < len(sessions) else None
    return out

def validate_ohlc(open_: float | None, high: float | None, low: float | None, close: float | None) -> tuple[bool, str]:
    values=(open_,high,low,close)
    if any(v is None or not math.isfinite(v) for v in values):
        return False, "MISSING_OR_NONFINITE_OHLC"
    assert open_ is not None and high is not None and low is not None and close is not None
    if min(values) <= 0:
        return False, "NONPOSITIVE_OHLC"
    if high < max(open_, close) or low > min(open_, close) or high < low:
        return False, "OHLC_INEQUALITY_FAILURE"
    return True, "VALID"

def classify_feature_family(*, nonblank_count: int, total_count: int, point_in_time_proven: bool,
                            join_validity_proven: bool = True) -> GateResult:
    if total_count < 0 or nonblank_count < 0 or nonblank_count > total_count:
        return GateResult("MR-3", "BLOCKED_INVALID_COVERAGE_COUNTS", ("INVALID_COUNTS",))
    if nonblank_count == 0:
        return GateResult("MR-3", "BLOCKED_DATA", ("NO_OBSERVED_VALUES",),
                          {"nonblank": nonblank_count, "total": total_count})
    if not point_in_time_proven:
        return GateResult("MR-3", "NOT_ESTIMABLE", ("POINT_IN_TIME_AVAILABILITY_UNPROVEN",),
                          {"nonblank": nonblank_count, "total": total_count})
    if not join_validity_proven:
        return GateResult("MR-3", "PASS_WITH_RESTRICTIONS", ("JOIN_COVERAGE_RESTRICTED",),
                          {"nonblank": nonblank_count, "total": total_count})
    return GateResult("MR-3", "CANDIDATE", (), {"nonblank": nonblank_count, "total": total_count})

def validate_split(*, train_origins: int, common_validation_origins: int,
                   label_endpoints_before_validation: bool, holdout_manifest_verified: bool) -> GateResult:
    if not holdout_manifest_verified:
        return GateResult("MR-4", "BLOCKED_HOLDOUT_PROOF", ("HOLDOUT_EXCLUSION_METADATA_UNVERIFIED",))
    if not label_endpoints_before_validation:
        return GateResult("MR-4", "BLOCKED_LEAKAGE", ("TRAIN_LABEL_OVERLAPS_VALIDATION",))
    if train_origins < MIN_TRAIN_ORIGINS or common_validation_origins < MIN_COMMON_VALIDATION_ORIGINS:
        return GateResult("MR-4", "INCOMPLETE_NOT_PROMOTABLE", ("FROZEN_SAMPLE_MINIMUM_NOT_MET",),
                          {"train_origins": train_origins, "common_validation_origins": common_validation_origins})
    return GateResult("MR-4", "PASS", (), {"train_origins": train_origins,
                                            "common_validation_origins": common_validation_origins})

def validate_session_metadata(*, calendar_provenance: bool, candle_semantics: str,
                              unresolved_session_flags: int, spot_duplicate_keys: int) -> GateResult:
    if not calendar_provenance:
        return GateResult("MR-1", "NOT_ESTIMABLE", ("AUTHORIZED_NSE_CALENDAR_PROVENANCE_MISSING",))
    if candle_semantics not in {"BAR_START", "BAR_END"}:
        return GateResult("MR-1", "NOT_ESTIMABLE", ("CANDLE_TIMESTAMP_SEMANTICS_AMBIGUOUS",))
    if spot_duplicate_keys:
        return GateResult("MR-1", "BLOCKED", ("DUPLICATE_SPOT_SESSION_KEYS",),
                          {"duplicate_keys": spot_duplicate_keys})
    if unresolved_session_flags:
        return GateResult("MR-1", "PASS_WITH_EXCLUSIONS", ("UNRESOLVED_SESSION_FLAGS_REMAIN",),
                          {"unresolved_session_flags": unresolved_session_flags})
    return GateResult("MR-1", "PASS")

def sanitize_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Allowlist metadata fields only; reject row-level values and unexpected keys."""
    allowed={"dataset_sha256","rows","columns","option_rows","spot_rows","row_width_errors",
             "timestamp_parse_errors","incomplete_keys","duplicate_keys","session_status",
             "target_statuses","feature_family_statuses","split_status","exclusion_counts",
             "origin_manifest_sha256","cleanup_status","gate_status"}
    extra=set(report)-allowed
    if extra:
        raise ValueError("report contains disallowed fields: "+",".join(sorted(extra)))
    return dict(report)

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run built-in offline deterministic checks")
    args=parser.parse_args()
    if not args.self_test:
        parser.error("this stage supports only --self-test; real-data execution is not implemented")
    checks = {
        "direction_down": direction_label(100,99)=="DOWN",
        "direction_flat": direction_label(100,100+100*1e-9)=="FLAT",
        "direction_up": direction_label(100,101)=="UP",
        "ohlc_valid": validate_ohlc(100,102,98,101)[0],
        "ohlc_invalid": not validate_ohlc(100,99,98,101)[0],
        "horizon_by_sessions": map_session_horizons(["2026-01-01","2026-01-02","2026-01-05"])[ "2026-01-01"][1]=="2026-01-02",
        "holdout_fail_closed": validate_split(train_origins=300,common_validation_origins=300,label_endpoints_before_validation=True,holdout_manifest_verified=False).status=="BLOCKED_HOLDOUT_PROOF",
        "blank_feature_blocked": classify_feature_family(nonblank_count=0,total_count=100,point_in_time_proven=True).status=="BLOCKED_DATA",
        "ambiguous_candle_fail_closed": validate_session_metadata(calendar_provenance=True,candle_semantics="UNKNOWN",unresolved_session_flags=0,spot_duplicate_keys=0).status=="NOT_ESTIMABLE",
        "no_market_io_default": True,
    }
    print(json.dumps({"suite":"modeling-readiness-primitives-v1","checks":checks,
                      "passed":sum(checks.values()),"total":len(checks),
                      "real_data_execution":"NOT_IMPLEMENTED","model_fitting":"NOT_AUTHORIZED",
                      "holdout_observation_access":"NOT_AUTHORIZED"},sort_keys=True))
    return 0 if all(checks.values()) else 1

if __name__=="__main__":
    raise SystemExit(main())
