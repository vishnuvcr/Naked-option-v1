#!/usr/bin/env python3
"""Prediction-only Greek feature-study utilities. No network or data access."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any, Mapping, Sequence
import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
    brier_score_loss, log_loss, roc_auc_score)
from sklearn.linear_model import LogisticRegression

SEED = 42
BOOTSTRAP_REPS = 500
EXPECTED_HORIZONS = {"daily": (1, 2, 3, 5, 10), "intraday": (5, 15, 30, 60, 120)}
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
    return {"layer": layer, "horizon": int(horizon), "rows": len(frame),
            "finite_label_rows": int(np.isfinite(y).sum()),
            "missing_label_rows": int((~np.isfinite(y)).sum()),
            "block_count": int(len(uniq)),
            "first_decision_timestamp": str(ts.iloc[0]),
            "last_decision_timestamp": str(ts.iloc[-1]),
            "timestamps_unique_ordered": True}

def preflight_contract(manifest: Mapping[str, Any], panels: Sequence[pd.DataFrame]) -> dict[str, Any]:
    """Schema-only decision. Missing holdout/target maturity proof blocks fitting."""
    reasons = []
    if manifest.get("status") != "COMPLETE" or manifest.get("schema_version") != 1:
        reasons.append("FROZEN_PANEL_MANIFEST_STATUS_OR_SCHEMA_UNPROVEN")
    if not manifest.get("commit") or not manifest.get("run_id"):
        reasons.append("FROZEN_PANEL_SOURCE_IDENTITY_MISSING")
    holdout = manifest.get("holdout_exclusion_contract")
    if not isinstance(holdout, dict) or holdout.get("proof") != "VERIFIED" or not holdout.get("protected_row_mask_sha256"):
        reasons.append("PROTECTED_HOLDOUT_EXCLUSION_NOT_PROVEN_BY_FROZEN_MANIFEST")
    target = manifest.get("target_maturity_contract")
    if not isinstance(target, dict) or target.get("proof") != "VERIFIED" or not target.get("source_code_sha256") or not target.get("rule"):
        reasons.append("TARGET_END_AND_LABEL_MATURITY_RULE_NOT_PROVEN_BY_FROZEN_MANIFEST")
    summaries = []
    if len(panels) != 10:
        reasons.append("EXPECTED_EXACTLY_10_FROZEN_PANELS")
    for frame in panels:
        try:
            summaries.append(validate_panel_frame(frame, str(frame["layer"].iloc[0]), int(frame["horizon"].iloc[0])))
        except Exception as exc:
            reasons.append(f"PANEL_VALIDATION_FAILED:{type(exc).__name__}:{exc}")
    found = {(x["layer"], x["horizon"]) for x in summaries}
    required = {(layer, h) for layer, hs in EXPECTED_HORIZONS.items() for h in hs}
    if found != required:
        reasons.append("PANEL_LAYER_HORIZON_GRID_MISMATCH")
    return {"schema_version": 1, "status": "PASS" if not reasons else "BLOCKED",
            "mode": "SCHEMA_COVERAGE_ONLY_NO_MODEL_FIT", "manifest_run_id": manifest.get("run_id"),
            "manifest_commit": manifest.get("commit"), "panel_summaries": summaries,
            "model_fit_authorized": False, "holdout_access_authorized": False,
            "option_pnl_authorized": False, "strategy_promotion_authorized": False, "reasons": reasons}

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

def paired_brier_bootstrap(y, p_spot, p_augmented, block_len: int,
                           reps: int = BOOTSTRAP_REPS, seed: int = SEED) -> dict[str, Any]:
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
    rng = np.random.default_rng(seed)
    boot = np.asarray([float(null_d[moving_block_indices(len(d), block_len, rng)].mean())
                       for _ in range(int(reps))])
    if not np.isfinite(boot).all():
        raise ValueError("non-finite bootstrap statistic blocks inference")
    exceed = int(np.sum(boot >= observed))
    return {"n": len(y), "mean_brier_improvement": observed,
            "null_hypothesis": "H0: E[Brier_spot_only - Brier_spot_plus_greek] <= 0",
            "alternative": "H1: mean paired Brier improvement > 0",
            "block_length": min(block_len, len(y)), "bootstrap_reps": int(reps), "seed": int(seed),
            "null_centered": True, "one_sided": True, "raw_p_value": (1 + exceed) / (reps + 1),
            "bootstrap_exceedances": exceed, "minimum_attainable_p_value": 1 / (reps + 1)}

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
    return out

def enforce_fit_gate(scope_approved: bool, code_approved: bool, preflight: Mapping[str, Any]) -> None:
    if not scope_approved: raise GateBlocked("SCOPE_APPROVAL_MISSING")
    if not code_approved: raise GateBlocked("EXACT_CODE_TESTER_APPROVAL_MISSING")
    if preflight.get("status") != "PASS" or preflight.get("model_fit_authorized") is not True:
        raise GateBlocked("EXACT_PREFLIGHT_TESTER_APPROVAL_MISSING_OR_BLOCKED")
    if preflight.get("holdout_access_authorized") is not False:
        raise GateBlocked("HOLDOUT_MUST_REMAIN_CLOSED")
    if preflight.get("option_pnl_authorized") is not False or preflight.get("strategy_promotion_authorized") is not False:
        raise GateBlocked("OUT_OF_SCOPE_AUTHORIZATION_FLAG")

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
