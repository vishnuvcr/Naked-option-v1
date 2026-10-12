#!/usr/bin/env python3
"""Prediction-only Greek feature-study utilities. No network or data access."""
from __future__ import annotations
import argparse, hashlib, io, json, math, os, subprocess, zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
    brier_score_loss, log_loss, roc_auc_score)
from sklearn.linear_model import LogisticRegression

SEED = 42
BOOTSTRAP_REPS = 500
EXPECTED_HORIZONS = {"daily": (1, 2, 3, 5, 10), "intraday": (5, 15, 30, 60, 120)}

DAILY_TIME_CONVENTION = "DATE_ONLY_DAILY_PANEL_TO_CASH_CLOSE_15_30_IST"
FROZEN_PHASE7_COMMIT = "b50be8cfa1ebe008a800e65a53f9c0fb2581aecb"
FROZEN_LABEL_SOURCE_BLOBS = {
    "daily": "0d1d93261fe10b8da47267185651f7ee161c3b46",
    "intraday": "58222be4a95f10c2f1a8bda4597927ff82f18de6",
}
PINNED_ARTIFACTS = {
    "greek": {
        "artifact_id": 11723198817,
        "sha256": "e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736",
        "name": "nifty-1m-greeks-enriched-r3",
    },
    "forecast": {
        "artifact_id": 11638738288,
        "sha256": "3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9",
        "name": "phase7-ensemble-reference",
        "manifest_sha256": "f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091",
        "aggregate_sha256": "96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39",
    },
}
GREEK_SOURCE_PIN = {
    "revision": "0f4800e43e6f96cec0794369d78eb4d3c4211ef5",
    "license": "CC-BY-NC-4.0",
    "source_artifact_id": 11698879857,
    "source_run_id": 38131641336,
    "source_zip_sha256": "40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b",
}
SPOT_FEATURE_COLUMNS = [
    "ret_1", "ret_5", "ret_15", "ret_30", "ret_60",
    "rv20", "rv60", "previous_session_return",
]
GREEK_FEATURE_COLUMNS = [
    "n_call", "n_put", "n_delta_call", "n_delta_put",
    "call_delta_median", "put_delta_median", "delta_imbalance",
    "call_gamma_median", "put_gamma_median",
    "call_theta_per_day_median", "put_theta_per_day_median",
    "call_vega_per_1pct_iv_median", "put_vega_per_1pct_iv_median",
    "call_iv_median", "put_iv_median", "iv_skew_put_minus_call",
    "oi_put_call_ratio", "volume_put_call_ratio",
    "oi_put_call_ratio_denominator_invalid", "volume_put_call_ratio_denominator_invalid",
    "oi_put_call_ratio_missing_side_observations", "volume_put_call_ratio_missing_side_observations",
    "oi_put_call_ratio_put_valid_n", "oi_put_call_ratio_call_valid_n",
    "volume_put_call_ratio_put_valid_n", "volume_put_call_ratio_call_valid_n",
    "n_option_rows_for_provenance",
]

VALID_GREEK_STATUS = {"GREEKS_ESTIMATED_FROM_INVERTED_IV", "GREEKS_ESTIMATED_FROM_SOURCE_IV_FALLBACK"}
PANEL_REQUIRED = {"layer", "horizon", "source_row_index", "decision_timestamp",
                  "label_direction", "future_return", "block_index",
                  *{f"P{i:02d}" for i in range(1, 11)}}

class GateBlocked(RuntimeError):
    """A required scientific or data contract is missing or invalid."""

def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def number(value: Any) -> float:
    try:
        x = float(value)
        return x if math.isfinite(x) else math.nan
    except (TypeError, ValueError, OverflowError):
        return math.nan

def median_min5(values) -> tuple[float, int]:
    arr = np.asarray([number(v) for v in values], dtype=float)
    arr = arr[np.isfinite(arr)]
    return (float(np.median(arr)), len(arr)) if len(arr) >= 5 else (math.nan, len(arr))

def _eligible(row: Mapping[str, Any], side: str) -> bool:
    flags = str(row.get("data_quality_flags", "")).upper()
    return (str(row.get("row_type", "")).upper() == "OPTION"
            and str(row.get("option_type", "")).upper() == side
            and str(row.get("greek_status", "")) in VALID_GREEK_STATUS
            and "NON_TRADING_SESSION" not in flags and "WEEKEND" not in flags)

def _ratio(rows, side, field):
    vals = [number(r.get(field)) for r in rows if str(r.get("option_type", "")).upper() == side]
    vals = [v for v in vals if np.isfinite(v) and v >= 0]
    return (sum(vals) if vals else math.nan, len(vals))

def aggregate_option_snapshot(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate one exact, already timestamp-matched option snapshot only."""
    calls = [r for r in rows if _eligible(r, "CE")]
    puts = [r for r in rows if _eligible(r, "PE")]
    out = {"n_call": len(calls), "n_put": len(puts),
           "n_delta_call": sum(np.isfinite(number(r.get("delta"))) for r in calls),
           "n_delta_put": sum(np.isfinite(number(r.get("delta"))) for r in puts),
           "observed_panel_warning": "PARTIAL_GRID_NOT_FULL_EXCHANGE_CHAIN"}
    fields = {"delta": "delta_median", "gamma": "gamma_median",
              "theta_per_day": "theta_per_day_median",
              "vega_per_1pct_iv": "vega_per_1pct_iv_median",
              "greek_implied_volatility": "iv_median"}
    for side, data in (("call", calls), ("put", puts)):
        for key, suffix in fields.items():
            med, n = median_min5(r.get(key) for r in data)
            name = f"{side}_{suffix}"
            out[name], out[name + "_n"] = med, n
    cd, pd_ = out["call_delta_median"], out["put_delta_median"]
    out["delta_imbalance"] = cd + pd_ if np.isfinite(cd) and np.isfinite(pd_) else math.nan
    civ, piv = out["call_iv_median"], out["put_iv_median"]
    out["iv_skew_put_minus_call"] = piv - civ if np.isfinite(civ) and np.isfinite(piv) else math.nan
    for col, name in (("open_interest", "oi_put_call_ratio"), ("volume", "volume_put_call_ratio")):
        p, pn = _ratio(puts, "PE", col)
        c, cn = _ratio(calls, "CE", col)
        if not pn or not cn or not np.isfinite(p) or not np.isfinite(c):
            val, status = math.nan, "MISSING_VALID_SIDE_OBSERVATIONS"
        elif c <= 0:
            val, status = math.nan, "NONPOSITIVE_CALL_DENOMINATOR"
        else:
            val, status = p / c, "VALID"
        out[name], out[name + "_status"] = val, status
        out[name + "_put_valid_n"], out[name + "_call_valid_n"] = pn, cn
    for outkey, col in (("greek_status_counts", "greek_status"),
                        ("iv_source_counts", "greek_iv_source"),
                        ("expiry_source_counts", "expiry_mapping_source")):
        counts = {}
        for r in rows:
            if str(r.get("row_type", "")).upper() == "OPTION":
                label = str(r.get(col, "")) or "MISSING"
                counts[label] = counts.get(label, 0) + 1
        out[outkey] = counts
        denom = sum(counts.values())
        out[outkey + "_fractions"] = ({k: v / denom for k, v in counts.items()} if denom else {})
    out["n_option_rows_for_provenance"] = sum(str(r.get("row_type", "")).upper() == "OPTION" for r in rows)
    return out

def validate_panel_frame(frame: pd.DataFrame, layer: str, horizon: int) -> dict[str, Any]:
    missing = PANEL_REQUIRED - set(frame.columns)
    if missing:
        raise GateBlocked("PANEL_SCHEMA_MISSING:" + ",".join(sorted(missing)))
    if layer not in EXPECTED_HORIZONS or int(horizon) not in EXPECTED_HORIZONS[layer]:
        raise GateBlocked("UNREGISTERED_LAYER_HORIZON")
    if frame.empty or not frame["layer"].astype(str).eq(layer).all():
        raise GateBlocked("EMPTY_PANEL_OR_WRONG_LAYER")
    h = pd.to_numeric(frame["horizon"], errors="coerce")
    if not h.eq(int(horizon)).all():
        raise GateBlocked("MIXED_OR_WRONG_HORIZON")
    idx = pd.to_numeric(frame["source_row_index"], errors="coerce").to_numpy(float)
    if not np.isfinite(idx).all() or not np.array_equal(idx, np.arange(len(frame), dtype=float)):
        raise GateBlocked("SOURCE_ROW_INDEX_NOT_ZERO_BASED_SEQUENCE")
    ts = pd.to_datetime(frame["decision_timestamp"], errors="coerce", utc=(layer == "intraday"))
    if ts.isna().any() or ts.duplicated().any() or not ts.is_monotonic_increasing:
        raise GateBlocked("DECISION_TIMESTAMP_INVALID_DUPLICATE_OR_UNSORTED")
    y = pd.to_numeric(frame["label_direction"], errors="coerce").to_numpy(float)
    if not np.isin(y[np.isfinite(y)], [0., 1.]).all():
        raise GateBlocked("LABEL_NOT_BINARY_0_1")
    future = pd.to_numeric(frame["future_return"], errors="coerce").to_numpy(float)
    if np.isinf(future).any():
        raise GateBlocked("FUTURE_RETURN_INFINITE")
    bi = pd.to_numeric(frame["block_index"], errors="coerce").to_numpy(float)
    if not np.isfinite(bi).all() or not np.equal(bi, bi.astype(int)).all() or (bi < 0).any():
        raise GateBlocked("BLOCK_INDEX_INVALID")
    uniq = np.unique(bi.astype(int))
    if not np.array_equal(uniq, np.arange(len(uniq))):
        raise GateBlocked("BLOCK_INDEX_NOT_CONTIGUOUS_FROM_ZERO")
    if np.any(np.diff(bi.astype(int)) < 0):
        raise GateBlocked("BLOCK_INDEX_NOT_MONOTONE_WITH_DECISION_TIME")
    for block_id in uniq:
        positions = np.flatnonzero(bi.astype(int) == block_id)
        if len(positions) and int(positions[-1] - positions[0] + 1) != len(positions):
            raise GateBlocked("BLOCK_INDEX_REAPPEARS_AFTER_LATER_BLOCK")
    return {"layer": layer, "horizon": int(horizon), "rows": len(frame),
            "finite_label_rows": int(np.isfinite(y).sum()),
            "missing_label_rows": int((~np.isfinite(y)).sum()),
            "block_count": int(len(uniq)),
            "first_decision_timestamp": str(ts.iloc[0]),
            "last_decision_timestamp": str(ts.iloc[-1]),
            "timestamps_unique_ordered": True}

def verify_pinned_artifact_identity(path: str | Path, artifact_name: str, observed_artifact_id: int) -> dict[str, Any]:
    """Verify an already-downloaded GitHub artifact against the immutable R3/RUN994 pins."""
    if artifact_name not in PINNED_ARTIFACTS:
        raise GateBlocked("UNREGISTERED_ARTIFACT_NAME")
    pin = PINNED_ARTIFACTS[artifact_name]
    try:
        actual_id = int(observed_artifact_id)
    except (TypeError, ValueError):
        raise GateBlocked("OBSERVED_ARTIFACT_ID_INVALID")
    if actual_id != int(pin["artifact_id"]):
        raise GateBlocked(f"ARTIFACT_ID_MISMATCH:{artifact_name}")
    actual_sha = sha256_file(path)
    if actual_sha != pin["sha256"]:
        raise GateBlocked(f"ARTIFACT_SHA256_MISMATCH:{artifact_name}")
    return {
        "artifact_name": artifact_name,
        "artifact_id": actual_id,
        "sha256": actual_sha,
        "verified": True,
        "pinned_source": "PHASE8P_CODE_CONSTANTS",
    }


def _validate_artifact_receipts(receipts: Mapping[str, Any] | None) -> list[str]:
    reasons = []
    if not isinstance(receipts, Mapping) or set(receipts) != {"greek", "forecast"}:
        return ["PINNED_ARTIFACT_RECEIPTS_MISSING_OR_INCOMPLETE"]
    for name, pin in PINNED_ARTIFACTS.items():
        receipt = receipts.get(name)
        if not isinstance(receipt, Mapping):
            reasons.append(f"ARTIFACT_RECEIPT_MISSING:{name}")
            continue
        if (receipt.get("verified") is not True
                or receipt.get("artifact_name") != name
                or receipt.get("artifact_id") != pin["artifact_id"]
                or receipt.get("sha256") != pin["sha256"]):
            reasons.append(f"ARTIFACT_RECEIPT_PIN_MISMATCH:{name}")
    return reasons


def preflight_contract(
    manifest: Mapping[str, Any],
    panels: Sequence[pd.DataFrame],
    *,
    artifact_receipts: Mapping[str, Any] | None = None,
    target_maturity_proof: Mapping[str, Any] | None = None,
    holdout_exclusion_proof: Mapping[str, Any] | None = None,
    target_end_by_panel: Mapping[str, Sequence[Any]] | None = None,
    panel_file_sha256: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Schema/coverage-only decision. This function can never authorize model fitting."""
    reasons: list[str] = []
    reasons.extend(_validate_artifact_receipts(artifact_receipts))
    if manifest.get("status") != "COMPLETE" or manifest.get("schema_version") != 1:
        reasons.append("FROZEN_PANEL_MANIFEST_STATUS_OR_SCHEMA_UNPROVEN")
    if str(manifest.get("commit", "")) != FROZEN_PHASE7_COMMIT:
        reasons.append("FROZEN_PANEL_SOURCE_COMMIT_MISMATCH")
    if not manifest.get("run_id"):
        reasons.append("FROZEN_PANEL_RUN_ID_MISSING")
    if manifest.get("protocol") != "research/phase7/PHASE7_METHOD_SPEC.md":
        reasons.append("FROZEN_PANEL_PROTOCOL_MISMATCH")
    if manifest.get("seed") != SEED:
        reasons.append("FROZEN_PANEL_SEED_MISMATCH")
    if not isinstance(panel_file_sha256, Mapping) or len(panel_file_sha256) != 10:
        reasons.append("TEN_PANEL_FILE_HASHES_REQUIRED")
    elif any(not isinstance(v, str) or len(v) != 64 for v in panel_file_sha256.values()):
        reasons.append("PANEL_FILE_HASH_INVALID")

    if not isinstance(target_maturity_proof, Mapping):
        reasons.append("TARGET_END_AND_LABEL_MATURITY_PROOF_MISSING")
    else:
        if target_maturity_proof.get("daily_label_source_blob_sha1") != FROZEN_LABEL_SOURCE_BLOBS["daily"]:
            reasons.append("DAILY_LABEL_SOURCE_BLOB_NOT_PINNED")
        if target_maturity_proof.get("intraday_label_source_blob_sha1") != FROZEN_LABEL_SOURCE_BLOBS["intraday"]:
            reasons.append("INTRADAY_LABEL_SOURCE_BLOB_NOT_PINNED")
        if target_maturity_proof.get("daily_rule") != "close.shift(-H)":
            reasons.append("DAILY_TARGET_RULE_MISMATCH")
        if target_maturity_proof.get("intraday_rule") != "exact timestamp + H minutes":
            reasons.append("INTRADAY_TARGET_RULE_MISMATCH")
        if target_maturity_proof.get("target_end_checks_passed") is not True:
            reasons.append("TARGET_END_SOURCE_ALIGNMENT_NOT_PROVEN")

    if not isinstance(holdout_exclusion_proof, Mapping):
        reasons.append("PROTECTED_HOLDOUT_EXCLUSION_PROOF_MISSING")
    else:
        if holdout_exclusion_proof.get("proof") != "VERIFIED":
            reasons.append("PROTECTED_HOLDOUT_EXCLUSION_NOT_VERIFIED")
        mask_sha = str(holdout_exclusion_proof.get("mask_sha256", ""))
        if len(mask_sha) != 64 or any(ch not in "0123456789abcdef" for ch in mask_sha.lower()):
            reasons.append("PROTECTED_HOLDOUT_MASK_SHA256_MISSING_OR_INVALID")
        cutoffs = holdout_exclusion_proof.get("cutoff_by_layer")
        if not isinstance(cutoffs, Mapping) or set(cutoffs) != {"daily", "intraday"}:
            reasons.append("PROTECTED_HOLDOUT_CUTOFFS_MISSING")
        if holdout_exclusion_proof.get("source_manifest_sha256") != manifest.get("manifest_sha256"):
            reasons.append("PROTECTED_HOLDOUT_PROOF_NOT_BOUND_TO_FROZEN_MANIFEST")

    summaries = []
    if len(panels) != 10:
        reasons.append("EXPECTED_EXACTLY_10_FROZEN_PANELS")
    found = set()
    for frame in panels:
        try:
            layer = str(frame["layer"].iloc[0])
            horizon = int(frame["horizon"].iloc[0])
            summary = validate_panel_frame(frame, layer, horizon)
            found.add((layer, horizon))
            y = pd.to_numeric(frame["label_direction"], errors="coerce").to_numpy(float)
            future = pd.to_numeric(frame["future_return"], errors="coerce").to_numpy(float)
            finite_y = np.isfinite(y)
            if np.any(finite_y & ~np.isfinite(future)):
                reasons.append(f"FINITE_LABEL_WITHOUT_FUTURE_RETURN:{layer}:H{horizon}")
            nonzero = finite_y & np.isfinite(future) & (future != 0)
            expected = (future[nonzero] > 0).astype(int)
            if not np.array_equal(y[nonzero].astype(int), expected):
                reasons.append(f"LABEL_SIGN_MISMATCH:{layer}:H{horizon}")
            if target_end_by_panel is None:
                reasons.append(f"TARGET_END_VALUES_MISSING:{layer}:H{horizon}")
            else:
                key = f"{layer}:H{horizon}"
                ends = pd.to_datetime(target_end_by_panel.get(key, []), errors="coerce", utc=True)
                decisions = pd.to_datetime(
                    frame["decision_timestamp"],
                    errors="coerce",
                    utc=(layer == "intraday"),
                )
                if len(ends) != len(frame) or ends.isna().any():
                    reasons.append(f"TARGET_END_VECTOR_INVALID:{layer}:H{horizon}")
                else:
                    decision_utc = pd.DatetimeIndex([
                        daily_close_timestamp(x) if layer == "daily" else pd.Timestamp(x).tz_convert("UTC")
                        for x in decisions
                    ])
                    if np.any(ends.asi8 <= decision_utc.asi8):
                        reasons.append(f"TARGET_END_NOT_STRICTLY_AFTER_DECISION:{layer}:H{horizon}")
                    if np.any(finite_y & ends.isna()):
                        reasons.append(f"FINITE_LABEL_WITHOUT_TARGET_END:{layer}:H{horizon}")
            summaries.append(summary)
        except Exception as exc:
            reasons.append(f"PANEL_VALIDATION_FAILED:{type(exc).__name__}:{exc}")
    required = {(layer, h) for layer, hs in EXPECTED_HORIZONS.items() for h in hs}
    if found != required:
        reasons.append("PANEL_LAYER_HORIZON_GRID_MISMATCH")

    pins = {
        name: {"artifact_id": receipts.get(name, {}).get("artifact_id"),
               "sha256": receipts.get(name, {}).get("sha256")}
        for name in ("greek", "forecast")
    } if isinstance(receipts, Mapping) else {}
    return {
        "schema_version": 2,
        "status": "PASS" if not reasons else "BLOCKED",
        "mode": "SCHEMA_COVERAGE_ONLY_NO_MODEL_FIT",
        "forecast_run_id": manifest.get("run_id"),
        "forecast_commit": manifest.get("commit"),
        "forecast_manifest_sha256": manifest.get("manifest_sha256"),
        "input_artifacts": pins,
        "panel_file_sha256": dict(panel_file_sha256 or {}),
        "panel_summaries": summaries,
        "target_maturity_proof": dict(target_maturity_proof or {}),
        "holdout_exclusion_proof": dict(holdout_exclusion_proof or {}),
        "model_fit_authorized": False,
        "holdout_access_authorized": False,
        "option_pnl_authorized": False,
        "strategy_promotion_authorized": False,
        "reasons": sorted(set(reasons)),
    }


def moving_block_indices(n: int, block_len: int, rng: np.random.Generator) -> np.ndarray:
    if n <= 0 or block_len <= 0:
        raise ValueError("n and block_len must be positive")
    L = min(int(block_len), int(n))
    starts = np.arange(0, n - L + 1, dtype=int)
    selected = rng.integers(0, len(starts), size=int(math.ceil(n / L)))
    idx = np.concatenate([np.arange(int(starts[j]), int(starts[j]) + L) for j in selected])[:n]
    if len(idx) != n:
        raise AssertionError("bootstrap index length mismatch")
    return idx

def paired_brier_bootstrap(
    y, p_spot, p_augmented, block_len: int,
    reps: int = BOOTSTRAP_REPS, seed: int = SEED,
    population_n: int | None = None,
    row_positions: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Paired, null-centred one-sided moving-block bootstrap.

    Optional row_positions preserve the original panel's time grid when exact feature
    joins are missing. Blocks are resampled on original panel positions; only
    prespecified matched rows contribute paired loss differences.
    """
    y, p0, p1 = (np.asarray(v, dtype=float) for v in (y, p_spot, p_augmented))
    if not (len(y) == len(p0) == len(p1)) or not len(y):
        raise ValueError("paired arrays must have identical non-zero length")
    if not (np.isfinite(y).all() and np.isfinite(p0).all() and np.isfinite(p1).all()):
        raise ValueError("non-finite paired observations block inference")
    if not np.isin(y, [0., 1.]).all() or ((p0 < 0) | (p0 > 1) | (p1 < 0) | (p1 > 1)).any():
        raise ValueError("invalid labels or probabilities")
    d = (p0 - y) ** 2 - (p1 - y) ** 2
    observed = float(d.mean())
    null_d = d - observed
    if row_positions is None:
        positions = np.arange(len(d), dtype=np.int64)
        pop_n = len(d) if population_n is None else int(population_n)
        if pop_n != len(d):
            raise ValueError("population_n requires explicit original row_positions")
    else:
        positions = np.asarray(row_positions, dtype=np.int64)
        pop_n = int(population_n) if population_n is not None else (int(positions.max()) + 1 if len(positions) else 0)
        if len(positions) != len(d) or pop_n < len(d) or np.any(positions < 0) or np.any(positions >= pop_n):
            raise ValueError("row_positions must align to paired rows and fit inside population_n")
        if len(np.unique(positions)) != len(positions) or np.any(np.diff(positions) <= 0):
            raise ValueError("row_positions must be unique and strictly chronological")
    if pop_n <= 0 or block_len <= 0 or reps <= 0:
        raise ValueError("population_n, block_len and reps must be positive")
    position_to_d = {int(position): i for i, position in enumerate(positions)}
    rng = np.random.default_rng(seed)
    boot_stats = []
    for _ in range(int(reps)):
        sampled_positions = moving_block_indices(pop_n, block_len, rng)
        selected_d = [null_d[position_to_d[int(position)]]
                      for position in sampled_positions if int(position) in position_to_d]
        if not selected_d:
            raise ValueError("bootstrap resample contains no paired rows; inference blocked")
        stat = float(np.mean(selected_d))
        if not np.isfinite(stat):
            raise ValueError("non-finite bootstrap statistic blocks inference")
        boot_stats.append(stat)
    boot = np.asarray(boot_stats, dtype=float)
    exceed = int(np.sum(boot >= observed))
    return {
        "n": len(y),
        "population_n": pop_n,
        "matched_rows": len(y),
        "mean_brier_improvement": observed,
        "null_hypothesis": "H0: E[Brier_spot_only - Brier_spot_plus_greek] <= 0",
        "alternative": "H1: mean paired Brier improvement > 0",
        "block_length": min(int(block_len), pop_n),
        "bootstrap_reps": int(reps),
        "seed": int(seed),
        "null_centered": True,
        "one_sided": True,
        "original_panel_positions_used": row_positions is not None,
        "raw_p_value": (1 + exceed) / (int(reps) + 1),
        "bootstrap_exceedances": exceed,
        "minimum_attainable_p_value": 1 / (int(reps) + 1),
    }


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1 or len(p) == 0 or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("p-values must be a non-empty finite vector in [0,1]")
    order = np.argsort(p, kind="mergesort")
    sorted_adjusted = []
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * float(p[i])))
        sorted_adjusted.append(running)
    out = np.empty(len(p), dtype=float)
    for rank, i in enumerate(order):
        out[i] = sorted_adjusted[rank]
    return out.tolist()

def paired_metrics(y, p_spot, p_augmented) -> dict[str, Any]:
    y, p0, p1 = (np.asarray(v, dtype=float) for v in (y, p_spot, p_augmented))
    if not (len(y) == len(p0) == len(p1)) or not len(y):
        raise ValueError("paired arrays must have identical non-zero length")
    if not (np.isfinite(y).all() and np.isfinite(p0).all() and np.isfinite(p1).all()):
        raise ValueError("same-row finite predictions required")
    if not np.isin(y, [0., 1.]).all() or ((p0 < 0) | (p0 > 1) | (p1 < 0) | (p1 > 1)).any():
        raise ValueError("invalid labels or probabilities")
    out = {"n": len(y), "positive_rate": float(y.mean()),
           "brier_spot_only": float(brier_score_loss(y, p0)),
           "brier_spot_plus_greek": float(brier_score_loss(y, p1)),
           "mean_brier_improvement": float(np.mean((p0-y)**2 - (p1-y)**2)),
           "log_loss_spot_only": float(log_loss(y, np.clip(p0,1e-6,1-1e-6), labels=[0,1])),
           "log_loss_spot_plus_greek": float(log_loss(y, np.clip(p1,1e-6,1-1e-6), labels=[0,1])),
           "balanced_accuracy_spot_only": float(balanced_accuracy_score(y, p0 >= .5)),
           "balanced_accuracy_spot_plus_greek": float(balanced_accuracy_score(y, p1 >= .5))}
    for key, fun in (("roc_auc", roc_auc_score), ("pr_auc", average_precision_score)):
        out[key + "_spot_only"] = float(fun(y, p0)) if len(np.unique(y)) == 2 else None
        out[key + "_spot_plus_greek"] = float(fun(y, p1)) if len(np.unique(y)) == 2 else None
    out["calibration_spot_only"] = calibration_intercept_slope(y, p0)
    out["calibration_spot_plus_greek"] = calibration_intercept_slope(y, p1)
    return out

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_text(ref: str, path: str) -> str:
    root = _repo_root()
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "show", f"{ref}:{path}"],
            stderr=subprocess.PIPE,
        ).decode("utf-8")
    except subprocess.CalledProcessError as exc:
        raise GateBlocked(f"TESTER_EVIDENCE_UNAVAILABLE:{ref}:{path}") from exc


def _git_blob_sha1(ref: str, path: str) -> str:
    root = _repo_root()
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", f"{ref}:{path}"],
            text=True, stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise GateBlocked(f"TESTER_EVIDENCE_BLOB_UNAVAILABLE:{ref}:{path}") from exc


def verify_code_gate_for_preflight() -> dict[str, Any]:
    """Allow schema-only artifact inspection only after an exact tester code PASS.

    The workflow must fetch the isolated tester branch and pin the actual Git blob SHA.
    This function can never authorize model fitting.
    """
    env_names = (
        "PHASE8P_CODE_DECISION_REF",
        "PHASE8P_CODE_DECISION_PATH",
        "PHASE8P_CODE_DECISION_BLOB_SHA1",
    )
    missing = [name for name in env_names if not os.environ.get(name)]
    if missing:
        raise GateBlocked("CODE_GATE_EVIDENCE_ENV_MISSING:" + ",".join(missing))
    ref = os.environ["PHASE8P_CODE_DECISION_REF"]
    path = os.environ["PHASE8P_CODE_DECISION_PATH"]
    expected_blob = os.environ["PHASE8P_CODE_DECISION_BLOB_SHA1"]
    actual_blob = _git_blob_sha1(ref, path)
    if actual_blob != expected_blob:
        raise GateBlocked("CODE_TESTER_DECISION_BLOB_SHA_MISMATCH")
    try:
        decision = json.loads(_git_text(ref, path))
    except json.JSONDecodeError as exc:
        raise GateBlocked("CODE_TESTER_DECISION_JSON_INVALID") from exc
    if decision.get("decision") != "PASS_FOR_CODE_ONLY":
        raise GateBlocked("INDEPENDENT_CODE_GATE_NOT_PASSED")
    current = subprocess.check_output(
        ["git", "-C", str(_repo_root()), "rev-parse", "HEAD"], text=True
    ).strip()
    if decision.get("developer_commit") != current:
        raise GateBlocked("CODE_REVIEW_DEVELOPER_COMMIT_MISMATCH")
    return {"decision": decision, "blob_sha1": actual_blob, "developer_commit": current}


def _read_and_verify_tester_evidence(evidence: Mapping[str, Any], kind: str,
                                     current_commit: str) -> tuple[str, Any]:
    if not isinstance(evidence, Mapping):
        raise GateBlocked(f"{kind}_EVIDENCE_MISSING")
    ref, path, expected_blob = (
        str(evidence.get("git_ref", "")),
        str(evidence.get("path", "")),
        str(evidence.get("blob_sha1", "")),
    )
    if not ref or not path or len(expected_blob) != 40:
        raise GateBlocked(f"{kind}_EVIDENCE_PIN_MALFORMED")
    actual_blob = _git_blob_sha1(ref, path)
    if actual_blob != expected_blob:
        raise GateBlocked(f"{kind}_EVIDENCE_BLOB_SHA_MISMATCH")
    text = _git_text(ref, path)
    if path.endswith(".json"):
        try:
            parsed: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GateBlocked(f"{kind}_EVIDENCE_JSON_INVALID") from exc
    else:
        parsed = text
    if isinstance(parsed, dict) and parsed.get("developer_commit") not in (None, current_commit):
        raise GateBlocked(f"{kind}_EVIDENCE_DEVELOPER_COMMIT_MISMATCH")
    return text, parsed


def enforce_fit_gate(authorization_bundle_path: str | Path | None = None) -> dict[str, Any]:
    """Verify the exact two-role authorization chain; arbitrary booleans/dicts are rejected.

    A workflow must set PHASE8P_AUTHORIZATION_BUNDLE_SHA256 to the exact tester-reviewed
    bundle digest. The bundle pins tester-branch Git blobs, the reviewed developer commit,
    the schema-preflight report SHA-256 and a separate tester decision for that report.
    """
    if authorization_bundle_path is None:
        raise GateBlocked("AUTHORIZATION_BUNDLE_PATH_REQUIRED")
    expected_bundle_sha = os.environ.get("PHASE8P_AUTHORIZATION_BUNDLE_SHA256", "")
    if len(expected_bundle_sha) != 64:
        raise GateBlocked("AUTHORIZATION_BUNDLE_SHA256_ENV_MISSING")
    bundle_path = Path(authorization_bundle_path)
    if not bundle_path.is_file():
        raise GateBlocked("AUTHORIZATION_BUNDLE_FILE_MISSING")
    actual_bundle_sha = sha256_file(bundle_path)
    if actual_bundle_sha != expected_bundle_sha:
        raise GateBlocked("AUTHORIZATION_BUNDLE_SHA256_MISMATCH")
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateBlocked("AUTHORIZATION_BUNDLE_JSON_INVALID") from exc
    if bundle.get("schema_version") != 1:
        raise GateBlocked("AUTHORIZATION_BUNDLE_SCHEMA_MISMATCH")

    current_commit = subprocess.check_output(
        ["git", "-C", str(_repo_root()), "rev-parse", "HEAD"], text=True
    ).strip()
    if bundle.get("developer_commit") != current_commit:
        raise GateBlocked("AUTHORIZATION_BUNDLE_DEVELOPER_COMMIT_MISMATCH")

    scope_text, scope_doc = _read_and_verify_tester_evidence(
        bundle.get("scope_approval"), "SCOPE", current_commit
    )
    if bundle["scope_approval"].get("blob_sha1") != "798008657afe0757c54c9aa7dc5eeb1fade3faf5":
        raise GateBlocked("UNEXPECTED_SCOPE_REVIEW_BLOB")
    if "PASS — SCOPE ONLY, WITH RESTRICTIONS" not in scope_text:
        raise GateBlocked("SCOPE_REVIEW_NOT_PASS")
    scope_blob = subprocess.check_output(
        ["git", "-C", str(_repo_root()), "rev-parse",
         f"{current_commit}:research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md"],
        text=True,
    ).strip()
    if scope_blob != "018500722f88f5fb100a2e24afc3d5d97394631e":
        raise GateBlocked("APPROVED_SCOPE_SOURCE_BLOB_MISMATCH")

    amendment_text, amendment_doc = _read_and_verify_tester_evidence(
        bundle.get("daily_time_amendment_approval"), "DAILY_TIME_AMENDMENT", current_commit
    )
    if bundle["daily_time_amendment_approval"].get("blob_sha1") != "d0f6ad6803c16051bd897f3074682281b3e4c3a0":
        raise GateBlocked("DAILY_TIME_AMENDMENT_REVIEW_BLOB_MISMATCH")
    if "PASS — SCOPE AMENDMENT ONLY, WITH RESTRICTIONS" not in amendment_text:
        raise GateBlocked("DAILY_TIME_AMENDMENT_NOT_PASS")
    proposal_blob = subprocess.check_output(
        ["git", "-C", str(_repo_root()), "rev-parse",
         f"{current_commit}:research/gates/PHASE8P_DAILY_TIMESTAMP_AMENDMENT_R1_2026-10-12.md"],
        text=True,
    ).strip()
    if proposal_blob != "265c6696466b1999371cb4581baf20fbe950d3f1":
        raise GateBlocked("DAILY_TIME_AMENDMENT_PROPOSAL_BLOB_MISMATCH")
    if not isinstance(amendment_doc, str) or "cash-session close" not in amendment_doc.lower():
        raise GateBlocked("DAILY_TIME_AMENDMENT_REVIEW_CONTENT_INVALID")

    code_text, code_doc = _read_and_verify_tester_evidence(
        bundle.get("code_approval"), "CODE", current_commit
    )
    if not isinstance(code_doc, dict) or code_doc.get("decision") != "PASS_FOR_CODE_ONLY":
        raise GateBlocked("INDEPENDENT_CODE_GATE_NOT_PASSED")
    if code_doc.get("developer_commit") != current_commit:
        raise GateBlocked("CODE_APPROVAL_DEVELOPER_COMMIT_MISMATCH")
    reviewed = code_doc.get("reviewed_blobs")
    if not isinstance(reviewed, Mapping):
        raise GateBlocked("CODE_APPROVAL_BLOB_MAP_MISSING")
    required_paths = {
        "scripts/phase8p_greek_prediction.py",
        "scripts/test_phase8p_greek_prediction.py",
        ".github/workflows/phase8p-greek-prediction.yml",
        "research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md",
    }
    if not required_paths.issubset(reviewed):
        raise GateBlocked("CODE_APPROVAL_DOES_NOT_PIN_REQUIRED_FILES")
    for path, expected_blob in reviewed.items():
        actual = subprocess.check_output(
            ["git", "-C", str(_repo_root()), "rev-parse", f"{current_commit}:{path}"],
            text=True,
        ).strip()
        if actual != expected_blob:
            raise GateBlocked("REVIEWED_DEVELOPER_BLOB_MISMATCH:" + path)

    preflight_path = Path(str(bundle.get("preflight_report_path", "")))
    preflight_sha_expected = str(bundle.get("preflight_report_sha256", ""))
    if not preflight_path.is_file() or len(preflight_sha_expected) != 64:
        raise GateBlocked("TESTER_REVIEWED_PREFLIGHT_REPORT_MISSING")
    preflight_sha_actual = sha256_file(preflight_path)
    if preflight_sha_actual != preflight_sha_expected:
        raise GateBlocked("TESTER_REVIEWED_PREFLIGHT_SHA256_MISMATCH")
    try:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateBlocked("PREFLIGHT_REPORT_JSON_INVALID") from exc
    if preflight.get("status") != "PASS" or preflight.get("mode") != "SCHEMA_COVERAGE_ONLY_NO_MODEL_FIT":
        raise GateBlocked("SCHEMA_PREFLIGHT_NOT_PASS")
    if preflight.get("model_fit_authorized") is not False:
        raise GateBlocked("SCHEMA_PREFLIGHT_MUST_NOT_SELF_AUTHORIZE_FIT")
    if preflight.get("holdout_access_authorized") is not False:
        raise GateBlocked("PREFLIGHT_HOLDOUT_FLAG_INVALID")
    if preflight.get("option_pnl_authorized") is not False or preflight.get("strategy_promotion_authorized") is not False:
        raise GateBlocked("PREFLIGHT_OUT_OF_SCOPE_FLAGS_INVALID")
    for name, pin in PINNED_ARTIFACTS.items():
        observed = preflight.get("input_artifacts", {}).get(name, {})
        if observed.get("artifact_id") != pin["artifact_id"] or observed.get("sha256") != pin["sha256"]:
            raise GateBlocked("PREFLIGHT_INPUT_ARTIFACT_PIN_MISMATCH:" + name)
    if not preflight.get("target_maturity_proof", {}).get("target_end_checks_passed"):
        raise GateBlocked("PREFLIGHT_TARGET_MATURITY_PROOF_MISSING")
    holdout_proof = preflight.get("holdout_exclusion_proof", {})
    if (holdout_proof.get("proof") != "VERIFIED"
            or not holdout_proof.get("mask_sha256")
            or not holdout_proof.get("cutoff_by_layer")):
        raise GateBlocked("PREFLIGHT_PROTECTED_HOLDOUT_PROOF_MISSING")

    preflight_text, preflight_decision = _read_and_verify_tester_evidence(
        bundle.get("preflight_approval"), "PREFLIGHT", current_commit
    )
    if not isinstance(preflight_decision, dict):
        raise GateBlocked("PREFLIGHT_TESTER_DECISION_INVALID")
    if preflight_decision.get("decision") != "PASS_PREFLIGHT_ONLY":
        raise GateBlocked("INDEPENDENT_PREFLIGHT_GATE_NOT_PASSED")
    if preflight_decision.get("developer_commit") != current_commit:
        raise GateBlocked("PREFLIGHT_DECISION_DEVELOPER_COMMIT_MISMATCH")
    if preflight_decision.get("preflight_report_sha256") != preflight_sha_actual:
        raise GateBlocked("PREFLIGHT_DECISION_REPORT_DIGEST_MISMATCH")
    if preflight_decision.get("authorize_prediction_fit") is not True:
        raise GateBlocked("PREFLIGHT_TESTER_DID_NOT_AUTHORIZE_PREDICTION_FIT")
    if preflight_decision.get("holdout_access_authorized") is not False:
        raise GateBlocked("PREFLIGHT_TESTER_HOLDOUT_FLAG_INVALID")
    if preflight_decision.get("option_pnl_authorized") is not False or preflight_decision.get("strategy_promotion_authorized") is not False:
        raise GateBlocked("PREFLIGHT_TESTER_OUT_OF_SCOPE_FLAGS_INVALID")

    input_artifacts = bundle.get("input_artifacts", {})
    for name, pin in PINNED_ARTIFACTS.items():
        observed = input_artifacts.get(name, {})
        if observed.get("artifact_id") != pin["artifact_id"] or observed.get("sha256") != pin["sha256"]:
            raise GateBlocked("AUTHORIZATION_BUNDLE_INPUT_PIN_MISMATCH:" + name)
    return {
        "verified": True,
        "developer_commit": current_commit,
        "authorization_bundle_sha256": actual_bundle_sha,
        "preflight_report_sha256": preflight_sha_actual,
        "preflight": preflight,
        "scope_doc": scope_doc,
        "daily_amendment_doc": amendment_doc,
        "code_decision": code_doc,
        "preflight_decision": preflight_decision,
        "input_artifacts": input_artifacts,
    }


def calibration_intercept_slope(y, p):
    """Fit diagnostic calibration of observed labels on prediction logits."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    if len(y) != len(p) or len(y) < 10 or not (np.isfinite(y).all() and np.isfinite(p).all()):
        return {"intercept": None, "slope": None}
    if len(np.unique(y)) != 2:
        return {"intercept": None, "slope": None}
    p = np.clip(p, 1e-6, 1 - 1e-6)
    logit = np.log(p / (1 - p)).reshape(-1, 1)
    model = LogisticRegression(penalty="l2", C=1e6, solver="lbfgs", max_iter=1000, random_state=SEED)
    model.fit(logit, y.astype(int))
    return {"intercept": float(model.intercept_[0]), "slope": float(model.coef_[0, 0])}

def exact_snapshot_rows(rows, decision_timestamp):
    """Select only OPTION rows whose recorded Greek valuation instant equals decision UTC."""
    decision = pd.Timestamp(decision_timestamp)
    if decision.tzinfo is None:
        raise GateBlocked("DECISION_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    decision_epoch = decision.tz_convert("UTC").timestamp()
    result = []
    for row in rows:
        row_type = str(row.get("row_type", "OPTION")).upper()
        if row_type != "OPTION":
            # SPOT rows deliberately have no option Greek valuation offset.
            continue
        start = number(row.get("timestamp_epoch"))
        offset = number(row.get("greek_valuation_offset_seconds"))
        if not np.isfinite(start) or not np.isfinite(offset):
            raise GateBlocked("OPTION_GREEK_VALUATION_TIMESTAMP_FIELDS_MISSING")
        if not math.isclose(offset, 60.0, rel_tol=0.0, abs_tol=1e-9):
            raise GateBlocked("UNREGISTERED_GREEK_VALUATION_OFFSET")
        if start > 1e12:
            start = math.floor(start / 1000.0)
        valuation = start + offset
        if math.isclose(valuation, decision_epoch, rel_tol=0.0, abs_tol=1e-6):
            result.append(row)
    return result


def daily_target_end_dates(decision_dates, source_dates, horizon):
    """Reproduce the frozen daily make_label shift(-H) row relationship."""
    src = pd.DatetimeIndex(pd.to_datetime(source_dates, errors="raise")).normalize()
    if src.has_duplicates or not src.is_monotonic_increasing:
        raise GateBlocked("DAILY_SOURCE_DATES_MUST_BE_UNIQUE_AND_SORTED")
    lookup = {stamp: i for i, stamp in enumerate(src)}
    result = []
    for raw in decision_dates:
        stamp = pd.Timestamp(raw)
        if stamp.tzinfo is not None:
            raise GateBlocked("DAILY_DATE_HAS_UNEXPECTED_TIMEZONE")
        stamp = stamp.normalize()
        pos = lookup.get(stamp)
        target = src[pos + int(horizon)] if pos is not None and pos + int(horizon) < len(src) else pd.NaT
        result.append(target)
    return pd.DatetimeIndex(result)

def intraday_target_end_timestamps(decision_timestamps, source_timestamps, horizon):
    """Reproduce the frozen intraday label's exact timestamp + H-minute lookup."""
    src = pd.DatetimeIndex(pd.to_datetime(source_timestamps, utc=True, errors="raise"))
    if src.has_duplicates or not src.is_monotonic_increasing:
        raise GateBlocked("INTRADAY_SOURCE_TIMESTAMPS_MUST_BE_UNIQUE_AND_SORTED")
    available = set(src.asi8.tolist())
    out = []
    for raw in decision_timestamps:
        decision = pd.Timestamp(raw)
        if decision.tzinfo is None:
            raise GateBlocked("INTRADAY_DECISION_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
        target = decision.tz_convert("UTC") + pd.Timedelta(minutes=int(horizon))
        out.append(target if target.value in available else pd.NaT)
    return pd.DatetimeIndex(out)

def build_spot_features(spot_rows, decision_timestamps, daily=False):
    """Build fixed backward-only spot features; no interpolation or cross-session minute lags."""
    required = {"timestamp_epoch", "session_date", "nifty_close"}
    if required - set(spot_rows.columns):
        raise GateBlocked("SPOT_SCHEMA_MISSING:" + ",".join(sorted(required - set(spot_rows.columns))))
    spot = spot_rows.copy()
    spot["timestamp_epoch"] = pd.to_numeric(spot["timestamp_epoch"], errors="coerce")
    spot["nifty_close"] = pd.to_numeric(spot["nifty_close"], errors="coerce")
    spot = spot[np.isfinite(spot["timestamp_epoch"]) & np.isfinite(spot["nifty_close"]) & (spot["nifty_close"] > 0)].copy()
    spot["timestamp_epoch"] = np.where(spot["timestamp_epoch"] > 1e12,
                                       np.floor(spot["timestamp_epoch"] / 1000), spot["timestamp_epoch"])
    spot["bar_end_epoch"] = spot["timestamp_epoch"] + 60
    spot["session_date"] = pd.to_datetime(spot["session_date"], errors="coerce").dt.normalize()
    spot = spot.dropna(subset=["session_date"]).sort_values("bar_end_epoch").drop_duplicates("bar_end_epoch", keep="last").reset_index(drop=True)
    if spot.empty:
        raise GateBlocked("NO_VALID_SPOT_BARS")
    ends = spot["bar_end_epoch"].to_numpy(float)
    closes = spot["nifty_close"].to_numpy(float)
    sessions = spot["session_date"].to_numpy()
    logc = np.log(closes)
    ret = np.full(len(spot), np.nan)
    for i in range(1, len(spot)):
        if ends[i] - ends[i-1] == 60 and sessions[i] == sessions[i-1]:
            ret[i] = logc[i] - logc[i-1]
    session_closes = spot.groupby("session_date", sort=True).tail(1).sort_values("session_date")
    session_dates = session_closes["session_date"].to_numpy()
    session_prices = session_closes["nifty_close"].to_numpy(float)
    ret_by_date = {pd.Timestamp(d): j for j, d in enumerate(session_dates)}
    output = []
    for raw in decision_timestamps:
        decision = pd.Timestamp(raw)
        if decision.tzinfo is None:
            raise GateBlocked("DECISION_TIMESTAMP_MUST_BE_TIMEZONE_AWARE_FOR_SPOT_FEATURES")
        epoch = decision.tz_convert("UTC").timestamp()
        i = int(np.searchsorted(ends, epoch, side="right") - 1)
        row = {"decision_timestamp_utc": decision.tz_convert("UTC").isoformat()}
        if i < 0 or abs(ends[i] - epoch) > 1e-6:
            # Same timestamp grid is required; do not use nearest/as-of bars.
            row["spot_exact_bar_missing"] = 1
            for name in ("ret_1", "ret_5", "ret_15", "ret_30", "ret_60", "rv20", "rv60", "previous_session_return"):
                row[name] = math.nan
            output.append(row)
            continue
        row["spot_exact_bar_missing"] = 0
        for lag in (1, 5, 15, 30, 60):
            j = i - lag
            if j >= 0 and sessions[j] == sessions[i] and np.all(np.diff(ends[j:i+1]) == 60):
                row[f"ret_{lag}"] = float(logc[i] - logc[j])
            else:
                row[f"ret_{lag}"] = math.nan
        for window in (20, 60):
            vals = ret[max(0, i-window+1):i+1]
            row[f"rv{window}"] = float(np.std(vals, ddof=1)) if len(vals) == window and np.isfinite(vals).all() else math.nan
        today = pd.Timestamp(sessions[i])
        prev = np.flatnonzero(session_dates < today)
        if len(prev) >= 2 and session_prices[prev[-2]] > 0 and session_prices[prev[-1]] > 0:
            row["previous_session_return"] = float(np.log(session_prices[prev[-1]] / session_prices[prev[-2]]))
        else:
            row["previous_session_return"] = math.nan
        output.append(row)
    return pd.DataFrame(output)

def daily_close_timestamp(raw_date):
    """Map a date-only daily cash-index decision to the tester-approved 15:30 IST close."""
    stamp = pd.Timestamp(raw_date)
    if pd.isna(stamp):
        raise GateBlocked("DAILY_DECISION_DATE_MISSING")
    if stamp.tzinfo is not None:
        raise GateBlocked("DAILY_DECISION_DATE_MUST_BE_DATE_ONLY")
    local = stamp.normalize().tz_localize("Asia/Kolkata") + pd.Timedelta(hours=15, minutes=30)
    return local.tz_convert("UTC")


def build_daily_spot_features(spot_rows, decision_dates):
    """Build daily features using the approved cash-close timestamp convention."""
    decisions = [daily_close_timestamp(x) for x in decision_dates]
    features = build_spot_features(spot_rows, decisions, daily=True)
    features["daily_decision_time_convention"] = DAILY_TIME_CONVENTION
    return features


def canonical_panel_timestamps(frame: pd.DataFrame, layer: str) -> pd.DatetimeIndex:
    if "decision_timestamp" not in frame:
        raise GateBlocked("DECISION_TIMESTAMP_FIELD_MISSING")
    if layer == "intraday":
        return pd.DatetimeIndex(pd.to_datetime(frame["decision_timestamp"], errors="raise", utc=True))
    if layer == "daily":
        return pd.DatetimeIndex([daily_close_timestamp(x) for x in frame["decision_timestamp"]])
    raise GateBlocked("UNREGISTERED_LAYER")


def _feature_epoch_column(frame: pd.DataFrame, name: str = "decision_timestamp_utc") -> np.ndarray:
    if name not in frame:
        raise GateBlocked("FEATURE_DECISION_TIMESTAMP_MISSING:" + name)
    ts = pd.DatetimeIndex(pd.to_datetime(frame[name], errors="raise", utc=True))
    if ts.has_duplicates or not ts.is_monotonic_increasing:
        raise GateBlocked("FEATURE_DECISION_TIMESTAMPS_DUPLICATE_OR_UNSORTED")
    return ts.asi8


def build_option_feature_frame(
    option_parts: Iterable[pd.DataFrame],
    decision_timestamps,
    spot_rows_sink: list[pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Aggregate exact-time Greek snapshots while only retaining matching OPTION rows.

    Each input DataFrame may contain both OPTION and SPOT records from one authenticated
    encrypted monthly part. Non-option records are copied to the optional spot sink and
    never subjected to Greek-offset validation.
    """
    decisions = pd.DatetimeIndex(pd.to_datetime(list(decision_timestamps), errors="raise", utc=True))
    if decisions.has_duplicates:
        decisions = decisions.drop_duplicates().sort_values()
    requested = set((decisions.asi8 // 1_000_000_000).tolist())
    groups: dict[int, list[dict[str, Any]]] = {}
    seen_contracts: set[tuple[Any, ...]] = set()
    option_rows_scanned = 0
    option_rows_exact = 0
    contract_key_fields = ("timestamp_epoch", "expiry_date", "expiry_flag",
                           "expiry_code", "returned_strike", "option_type")
    for part_number, frame in enumerate(option_parts):
        if not isinstance(frame, pd.DataFrame) or "row_type" not in frame:
            raise GateBlocked(f"COMPOSITE_PART_SCHEMA_INVALID:{part_number}")
        types = frame["row_type"].fillna("").astype(str).str.upper()
        spots = frame.loc[types.eq("SPOT")].copy()
        if spot_rows_sink is not None and not spots.empty:
            spot_rows_sink.append(spots)
        options = frame.loc[types.eq("OPTION")].copy()
        if options.empty:
            continue
        required = {"timestamp_epoch", "greek_valuation_offset_seconds", *contract_key_fields}
        missing = required - set(options.columns)
        if missing:
            raise GateBlocked("OPTION_PART_REQUIRED_FIELDS_MISSING:" + ",".join(sorted(missing)))
        start = pd.to_numeric(options["timestamp_epoch"], errors="coerce").to_numpy(float)
        offset = pd.to_numeric(options["greek_valuation_offset_seconds"], errors="coerce").to_numpy(float)
        if np.any(~np.isfinite(start)) or np.any(~np.isfinite(offset)):
            raise GateBlocked(f"OPTION_TIMESTAMP_OR_VALUATION_OFFSET_MISSING:PART{part_number}")
        start = np.where(start > 1e12, np.floor(start / 1000.0), start)
        if np.any(~np.isclose(offset, 60.0, rtol=0.0, atol=1e-9)):
            raise GateBlocked(f"UNREGISTERED_GREEK_VALUATION_OFFSET:PART{part_number}")
        valuation = start + offset
        exact = np.isin(valuation.astype(np.int64), np.fromiter(requested, dtype=np.int64)) if requested else np.zeros(len(options), dtype=bool)
        option_rows_scanned += len(options)
        if not exact.any():
            continue
        selected = options.loc[exact].copy()
        selected["_phase8p_start_epoch_seconds"] = start[exact].astype(np.int64)
        selected["_phase8p_valuation_epoch_seconds"] = valuation[exact].astype(np.int64)
        # Detect duplicate contract-time rows across and within monthly parts before aggregation.
        for row in selected.to_dict("records"):
            key_values = []
            for field in contract_key_fields:
                value = row.get(field)
                if value is None or (isinstance(value, float) and not np.isfinite(value)):
                    key_values.append("MISSING" if field != "timestamp_epoch" else None)
                else:
                    key_values.append(str(value))
            key = tuple(key_values)
            if key in seen_contracts:
                raise GateBlocked("DUPLICATE_OPTION_CONTRACT_TIMESTAMP_ACROSS_PARTS")
            seen_contracts.add(key)
            epoch = int(row["_phase8p_valuation_epoch_seconds"])
            groups.setdefault(epoch, []).append(row)
            option_rows_exact += 1

    records = []
    decision_seconds = (decisions.asi8 // 1_000_000_000).astype(np.int64)
    for epoch in decision_seconds:
        rows = groups.get(int(epoch), [])
        summary = aggregate_option_snapshot(rows) if rows else {
            "n_call": 0, "n_put": 0, "n_delta_call": 0, "n_delta_put": 0,
            "observed_panel_warning": "PARTIAL_GRID_NOT_FULL_EXCHANGE_CHAIN",
            "n_option_rows_for_provenance": 0, "greek_status_counts": {},
            "iv_source_counts": {}, "expiry_source_counts": {},
            "greek_status_counts_fractions": {}, "iv_source_counts_fractions": {},
            "expiry_source_counts_fractions": {},
        }
        flat: dict[str, Any] = {
            "decision_timestamp_utc": pd.Timestamp(int(epoch), unit="s", tz="UTC").isoformat(),
            "decision_epoch_seconds": int(epoch),
            "greek_exact_snapshot_missing": int(not bool(rows)),
            "n_option_rows_exact_snapshot": int(len(rows)),
        }
        for key, value in summary.items():
            if isinstance(value, dict):
                continue
            if isinstance(value, str):
                if key.endswith("_status"):
                    base = key[:-len("_status")]
                    flat[base + "_denominator_invalid"] = int(value != "VALID")
                    flat[base + "_missing_side_observations"] = int(value == "MISSING_VALID_SIDE_OBSERVATIONS")
                continue
            flat[key] = value
        for summary_key, prefix in (
            ("greek_status_counts_fractions", "greek_status_fraction"),
            ("iv_source_counts_fractions", "iv_source_fraction"),
            ("expiry_source_counts_fractions", "expiry_source_fraction"),
        ):
            for label, proportion in summary.get(summary_key, {}).items():
                clean = "".join(ch if ch.isalnum() else "_" for ch in str(label)).strip("_")
                flat[f"{prefix}_{clean}"] = float(proportion)
        records.append(flat)
    result = pd.DataFrame(records)
    if result.empty:
        return pd.DataFrame(columns=["decision_timestamp_utc", "decision_epoch_seconds", "greek_exact_snapshot_missing"])
    if result["decision_epoch_seconds"].duplicated().any():
        raise GateBlocked("OPTION_FEATURE_FRAME_HAS_DUPLICATE_DECISION_TIME")
    result.attrs["coverage"] = {
        "requested_decision_instants": int(len(result)),
        "exact_snapshot_instants": int((result["greek_exact_snapshot_missing"] == 0).sum()),
        "missing_exact_snapshot_instants": int((result["greek_exact_snapshot_missing"] == 1).sum()),
        "option_rows_scanned": int(option_rows_scanned),
        "option_rows_at_exact_requested_instants": int(option_rows_exact),
        "coverage_unit": "exact Greek valuation instant (start timestamp + recorded 60 seconds)",
        "grid_limitation": "PARTIAL_GRID_NOT_FULL_EXCHANGE_CHAIN",
    }
    return result


def align_features_to_prediction_panel(
    panel: pd.DataFrame,
    spot_feature_frame: pd.DataFrame,
    greek_feature_frame: pd.DataFrame,
    layer: str,
    source_timestamps=None,
) -> pd.DataFrame:
    """Exact one-to-one panel/feature alignment plus the frozen label-end timestamp."""
    if panel.empty:
        raise GateBlocked("EMPTY_PREDICTION_PANEL")
    horizon = int(panel["horizon"].iloc[0])
    summary = validate_panel_frame(panel, layer, horizon)
    decisions = canonical_panel_timestamps(panel, layer)
    if decisions.has_duplicates or not decisions.is_monotonic_increasing:
        raise GateBlocked("PANEL_DECISION_TIMES_DUPLICATE_OR_UNSORTED")
    out = panel.reset_index(drop=True).copy()
    out["_phase8p_row_position"] = np.arange(len(out), dtype=np.int64)
    out["decision_timestamp_utc"] = decisions
    decision_epoch = decisions.asi8 // 1_000_000_000
    out["_phase8p_decision_epoch_seconds"] = decision_epoch

    spot = spot_feature_frame.copy()
    spot_epoch = _feature_epoch_column(spot)
    if len(np.unique(spot_epoch)) != len(spot_epoch):
        raise GateBlocked("SPOT_FEATURE_FRAME_DUPLICATE_DECISION_TIME")
    spot["_phase8p_decision_epoch_seconds"] = spot_epoch // 1_000_000_000
    spot = spot.drop(columns=["decision_timestamp_utc"], errors="ignore")
    out = out.merge(spot, on="_phase8p_decision_epoch_seconds", how="left",
                    validate="one_to_one", suffixes=("", "_spot"))
    if "spot_exact_bar_missing" not in out:
        out["spot_exact_bar_missing"] = 1
    out["spot_exact_bar_missing"] = pd.to_numeric(out["spot_exact_bar_missing"], errors="coerce").fillna(1).astype(int)

    greek = greek_feature_frame.copy()
    greek_epoch = _feature_epoch_column(greek)
    if len(np.unique(greek_epoch)) != len(greek_epoch):
        raise GateBlocked("GREEK_FEATURE_FRAME_DUPLICATE_DECISION_TIME")
    greek["_phase8p_decision_epoch_seconds"] = greek_epoch // 1_000_000_000
    greek = greek.drop(columns=["decision_timestamp_utc"], errors="ignore")
    greek_columns = [c for c in greek.columns if c != "_phase8p_decision_epoch_seconds"]
    out = out.merge(greek, on="_phase8p_decision_epoch_seconds", how="left",
                    validate="one_to_one", suffixes=("", "_greek"))
    if "greek_exact_snapshot_missing" not in out:
        out["greek_exact_snapshot_missing"] = 1
    out["greek_exact_snapshot_missing"] = pd.to_numeric(out["greek_exact_snapshot_missing"], errors="coerce").fillna(1).astype(int)

    if layer == "daily":
        date_values = panel["decision_timestamp"].tolist()
        target_dates = daily_target_end_dates(date_values, date_values, horizon)
        target_end = []
        for date_value in target_dates:
            target_end.append(pd.NaT if pd.isna(date_value) else daily_close_timestamp(date_value))
        target_end = pd.DatetimeIndex(target_end)
    else:
        if source_timestamps is None:
            raise GateBlocked("INTRADAY_FULL_SOURCE_TIMESTAMPS_REQUIRED_FOR_TARGET_END")
        target_end = intraday_target_end_timestamps(decisions, source_timestamps, horizon)
    out["target_end_timestamp_utc"] = target_end
    y = pd.to_numeric(out["label_direction"], errors="coerce").to_numpy(float)
    if np.any(np.isfinite(y) & pd.isna(target_end)):
        raise GateBlocked("FINITE_LABEL_WITHOUT_PROVABLE_TARGET_END")
    finite = np.isfinite(y)
    end_epoch = pd.DatetimeIndex(target_end).asi8
    dec_epoch = decisions.asi8
    if np.any(finite & (end_epoch <= dec_epoch)):
        raise GateBlocked("TARGET_END_NOT_STRICTLY_AFTER_DECISION")
    out["source_panel_row_count"] = summary["rows"]
    return out


def _walk_forward_predict_core(
    y, target_end, decision_time, block_index, x_spot, x_augmented, layer,
    minimum_training_rows: int = 1000,
) -> dict[str, Any]:
    """Internal model core. Production entry points must call enforce_fit_gate first."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    y = np.asarray(y, dtype=float)
    target_end = pd.to_datetime(target_end, errors="raise", utc=True)
    decision_time = pd.to_datetime(decision_time, errors="raise", utc=True)
    blocks = np.asarray(block_index, dtype=int)
    if not (len(y) == len(target_end) == len(decision_time) == len(blocks) == len(x_spot) == len(x_augmented)):
        raise GateBlocked("PANEL_TARGET_FEATURE_LENGTH_MISMATCH")
    if decision_time.isna().any() or not decision_time.is_monotonic_increasing or decision_time.has_duplicates:
        raise GateBlocked("DECISION_TIME_ORDER_INVALID")
    finite_y = np.isfinite(y)
    if np.any(finite_y & target_end.isna()):
        raise GateBlocked("FINITE_LABEL_WITHOUT_TARGET_END")
    if not np.isin(y[finite_y], [0., 1.]).all():
        raise GateBlocked("LABEL_NOT_BINARY_0_1")
    if len(blocks) == 0 or np.any(blocks < 0) or not np.array_equal(np.unique(blocks), np.arange(len(np.unique(blocks)))):
        raise GateBlocked("BLOCK_INDEX_NOT_CONTIGUOUS")
    if np.any(np.diff(blocks) < 0):
        raise GateBlocked("BLOCK_INDEX_NOT_MONOTONE_WITH_DECISION_TIME")
    for b in np.unique(blocks):
        positions = np.flatnonzero(blocks == b)
        if int(positions[-1] - positions[0] + 1) != len(positions):
            raise GateBlocked("BLOCK_INDEX_REAPPEARS_AFTER_LATER_BLOCK")
    if not x_spot.index.equals(pd.RangeIndex(len(y))) or not x_augmented.index.equals(pd.RangeIndex(len(y))):
        raise GateBlocked("FEATURES_NOT_ROW_ALIGNED_TO_FROZEN_PANEL")
    if minimum_training_rows < 1:
        raise GateBlocked("MINIMUM_TRAINING_ROWS_INVALID")
    specs = {
        "logistic": lambda: Pipeline([
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(penalty="l2", C=1.0, solver="liblinear",
                class_weight=None, max_iter=1000, tol=1e-4, random_state=SEED)),
        ]),
        "hist_gradient_boosting": lambda: Pipeline([
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("model", HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03,
                max_leaf_nodes=15, min_samples_leaf=30, l2_regularization=0.0,
                max_bins=255, early_stopping=False, class_weight=None, random_state=SEED)),
        ]),
    }
    outputs = {}
    for model_name, factory in specs.items():
        p_spot = np.full(len(y), np.nan)
        p_augmented = np.full(len(y), np.nan)
        fit_blocks = 0
        blocked_blocks = []
        for b in np.unique(blocks):
            test = np.flatnonzero(blocks == b)
            if not len(test):
                continue
            cutoff = decision_time[test[0]]
            train = np.flatnonzero((blocks < b) & finite_y & (target_end < cutoff))
            if len(train) < minimum_training_rows:
                blocked_blocks.append({"block": int(b), "reason": "INSUFFICIENT_MATURE_TRAIN_ROWS",
                                       "n_train": int(len(train))})
                continue
            if len(np.unique(y[train])) < 2:
                raise GateBlocked(f"SINGLE_CLASS_TRAINING_BLOCK:{model_name}:{int(b)}")
            models = []
            try:
                for features in (x_spot, x_augmented):
                    model = factory()
                    with warnings.catch_warnings():
                        warnings.simplefilter("error", ConvergenceWarning)
                        model.fit(features.iloc[train], y[train].astype(int))
                    models.append(model)
                p0 = models[0].predict_proba(x_spot.iloc[test])[:, 1]
                p1 = models[1].predict_proba(x_augmented.iloc[test])[:, 1]
            except Exception as exc:
                raise GateBlocked(f"MODEL_FIT_OR_CONVERGENCE_FAILED:{model_name}:BLOCK{int(b)}:{type(exc).__name__}") from exc
            if not (np.isfinite(p0).all() and np.isfinite(p1).all()):
                raise GateBlocked(f"NONFINITE_PREDICTION:{model_name}:{int(b)}")
            p_spot[test] = p0
            p_augmented[test] = p1
            fit_blocks += 1
        outputs[model_name] = {
            "p_spot": p_spot,
            "p_augmented": p_augmented,
            "fit_blocks": int(fit_blocks),
            "blocked_blocks": blocked_blocks,
        }
    return outputs


def walk_forward_predict(
    y, target_end, decision_time, block_index, x_spot, x_augmented, layer,
    authorization_bundle_path: str | Path | None = None,
) -> dict[str, Any]:
    """Authorized production wrapper; caller booleans and arbitrary dicts are not accepted."""
    enforce_fit_gate(authorization_bundle_path)
    return _walk_forward_predict_core(
        y, target_end, decision_time, block_index, x_spot, x_augmented, layer,
        minimum_training_rows=1000,
    )


def write_aggregate_only_report(report: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    """Write only scalar aggregate results and hashes; reject row-level/raw payloads."""
    forbidden = {
        "raw_rows", "contract_rows", "option_contracts", "prediction_vector",
        "feature_matrix", "raw_predictions", "raw_features", "decrypted_csv",
        "per_contract_details", "option_rows_data", "spot_rows_data",
    }
    def walk(value, location="report"):
        if isinstance(value, (pd.DataFrame, pd.Series, np.ndarray)):
            raise GateBlocked("AGGREGATE_REPORT_CONTAINS_RAW_ARRAY:" + location)
        if isinstance(value, Mapping):
            for key, child in value.items():
                if str(key).lower() in forbidden:
                    raise GateBlocked("AGGREGATE_REPORT_FORBIDDEN_FIELD:" + str(key))
                walk(child, location + "." + str(key))
        elif isinstance(value, (list, tuple)):
            for i, child in enumerate(value):
                walk(child, f"{location}[{i}]")
        elif isinstance(value, np.generic):
            walk(value.item(), location)
        elif not (value is None or isinstance(value, (str, bool, int, float))):
            raise GateBlocked("AGGREGATE_REPORT_UNSUPPORTED_VALUE:" + location)
    walk(report)
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload + "\n", encoding="utf-8")
    return {"path": str(target), "sha256": sha256_file(target), "bytes": target.stat().st_size}


def _flatten_spot_frames(daily_features: pd.DataFrame, intraday_features: pd.DataFrame) -> pd.DataFrame:
    frames = [frame for frame in (daily_features, intraday_features) if frame is not None and not frame.empty]
    if not frames:
        raise GateBlocked("NO_SPOT_FEATURE_ROWS_BUILT")
    combined = pd.concat(frames, ignore_index=True, sort=False)
    epochs = _feature_epoch_column(combined)
    combined["_phase8p_feature_epoch"] = epochs // 1_000_000_000
    out = []
    for _, group in combined.groupby("_phase8p_feature_epoch", sort=True, dropna=False):
        if len(group) > 1:
            cols = [c for c in SPOT_FEATURE_COLUMNS + ["spot_exact_bar_missing"] if c in group]
            first = group.iloc[0][cols]
            for _, row in group.iloc[1:].iterrows():
                for col in cols:
                    a, b = first[col], row[col]
                    if pd.isna(a) and pd.isna(b):
                        continue
                    if pd.isna(a) != pd.isna(b) or (not pd.isna(a) and not np.isclose(float(a), float(b), rtol=0, atol=1e-12)):
                        raise GateBlocked("DAILY_INTRADAY_SPOT_FEATURES_DISAGREE_AT_SHARED_CLOSE")
            out.append(group.iloc[0])
        else:
            out.append(group.iloc[0])
    merged = pd.DataFrame(out).drop(columns=["_phase8p_feature_epoch"], errors="ignore").reset_index(drop=True)
    merged["decision_timestamp_utc"] = pd.to_datetime(merged["decision_timestamp_utc"], utc=True)
    return merged.sort_values("decision_timestamp_utc").reset_index(drop=True)


def _panel_key(layer: str, horizon: int) -> str:
    return f"{layer}:H{int(horizon)}"


def _numeric_features_for_frame(frame: pd.DataFrame, names: Sequence[str]) -> pd.DataFrame:
    missing = [name for name in names if name not in frame.columns]
    if missing:
        # Missing registered Greek fields are explicit missing features; no alternate field is substituted.
        frame = frame.copy()
        for name in missing:
            frame[name] = np.nan
    out = frame[list(names)].copy().reset_index(drop=True)
    for column in out:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def _run_prediction_study_authorized(
    panels: Mapping[str, pd.DataFrame],
    spot_rows: pd.DataFrame,
    greek_features: pd.DataFrame,
    spot_features: pd.DataFrame,
    panel_file_sha256: Mapping[str, str],
    authorization: Mapping[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    preflight = authorization["preflight"]
    if set(panels) != {_panel_key(layer, h) for layer, hs in EXPECTED_HORIZONS.items() for h in hs}:
        raise GateBlocked("RUN_REQUIRES_ALL_10_FROZEN_PANELS")
    expected_panel_hashes = preflight.get("panel_file_sha256", {})
    if not isinstance(expected_panel_hashes, Mapping) or dict(expected_panel_hashes) != dict(panel_file_sha256):
        raise GateBlocked("PANEL_FILE_HASHES_DIFFER_FROM_TESTER_APPROVED_PREFLIGHT")
    holdout = preflight.get("holdout_exclusion_proof", {})
    cutoff_by_layer = holdout.get("cutoff_by_layer")
    if not isinstance(cutoff_by_layer, Mapping) or set(cutoff_by_layer) != {"daily", "intraday"}:
        raise GateBlocked("TESTER_PREFLIGHT_HAS_NO_VALID_HOLDOUT_CUTOFF")
    cell_records = []
    valid_inference_cells = []
    source_timestamps = pd.to_numeric(spot_rows["timestamp_epoch"], errors="coerce").to_numpy(float)
    source_timestamps = np.where(source_timestamps > 1e12, np.floor(source_timestamps / 1000), source_timestamps)
    source_timestamps = pd.to_datetime(source_timestamps[np.isfinite(source_timestamps)], unit="s", utc=True).sort_values()
    for layer, horizons in EXPECTED_HORIZONS.items():
        for horizon in horizons:
            key = _panel_key(layer, horizon)
            panel = panels[key]
            aligned = align_features_to_prediction_panel(
                panel, spot_features, greek_features, layer,
                source_timestamps=source_timestamps if layer == "intraday" else None,
            )
            decision_time = pd.DatetimeIndex(pd.to_datetime(aligned["decision_timestamp_utc"], utc=True))
            target_end = pd.DatetimeIndex(pd.to_datetime(aligned["target_end_timestamp_utc"], utc=True))
            cutoff_value = cutoff_by_layer.get(layer)
            cutoff = daily_close_timestamp(cutoff_value) if layer == "daily" else pd.Timestamp(cutoff_value)
            if cutoff.tzinfo is None:
                raise GateBlocked("HOLDOUT_CUTOFF_MUST_BE_TIMEZONE_AWARE")
            cutoff = cutoff.tz_convert("UTC")
            y_all = pd.to_numeric(aligned["label_direction"], errors="coerce").to_numpy(float)
            base_eligible = np.isfinite(y_all) & target_end.notna().to_numpy()
            development = base_eligible & (decision_time.asi8 < cutoff.value) & (target_end.asi8 < cutoff.value)
            eligible_n = int(development.sum())
            spot_ok = pd.to_numeric(aligned["spot_exact_bar_missing"], errors="coerce").fillna(1).to_numpy(int) == 0
            greek_ok = pd.to_numeric(aligned["greek_exact_snapshot_missing"], errors="coerce").fillna(1).to_numpy(int) == 0
            joined = development & spot_ok & greek_ok
            match_n = int(joined.sum())
            match_rate = float(match_n / eligible_n) if eligible_n else 0.0
            old_blocks = pd.to_numeric(aligned["block_index"], errors="coerce").to_numpy(int)
            reasons = []
            if match_rate < 0.60:
                reasons.append("EXACT_FEATURE_JOIN_BELOW_60_PERCENT")
            if match_n < 1:
                reasons.append("NO_EXACT_PAIRED_FEATURE_ROWS")
            if eligible_n < 1:
                reasons.append("NO_DEVELOPMENT_ROWS_AFTER_HOLDOUT_EXCLUSION")
            if len(np.unique(old_blocks[development])) < 20:
                reasons.append("FEWER_THAN_20_CHRONOLOGICAL_DEVELOPMENT_BLOCKS")
            if reasons:
                cell_records.append({
                    "layer": layer, "horizon": int(horizon), "status": "BLOCKED_DATA",
                    "source_panel_rows": int(len(panel)), "development_labeled_rows": eligible_n,
                    "exact_paired_feature_rows": match_n, "exact_join_rate": match_rate,
                    "chronological_development_blocks": int(len(np.unique(old_blocks[development]))),
                    "reasons": reasons,
                })
                continue
            selected_positions = np.flatnonzero(joined)
            aligned_selected = aligned.iloc[selected_positions].copy().reset_index(drop=True)
            old_selected_blocks = old_blocks[selected_positions]
            ordered_block_ids = sorted(np.unique(old_selected_blocks).tolist())
            block_map = {old: new for new, old in enumerate(ordered_block_ids)}
            new_blocks = np.asarray([block_map[int(b)] for b in old_selected_blocks], dtype=int)
            if np.any(np.diff(new_blocks) < 0):
                raise GateBlocked(f"BLOCK_ID_TIME_ORDER_FAILURE:{key}")
            x0 = _numeric_features_for_frame(aligned_selected, SPOT_FEATURE_COLUMNS)
            x0.index = pd.RangeIndex(len(x0))
            greek_numeric = [c for c in GREEK_FEATURE_COLUMNS + [
                "greek_exact_snapshot_missing", "n_option_rows_exact_snapshot"
            ] if c in aligned_selected.columns]
            greek_numeric.extend(sorted(c for c in aligned_selected.columns
                                        if c.startswith(("greek_status_fraction_", "iv_source_fraction_", "expiry_source_fraction_"))
                                        and c not in greek_numeric))
            x1 = pd.concat([x0.reset_index(drop=True),
                            _numeric_features_for_frame(aligned_selected, greek_numeric)], axis=1)
            x1.index = pd.RangeIndex(len(x1))
            if x1.columns.duplicated().any():
                raise GateBlocked("AUGMENTED_FEATURE_COLUMNS_DUPLICATED")
            y = pd.to_numeric(aligned_selected["label_direction"], errors="raise").to_numpy(float)
            ends = pd.to_datetime(aligned_selected["target_end_timestamp_utc"], utc=True)
            dts = pd.to_datetime(aligned_selected["decision_timestamp_utc"], utc=True)
            prediction = _walk_forward_predict_core(
                y, ends, dts, new_blocks, x0, x1, layer, minimum_training_rows=1000
            )
            cell_successes = []
            for model_name, model_result in prediction.items():
                p0, p1 = model_result["p_spot"], model_result["p_augmented"]
                paired = np.isfinite(p0) & np.isfinite(p1) & np.isfinite(y)
                n_oos = int(paired.sum())
                n_test_blocks = int(len(np.unique(new_blocks[paired]))) if paired.any() else 0
                record = {
                    "layer": layer, "horizon": int(horizon), "model": model_name,
                    "status": "PASS" if n_oos >= 500 and n_test_blocks >= 20 and model_result["fit_blocks"] >= 20 else "BLOCKED_DATA",
                    "source_panel_rows": int(len(panel)), "development_labeled_rows": eligible_n,
                    "exact_paired_feature_rows": match_n, "exact_join_rate": match_rate,
                    "paired_oos_rows": n_oos, "paired_oos_blocks": n_test_blocks,
                    "fit_blocks": int(model_result["fit_blocks"]),
                    "blocked_blocks": model_result["blocked_blocks"],
                }
                if record["status"] == "PASS":
                    metrics = paired_metrics(y[paired], p0[paired], p1[paired])
                    original_positions = aligned_selected.loc[paired, "source_row_index"].astype(int).to_numpy()
                    boot = paired_brier_bootstrap(
                        y[paired], p0[paired], p1[paired], 20 if layer == "daily" else 60,
                        reps=BOOTSTRAP_REPS, seed=SEED, population_n=len(panel),
                        row_positions=original_positions,
                    )
                    record["metrics"] = metrics
                    record["inference"] = boot
                    cell_successes.append(record)
                cell_records.append(record)
            if len(cell_successes) != 2:
                # Holm correction is over all 20 predeclared comparisons: a failed cell blocks the family inference.
                pass

    expected_cells = 20
    if len(cell_records) != expected_cells:
        raise GateBlocked(f"INCOMPLETE_MODEL_HORIZON_GRID:{len(cell_records)}")
    all_pass = all(cell.get("status") == "PASS" for cell in cell_records)
    if all_pass:
        raw_p = [float(cell["inference"]["raw_p_value"]) for cell in cell_records]
        adjusted = holm_adjust(raw_p)
        for cell, p_adj in zip(cell_records, adjusted):
            cell["inference"]["holm_adjusted_p_value"] = float(p_adj)
        inference_status = "COMPLETE_20_TEST_HOLM"
    else:
        inference_status = "BLOCKED_INCOMPLETE_20_TEST_FAMILY"
        for cell in cell_records:
            if "inference" in cell:
                cell["inference"]["holm_adjusted_p_value"] = None
    report = {
        "schema_version": 1,
        "study": "PHASE8P_GREEK_INCREMENTAL_PREDICTION",
        "status": "PASS_METRICS_READY_FOR_INDEPENDENT_TESTER_REVIEW" if all_pass else "BLOCKED_DATA_OR_INFERENCE",
        "scope": "prediction_only",
        "input_artifacts": preflight.get("input_artifacts"),
        "developer_commit": authorization.get("developer_commit"),
        "authorization_bundle_sha256": authorization.get("authorization_bundle_sha256"),
        "preflight_report_sha256": authorization.get("preflight_report_sha256"),
        "panel_file_sha256": dict(panel_file_sha256),
        "model_family": ["L2_LOGISTIC_LIBLINEAR_C1", "HIST_GRADIENT_BOOSTING_FIXED"],
        "primary_metric": "mean_Brier_spot_only_minus_Brier_spot_plus_Greek",
        "multiple_testing": {"method": "Holm_step_down", "family_size": 20, "status": inference_status},
        "cells": cell_records,
        "empirical_option_pnl_run": False,
        "holdout_accessed": False,
        "strategy_promotion": False,
        "commercial_use": False,
    }
    return report


def run_prediction_study(
    panels: Mapping[str, pd.DataFrame],
    option_parts: Iterable[pd.DataFrame],
    *,
    spot_rows: pd.DataFrame | None = None,
    panel_file_sha256: Mapping[str, str],
    authorization_bundle_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Full fixed 20-comparison prediction runner; production authorization is mandatory."""
    authorization = enforce_fit_gate(authorization_bundle_path)
    unique_decisions = []
    daily_dates = []
    intraday_times = []
    for key, panel in panels.items():
        layer = str(panel["layer"].iloc[0])
        times = canonical_panel_timestamps(panel, layer)
        unique_decisions.extend(times.tolist())
        if layer == "daily":
            daily_dates.extend(panel["decision_timestamp"].tolist())
        else:
            intraday_times.extend(times.tolist())
    unique_decisions = pd.DatetimeIndex(unique_decisions).drop_duplicates().sort_values()
    spot_sink: list[pd.DataFrame] = []
    greek_features = build_option_feature_frame(option_parts, unique_decisions, spot_sink if spot_rows is None else None)
    if spot_rows is None:
        if not spot_sink:
            raise GateBlocked("ENCRYPTED_COMPOSITE_CONTAINED_NO_SPOT_ROWS")
        spot_rows = pd.concat(spot_sink, ignore_index=True)
    daily_features = build_daily_spot_features(spot_rows, sorted(set(pd.Timestamp(x).normalize() for x in daily_dates))) if daily_dates else pd.DataFrame()
    intraday_features = build_spot_features(spot_rows, pd.DatetimeIndex(intraday_times).drop_duplicates().sort_values()) if intraday_times else pd.DataFrame()
    spot_features = _flatten_spot_frames(daily_features, intraday_features)
    report = _run_prediction_study_authorized(
        panels, spot_rows, greek_features, spot_features, panel_file_sha256,
        authorization, output_path,
    )
    receipt = write_aggregate_only_report(report, output_path)
    report["aggregate_report_receipt"] = receipt
    return report


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_bytes(ref: str, path: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(_repo_root()), "show", f"{ref}:{path}"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise GateBlocked(f"FROZEN_SOURCE_FILE_UNAVAILABLE:{ref}:{path}") from exc


def _verify_frozen_label_sources(manifest: Mapping[str, Any]) -> dict[str, Any]:
    proof = {}
    code_files = manifest.get("code_files", {})
    for layer, path in (
        ("daily", "scripts/run_phase3_daily_baselines.py"),
        ("intraday", "scripts/run_phase3_intraday_baselines.py"),
    ):
        actual_blob = _git_blob_sha1(FROZEN_PHASE7_COMMIT, path)
        if actual_blob != FROZEN_LABEL_SOURCE_BLOBS[layer]:
            raise GateBlocked("FROZEN_LABEL_SOURCE_BLOB_MISMATCH:" + layer)
        content = _git_bytes(FROZEN_PHASE7_COMMIT, path)
        actual_sha256 = _sha256_bytes(content)
        manifest_record = code_files.get(path, {})
        expected_sha256 = manifest_record.get("sha256") if isinstance(manifest_record, Mapping) else None
        if not expected_sha256 or actual_sha256 != expected_sha256:
            raise GateBlocked("FROZEN_LABEL_SOURCE_SHA256_NOT_RECONCILED_TO_PANEL_MANIFEST:" + layer)
        text = content.decode("utf-8")
        if layer == "daily" and 'future=np.log(df["close"].shift(-h)/df["close"])' not in text:
            raise GateBlocked("FROZEN_DAILY_LABEL_RULE_CHANGED")
        if layer == "intraday" and (
            "future_target=idx+pd.Timedelta(minutes=h)" not in text
            or "future_pos=indexer.get_indexer(future_target)" not in text
        ):
            raise GateBlocked("FROZEN_INTRADAY_LABEL_RULE_CHANGED")
        proof[layer] = {
            "source_path": path,
            "source_commit": FROZEN_PHASE7_COMMIT,
            "source_blob_sha1": actual_blob,
            "source_sha256": actual_sha256,
        }
    return {
        "daily_label_source_blob_sha1": proof["daily"]["source_blob_sha1"],
        "intraday_label_source_blob_sha1": proof["intraday"]["source_blob_sha1"],
        "daily_rule": "close.shift(-H)",
        "intraday_rule": "exact timestamp + H minutes",
        "source_files": proof,
        "target_end_checks_passed": False,
    }


def verify_code_gate_for_preflight() -> dict[str, Any]:
    """Verify tester approvals for schema-only data inspection without allowing model fit."""
    env = ("PHASE8P_CODE_DECISION_REF", "PHASE8P_CODE_DECISION_PATH", "PHASE8P_CODE_DECISION_BLOB_SHA1")
    if any(not os.environ.get(key) for key in env):
        raise GateBlocked("INDEPENDENT_CODE_GATE_PIN_MISSING")
    ref, path, expected_blob = (os.environ[key] for key in env)
    if _git_blob_sha1(ref, path) != expected_blob:
        raise GateBlocked("INDEPENDENT_CODE_GATE_BLOB_MISMATCH")
    try:
        decision = json.loads(_git_text(ref, path))
    except json.JSONDecodeError as exc:
        raise GateBlocked("INDEPENDENT_CODE_GATE_DECISION_INVALID") from exc
    current = subprocess.check_output(["git", "-C", str(_repo_root()), "rev-parse", "HEAD"], text=True).strip()
    if decision.get("decision") != "PASS_FOR_CODE_ONLY" or decision.get("developer_commit") != current:
        raise GateBlocked("INDEPENDENT_CODE_GATE_NOT_APPROVED_FOR_CURRENT_COMMIT")
    reviewed = decision.get("reviewed_blobs", {})
    for path in (
        "scripts/phase8p_greek_prediction.py",
        "scripts/test_phase8p_greek_prediction.py",
        ".github/workflows/phase8p-greek-prediction.yml",
        "research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md",
    ):
        expected = reviewed.get(path)
        actual = _git_blob_sha1(current, path)
        if not expected or expected != actual:
            raise GateBlocked("INDEPENDENT_CODE_GATE_FILE_MISMATCH:" + path)
    # The approved R3 research scope and daily timestamp amendment are fixed immutable reviews.
    scope_ref = "refs/remotes/origin/phase-08-prediction-tester"
    if _git_blob_sha1(scope_ref, "research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_TESTER_R3_2026-10-12.md") != "798008657afe0757c54c9aa7dc5eeb1fade3faf5":
        raise GateBlocked("SCOPE_REVIEW_BLOB_MISMATCH")
    if _git_blob_sha1(scope_ref, "research/gates/PHASE8P_DAILY_TIMESTAMP_AMENDMENT_TESTER_R2_2026-10-12.md") != "d0f6ad6803c16051bd897f3074682281b3e4c3a0":
        raise GateBlocked("DAILY_TIMESTAMP_AMENDMENT_REVIEW_BLOB_MISMATCH")
    if _git_blob_sha1(scope_ref, "research/gates/PHASE8P_DAILY_TIMESTAMP_AMENDMENT_DECISION_R2_2026-10-12.json") != "c154ab22dbf3fe244c6ff2010b6ea60a30538308":
        raise GateBlocked("DAILY_TIMESTAMP_AMENDMENT_DECISION_BLOB_MISMATCH")
    return {"developer_commit": current, "code_decision": decision, "code_decision_blob_sha1": expected_blob}


def load_frozen_forecast_panels(artifact_zip_path: str | Path, observed_artifact_id: int):
    """Load the exact frozen Run #994 panels only after the caller has passed the proper gate."""
    receipt = verify_pinned_artifact_identity(artifact_zip_path, "forecast", observed_artifact_id)
    with zipfile.ZipFile(artifact_zip_path, "r") as archive:
        names = archive.namelist()
        manifest_names = [name for name in names if name.endswith("phase7_reference_manifest.json")]
        aggregate_names = [name for name in names if name.endswith("phase7_ensemble_results.json")]
        if len(manifest_names) != 1 or len(aggregate_names) != 1:
            raise GateBlocked("FROZEN_FORECAST_MANIFEST_OR_AGGREGATE_MISSING_OR_DUPLICATE")
        manifest_bytes = archive.read(manifest_names[0])
        aggregate_bytes = archive.read(aggregate_names[0])
        manifest_sha = _sha256_bytes(manifest_bytes)
        if manifest_sha != PINNED_ARTIFACTS["forecast"]["manifest_sha256"]:
            raise GateBlocked("FROZEN_FORECAST_MANIFEST_SHA256_MISMATCH")
        if _sha256_bytes(aggregate_bytes) != PINNED_ARTIFACTS["forecast"]["aggregate_sha256"]:
            raise GateBlocked("FROZEN_FORECAST_AGGREGATE_SHA256_MISMATCH")
        try:
            manifest = json.loads(manifest_bytes)
        except json.JSONDecodeError as exc:
            raise GateBlocked("FROZEN_FORECAST_MANIFEST_JSON_INVALID") from exc
        if (manifest.get("status") != "COMPLETE" or manifest.get("schema_version") != 1
                or manifest.get("commit") != FROZEN_PHASE7_COMMIT
                or manifest.get("seed") != SEED
                or manifest.get("protocol") != "research/phase7/PHASE7_METHOD_SPEC.md"):
            raise GateBlocked("FROZEN_FORECAST_MANIFEST_CONTRACT_MISMATCH")
        if len(manifest.get("prediction_panels", [])) != 10:
            raise GateBlocked("FROZEN_FORECAST_PANEL_COUNT_MISMATCH")
        panels: dict[str, pd.DataFrame] = {}
        panel_hashes: dict[str, str] = {}
        records = {(str(row.get("layer")), int(row.get("horizon"))): row
                   for row in manifest["prediction_panels"]}
        expected_grid = {(layer, h) for layer, hs in EXPECTED_HORIZONS.items() for h in hs}
        if set(records) != expected_grid:
            raise GateBlocked("FROZEN_FORECAST_LAYER_HORIZON_GRID_MISMATCH")
        for layer, horizon in sorted(expected_grid):
            base_name = f"phase7_predictions_{layer}_H{horizon}.parquet"
            matches = [name for name in names if name.endswith("/" + base_name) or name == base_name]
            if len(matches) != 1:
                raise GateBlocked("FROZEN_PANEL_FILE_MISSING_OR_DUPLICATE:" + base_name)
            raw = archive.read(matches[0])
            digest = _sha256_bytes(raw)
            record = records[(layer, horizon)]
            if digest != record.get("sha256"):
                raise GateBlocked("FROZEN_PANEL_FILE_SHA256_MISMATCH:" + base_name)
            try:
                frame = pd.read_parquet(io.BytesIO(raw))
            except Exception as exc:
                raise GateBlocked("FROZEN_PANEL_PARQUET_UNREADABLE:" + base_name) from exc
            if len(frame) != int(record.get("rows", -1)) or record.get("columns") != list(frame.columns):
                raise GateBlocked("FROZEN_PANEL_SCHEMA_OR_ROWS_MISMATCH:" + base_name)
            validate_panel_frame(frame, layer, horizon)
            key = _panel_key(layer, horizon)
            panels[key] = frame
            panel_hashes[key] = digest
        manifest["manifest_sha256"] = manifest_sha
        manifest["aggregate_sha256"] = _sha256_bytes(aggregate_bytes)
        return panels, manifest, panel_hashes, receipt


def _derive_key_from_hf_token(token: str) -> bytes:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    if not isinstance(token, str) or len(token.strip()) < 16:
        raise GateBlocked("HF_TOKEN_MISSING_OR_TOO_SHORT_FOR_CACHE_DECRYPTION")
    return Scrypt(
        salt=b"Naked-option-v1-HF-TOKEN-DERIVATION-v1",
        length=32, n=2**14, r=8, p=1,
    ).derive(token.encode())


def iter_encrypted_composite_parts(artifact_zip_path: str | Path) -> Iterable[pd.DataFrame]:
    """Yield authenticated CSV frames directly from the encrypted cached artifact in memory.

    The official entry points call this only after their code/preflight authorization check.
    No decrypted plaintext file or intermediate data artifact is written to disk.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    token = os.environ.get("HF_TOKEN", "")
    key = _derive_key_from_hf_token(token)
    with zipfile.ZipFile(artifact_zip_path, "r") as archive:
        names = archive.namelist()
        manifest_names = [name for name in names if name.endswith("dataset_manifest.json")]
        if len(manifest_names) != 1:
            raise GateBlocked("GREEK_DATASET_MANIFEST_MISSING_OR_DUPLICATE")
        manifest = json.loads(archive.read(manifest_names[0]))
        if manifest.get("source_license") != "CC-BY-NC-4.0: non-commercial research only":
            raise GateBlocked("GREEK_DATASET_LICENSE_RESTRICTION_MISMATCH")
        if manifest.get("download_bundle_contains_encrypted_data_only") is not True:
            raise GateBlocked("GREEK_DATASET_ENCRYPTION_MARKER_MISSING")
        parts = manifest.get("parts", [])
        if len(parts) != 61:
            raise GateBlocked("GREEK_DATASET_PART_COUNT_MISMATCH")
        expected_rows = 0
        for part_number, part in enumerate(parts):
            if not isinstance(part, Mapping) or not isinstance(part.get("row_count"), int):
                raise GateBlocked(f"GREEK_DATASET_PART_ROW_COUNT_INVALID:{part_number}")
            expected_rows += int(part["row_count"])
        if expected_rows != 8_999_865 or manifest.get("rows_preserved") != expected_rows:
            raise GateBlocked("GREEK_DATASET_ROW_TOTAL_MISMATCH")
        total_rows = 0
        for part_number, part in enumerate(parts):
            filename = str(part.get("file", ""))
            matches = [name for name in names if name.endswith("/" + filename) or name == filename]
            if len(matches) != 1:
                raise GateBlocked("GREEK_ENCRYPTED_PART_MISSING_OR_DUPLICATE:" + filename)
            raw = archive.read(matches[0])
            if _sha256_bytes(raw) != part.get("encrypted_sha256"):
                raise GateBlocked("GREEK_ENCRYPTED_PART_SHA256_MISMATCH:" + filename)
            if not raw.startswith(b"N1C1") or len(raw) < 32:
                raise GateBlocked("GREEK_ENCRYPTED_PART_HEADER_INVALID:" + filename)
            try:
                plain_gzip = AESGCM(key).decrypt(raw[4:16], raw[16:], b"Naked-option-v1:NIFTY-1m-composite:v1")
            except Exception as exc:
                raise GateBlocked("GREEK_ENCRYPTED_PART_AUTHENTICATION_FAILED:" + filename) from exc
            if _sha256_bytes(plain_gzip) != part.get("plain_gzip_sha256"):
                raise GateBlocked("GREEK_DECRYPTED_PART_SHA256_MISMATCH:" + filename)
            try:
                frame = pd.read_csv(io.BytesIO(plain_gzip), compression="gzip", low_memory=False)
            except Exception as exc:
                raise GateBlocked("GREEK_DECRYPTED_PART_CSV_INVALID:" + filename) from exc
            if len(frame) != int(part["row_count"]):
                raise GateBlocked("GREEK_DECRYPTED_PART_ROW_COUNT_MISMATCH:" + filename)
            total_rows += len(frame)
            yield frame
        if total_rows != expected_rows:
            raise GateBlocked(f"GREEK_DATASET_TOTAL_ROWS_MISMATCH:{total_rows}:{expected_rows}")


def _derive_holdout_proof_from_frozen_manifest(manifest: Mapping[str, Any]) -> dict[str, Any] | None:
    """Accept only a holdout contract explicitly embedded in the pinned immutable manifest."""
    contract = manifest.get("holdout_exclusion_contract")
    if not isinstance(contract, Mapping):
        return None
    mask_sha = str(contract.get("mask_sha256", ""))
    cutoffs = contract.get("cutoff_by_layer")
    if (contract.get("proof") != "VERIFIED"
            or len(mask_sha) != 64
            or not isinstance(cutoffs, Mapping)
            or set(cutoffs) != {"daily", "intraday"}
            or contract.get("source_artifact_id") != PINNED_ARTIFACTS["forecast"]["artifact_id"]
            or contract.get("source_run_id") != manifest.get("run_id")):
        return None
    return {
        "proof": "VERIFIED",
        "mask_sha256": mask_sha,
        "cutoff_by_layer": dict(cutoffs),
        "source_manifest_sha256": manifest.get("manifest_sha256"),
        "source_manifest_commit": manifest.get("commit"),
        "source_artifact_id": contract.get("source_artifact_id"),
        "source_run_id": contract.get("source_run_id"),
        "proof_method": contract.get("proof_method"),
    }


def _build_features_for_panels(panels: Mapping[str, pd.DataFrame], spot_rows: pd.DataFrame,
                               option_parts: Iterable[pd.DataFrame]):
    all_daily_dates = []
    all_intraday_times = []
    all_decisions = []
    for key, panel in panels.items():
        layer = str(panel["layer"].iloc[0])
        times = canonical_panel_timestamps(panel, layer)
        all_decisions.extend(times.tolist())
        if layer == "daily":
            all_daily_dates.extend(panel["decision_timestamp"].tolist())
        else:
            all_intraday_times.extend(times.tolist())
    all_decisions = pd.DatetimeIndex(all_decisions).drop_duplicates().sort_values()
    greek_features = build_option_feature_frame(option_parts, all_decisions)
    daily_features = build_daily_spot_features(
        spot_rows, sorted(set(pd.Timestamp(x).normalize() for x in all_daily_dates))
    ) if all_daily_dates else pd.DataFrame()
    intraday_features = build_spot_features(
        spot_rows, pd.DatetimeIndex(all_intraday_times).drop_duplicates().sort_values()
    ) if all_intraday_times else pd.DataFrame()
    spot_features = _flatten_spot_frames(daily_features, intraday_features)
    source_epochs = pd.to_numeric(spot_rows["timestamp_epoch"], errors="coerce").to_numpy(float)
    source_epochs = np.where(source_epochs > 1e12, np.floor(source_epochs / 1000.0), source_epochs)
    source_epochs = source_epochs[np.isfinite(source_epochs)]
    source_timestamps = pd.to_datetime(source_epochs, unit="s", utc=True).sort_values()
    aligned = {}
    target_end_by_panel = {}
    coverage = {}
    for key, panel in panels.items():
        layer = str(panel["layer"].iloc[0])
        aligned_panel = align_features_to_prediction_panel(
            panel, spot_features, greek_features, layer,
            source_timestamps=source_timestamps if layer == "intraday" else None,
        )
        aligned[key] = aligned_panel
        target_end_by_panel[key] = aligned_panel["target_end_timestamp_utc"].tolist()
        y = pd.to_numeric(aligned_panel["label_direction"], errors="coerce").to_numpy(float)
        label_mask = np.isfinite(y)
        spot_ok = pd.to_numeric(aligned_panel["spot_exact_bar_missing"], errors="coerce").fillna(1).to_numpy(int) == 0
        greek_ok = pd.to_numeric(aligned_panel["greek_exact_snapshot_missing"], errors="coerce").fillna(1).to_numpy(int) == 0
        eligible_n = int(label_mask.sum())
        exact_n = int((label_mask & spot_ok & greek_ok).sum())
        coverage[key] = {
            "panel_rows": int(len(panel)), "labeled_rows": eligible_n,
            "exact_spot_rows": int((label_mask & spot_ok).sum()),
            "exact_greek_snapshot_rows": int((label_mask & greek_ok).sum()),
            "exact_paired_feature_rows": exact_n,
            "exact_join_rate": float(exact_n / eligible_n) if eligible_n else 0.0,
            "chronological_blocks": int(aligned_panel["block_index"].nunique()),
        }
    return greek_features, spot_features, aligned, target_end_by_panel, coverage


def run_schema_preflight_from_artifacts(
    greek_zip_path: str | Path, observed_greek_artifact_id: int,
    forecast_zip_path: str | Path, observed_forecast_artifact_id: int,
    output_path: str | Path,
) -> dict[str, Any]:
    """Schema-only preflight. It requires the independent code PASS before opening data."""
    code_receipt = verify_code_gate_for_preflight()
    greek_receipt = verify_pinned_artifact_identity(greek_zip_path, "greek", observed_greek_artifact_id)
    panels, manifest, panel_hashes, forecast_receipt = load_frozen_forecast_panels(
        forecast_zip_path, observed_forecast_artifact_id
    )
    # Only this schema/coverage function is allowed to decrypt for data verification before fitting.
    spot_sink: list[pd.DataFrame] = []
    decisions = []
    daily_dates = []
    intraday_times = []
    for panel in panels.values():
        layer = str(panel["layer"].iloc[0])
        times = canonical_panel_timestamps(panel, layer)
        decisions.extend(times.tolist())
        if layer == "daily":
            daily_dates.extend(panel["decision_timestamp"].tolist())
        else:
            intraday_times.extend(times.tolist())
    unique_decisions = pd.DatetimeIndex(decisions).drop_duplicates().sort_values()
    # Build exact Greek snapshots and capture SPOT rows in the same streaming pass.
    greek_features = build_option_feature_frame(iter_encrypted_composite_parts(greek_zip_path), unique_decisions, spot_sink)
    if not spot_sink:
        raise GateBlocked("SCHEMA_PREFLIGHT_FOUND_NO_SPOT_ROWS")
    spot_rows = pd.concat(spot_sink, ignore_index=True)
    daily_features = build_daily_spot_features(
        spot_rows, sorted(set(pd.Timestamp(x).normalize() for x in daily_dates))
    )
    intraday_features = build_spot_features(
        spot_rows, pd.DatetimeIndex(intraday_times).drop_duplicates().sort_values()
    )
    spot_features = _flatten_spot_frames(daily_features, intraday_features)
    source_epochs = pd.to_numeric(spot_rows["timestamp_epoch"], errors="coerce").to_numpy(float)
    source_epochs = np.where(source_epochs > 1e12, np.floor(source_epochs / 1000.0), source_epochs)
    source_epochs = source_epochs[np.isfinite(source_epochs)]
    source_timestamps = pd.to_datetime(source_epochs, unit="s", utc=True).sort_values()
    aligned = {}
    target_end = {}
    coverage = {}
    for key, panel in panels.items():
        layer = str(panel["layer"].iloc[0])
        a = align_features_to_prediction_panel(
            panel, spot_features, greek_features, layer,
            source_timestamps=source_timestamps if layer == "intraday" else None,
        )
        aligned[key] = a
        target_end[key] = a["target_end_timestamp_utc"].tolist()
        y = pd.to_numeric(a["label_direction"], errors="coerce").to_numpy(float)
        finite = np.isfinite(y)
        spot_ok = pd.to_numeric(a["spot_exact_bar_missing"], errors="coerce").fillna(1).to_numpy(int) == 0
        greek_ok = pd.to_numeric(a["greek_exact_snapshot_missing"], errors="coerce").fillna(1).to_numpy(int) == 0
        n_labels = int(finite.sum())
        n_join = int((finite & spot_ok & greek_ok).sum())
        coverage[key] = {
            "panel_rows": int(len(a)), "finite_label_rows": n_labels,
            "exact_spot_rows": int((finite & spot_ok).sum()),
            "exact_greek_snapshot_rows": int((finite & greek_ok).sum()),
            "exact_paired_feature_rows": n_join,
            "exact_join_rate": float(n_join / n_labels) if n_labels else 0.0,
            "chronological_blocks": int(a["block_index"].nunique()),
        }
    target_proof = _verify_frozen_label_sources(manifest)
    all_target_checks = True
    for key, a in aligned.items():
        y = pd.to_numeric(a["label_direction"], errors="coerce").to_numpy(float)
        ends = pd.DatetimeIndex(pd.to_datetime(a["target_end_timestamp_utc"], errors="coerce", utc=True))
        decisions = pd.DatetimeIndex(pd.to_datetime(a["decision_timestamp_utc"], errors="coerce", utc=True))
        future = pd.to_numeric(a["future_return"], errors="coerce").to_numpy(float)
        finite = np.isfinite(y)
        if np.any(finite & ends.isna()) or np.any(finite & (ends.asi8 <= decisions.asi8)):
            all_target_checks = False
        valid = finite & np.isfinite(future) & (future != 0)
        if not np.array_equal(y[valid].astype(int), (future[valid] > 0).astype(int)):
            all_target_checks = False
    target_proof["target_end_checks_passed"] = bool(all_target_checks)
    holdout_proof = _derive_holdout_proof_from_frozen_manifest(manifest)
    receipts = {"greek": greek_receipt, "forecast": forecast_receipt}
    decision = preflight_contract(
        manifest, list(panels.values()),
        artifact_receipts=receipts,
        target_maturity_proof=target_proof,
        holdout_exclusion_proof=holdout_proof,
        target_end_by_panel=target_end,
        panel_file_sha256=panel_hashes,
    )
    # Coverage and sample-size gates are deterministic data gates, not model results.
    for key, item in coverage.items():
        if item["exact_join_rate"] < 0.60:
            decision["reasons"].append(f"EXACT_FEATURE_JOIN_BELOW_60_PERCENT:{key}")
        if item["chronological_blocks"] < 20:
            decision["reasons"].append(f"FEWER_THAN_20_CHRONOLOGICAL_BLOCKS:{key}")
    decision["coverage_by_panel"] = coverage
    decision["spot_feature_frame_rows"] = int(len(spot_features))
    decision["greek_feature_frame_rows"] = int(len(greek_features))
    decision["feature_grid_is_partial"] = True
    decision["greek_source_revision"] = GREEK_SOURCE_PIN["revision"]
    decision["greek_source_license"] = GREEK_SOURCE_PIN["license"]
    decision["code_gate_developer_commit"] = code_receipt["developer_commit"]
    decision["model_fit_authorized"] = False
    decision["holdout_access_authorized"] = False
    decision["option_pnl_authorized"] = False
    decision["strategy_promotion_authorized"] = False
    decision["reasons"] = sorted(set(decision["reasons"]))
    if decision["reasons"]:
        decision["status"] = "BLOCKED"
    receipt = write_aggregate_only_report(decision, output_path)
    decision["preflight_report_receipt"] = receipt
    return decision


def run_prediction_study_from_artifacts(
    greek_zip_path: str | Path, observed_greek_artifact_id: int,
    forecast_zip_path: str | Path, observed_forecast_artifact_id: int,
    authorization_bundle_path: str | Path, output_path: str | Path,
) -> dict[str, Any]:
    """Full production path. Authorization is verified before opening either input ZIP."""
    authorization = enforce_fit_gate(authorization_bundle_path)
    greek_receipt = verify_pinned_artifact_identity(greek_zip_path, "greek", observed_greek_artifact_id)
    panels, manifest, panel_hashes, forecast_receipt = load_frozen_forecast_panels(
        forecast_zip_path, observed_forecast_artifact_id
    )
    for name, receipt in (("greek", greek_receipt), ("forecast", forecast_receipt)):
        approved = authorization["preflight"].get("input_artifacts", {}).get(name, {})
        if receipt["artifact_id"] != approved.get("artifact_id") or receipt["sha256"] != approved.get("sha256"):
            raise GateBlocked("RUN_ARTIFACT_DIFFERS_FROM_TESTER_APPROVED_PREFLIGHT:" + name)
    if dict(panel_hashes) != dict(authorization["preflight"].get("panel_file_sha256", {})):
        raise GateBlocked("RUN_PANEL_HASHES_DIFFER_FROM_TESTER_APPROVED_PREFLIGHT")
    return run_prediction_study(
        panels, iter_encrypted_composite_parts(greek_zip_path),
        panel_file_sha256=panel_hashes, authorization_bundle_path=authorization_bundle_path,
        output_path=output_path,
    )


def synthetic_self_test() -> dict[str, Any]:
    rows=[]
    for i in range(5):
        rows.append({"row_type":"OPTION","option_type":"CE","greek_status":"GREEKS_ESTIMATED_FROM_INVERTED_IV",
            "delta":.6+i*.01,"gamma":.02,"theta_per_day":-1.,"vega_per_1pct_iv":.4,
            "greek_implied_volatility":.20,"open_interest":100,"volume":10,
            "greek_iv_source":"IV_INVERTED_FROM_OPTION_CLOSE","expiry_mapping_source":"HF_EXPIRY_PARTITION_FILELIST_PROXY"})
        rows.append({"row_type":"OPTION","option_type":"PE","greek_status":"GREEKS_ESTIMATED_FROM_INVERTED_IV",
            "delta":-.4-i*.01,"gamma":.025,"theta_per_day":-.8,"vega_per_1pct_iv":.45,
            "greek_implied_volatility":.25,"open_interest":200,"volume":20,
            "greek_iv_source":"IV_INVERTED_FROM_OPTION_CLOSE","expiry_mapping_source":"HF_EXPIRY_PARTITION_FILELIST_PROXY"})
    rows += [{"row_type":"OPTION","option_type":"CE","greek_status":"IV_INPUT_INVALID","delta":.9,
              "open_interest":1e9,"volume":1e9},
             {"row_type":"OPTION","option_type":"PE","greek_status":"GREEKS_ESTIMATED_FROM_INVERTED_IV","delta":-.9,
              "open_interest":200,"volume":20,"data_quality_flags":"SOURCE_FLAGGED_NON_TRADING_SESSION"}]
    a=aggregate_option_snapshot(rows)
    assert abs(a["call_delta_median"]-.62)<1e-12 and abs(a["put_delta_median"]+.42)<1e-12
    assert abs(a["delta_imbalance"]-.20)<1e-12 and abs(a["iv_skew_put_minus_call"]-.05)<1e-12
    assert abs(a["oi_put_call_ratio"]-2)<1e-12 and abs(a["volume_put_call_ratio"]-2)<1e-12
    assert math.isnan(aggregate_option_snapshot(rows[:8])["call_delta_median"])
    zeros=[dict(r,open_interest=0,volume=0) for r in rows[:10]]
    assert aggregate_option_snapshot(zeros)["oi_put_call_ratio_status"]=="NONPOSITIVE_CALL_DENOMINATOR"
    frame=pd.DataFrame({"layer":["intraday"]*4,"horizon":[5]*4,"source_row_index":range(4),
       "decision_timestamp":pd.date_range("2025-01-01T04:00:00Z",periods=4,freq="h"),
       "label_direction":[0,1,0,1],"future_return":[-.01,.02,-.03,.04],"block_index":[0,0,1,1],
       **{f"P{i:02d}":[.4,.6,.45,.55] for i in range(1,11)}})
    assert validate_panel_frame(frame,"intraday",5)["rows"]==4
    d=preflight_contract({"status":"COMPLETE","schema_version":1,"run_id":994,"commit":"abc"},[frame])
    assert d["status"]=="BLOCKED" and not d["model_fit_authorized"]
    assert "PROTECTED_HOLDOUT_EXCLUSION_NOT_PROVEN_BY_FROZEN_MANIFEST" in d["reasons"]
    assert "TARGET_END_AND_LABEL_MATURITY_RULE_NOT_PROVEN_BY_FROZEN_MANIFEST" in d["reasons"]
    for bad, reason in ((frame.drop(columns=["future_return"]),"PANEL_SCHEMA_MISSING"),
                        (frame.assign(source_row_index=[0,1,1,3]),"SOURCE_ROW_INDEX_NOT_ZERO_BASED_SEQUENCE"),
                        (frame.assign(label_direction=[0,2,0,1]),"LABEL_NOT_BINARY_0_1"),
                        (frame.assign(block_index=[0,2,2,2]),"BLOCK_INDEX_NOT_CONTIGUOUS_FROM_ZERO")):
        try: validate_panel_frame(bad,"intraday",5)
        except GateBlocked as e: assert reason in str(e), str(e)
        else: raise AssertionError("invalid panel accepted: "+reason)
    y=np.asarray([0,1]*60,dtype=float); p0=np.where(y==1,.55,.45); p1=np.where(y==1,.70,.30)
    assert paired_brier_bootstrap(y,p0,p1,20,reps=99)["mean_brier_improvement"]>0
    m=paired_metrics(y,p0,p1)
    assert m["mean_brier_improvement"]>0 and m["brier_spot_plus_greek"]<m["brier_spot_only"]
    assert abs(holm_adjust([.01,.04,.03,.002])[3]-.008)<1e-12
    try: enforce_fit_gate(True,True,{"status":"BLOCKED","model_fit_authorized":False,
        "holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False})
    except GateBlocked: pass
    else: raise AssertionError("blocked preflight accepted")
    return {"status":"PASS","mode":"SYNTHETIC_ONLY","feature_math":"PASS","panel_fail_closed":"PASS",
            "bootstrap_holm":"PASS","real_artifacts_opened":False,"model_fitted":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--validate-decision",type=Path,help="Check that a schema decision does not authorize fitting")
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps(synthetic_self_test(),sort_keys=True)); return
    if args.validate_decision:
        d=json.loads(args.validate_decision.read_text())
        if d.get("model_fit_authorized") is not False:
            raise GateBlocked("SCHEMA_PREFLIGHT_CANNOT_AUTHORIZE_MODEL_FITTING")
        print(json.dumps({"status":d.get("status"),"model_fit_authorized":False,"reasons":d.get("reasons",[])},sort_keys=True)); return
    ap.error("use --self-test or --validate-decision; production data access is workflow-gated")

if __name__=="__main__": main()
