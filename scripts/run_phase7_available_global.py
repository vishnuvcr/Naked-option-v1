from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, log_loss, roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
DAILY_PATH = ROOT / "data" / "cache" / "raw" / "phase3" / "nifty50_daily.csv"
GLOBAL_DIR = ROOT / "data" / "cache" / "raw" / "global_history"
MANIFEST_PATH = ROOT / "data" / "reports" / "available_global_source_manifest.json"
REPORT_DIR = ROOT / "data" / "reports"
OUTPUT_PATH = REPORT_DIR / "available_global_prediction_results.json"
PANEL_PATH = REPORT_DIR / "available_global_prediction_panels.csv"
HORIZONS = (1, 2, 3, 5, 10)
MIN_TRAIN = 252
TEST_BLOCK = 20
BOOTSTRAP_REPS = 500
BOOTSTRAP_BLOCK = 20
SEED = 42
EPS = 1e-12


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_nifty_daily(path: Path = DAILY_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"NIFTY daily file not found: {path}")
    df = pd.read_csv(path)
    required = {"date", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"NIFTY file lacks required columns: {sorted(required - set(df.columns))}")
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.normalize()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if len(df) < 1000 or (df["close"] <= 0).any():
        raise ValueError(f"NIFTY history quality gate failed: rows={len(df)}")
    if not df["date"].is_monotonic_increasing:
        raise ValueError("NIFTY dates are not monotonic after normalization")
    return df


def strict_asof_features(target_dates: pd.Series, source: pd.DataFrame) -> pd.DataFrame:
    """Join only source sessions strictly earlier than each NIFTY session date."""
    left = pd.DataFrame({"date": pd.to_datetime(target_dates).dt.normalize()}).sort_values("date")
    right = source.copy()
    right["date"] = pd.to_datetime(right["date"]).dt.normalize()
    right = right.sort_values("date").drop_duplicates("date", keep="last")
    if right["date"].duplicated().any():
        raise ValueError("duplicate source dates after normalization")
    # allow_exact_matches=False is the critical point-in-time guard.
    joined = pd.merge_asof(left, right, on="date", direction="backward", allow_exact_matches=False)
    return joined.drop(columns=["date"])


def source_features(series_id: str, frame: pd.DataFrame) -> pd.DataFrame:
    f = frame[["date", "close"]].copy()
    f["date"] = pd.to_datetime(f["date"]).dt.normalize()
    f["close"] = pd.to_numeric(f["close"], errors="coerce")
    f = f.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last")
    f = f.loc[f["close"] > 0].copy()
    lr = np.log(f["close"]).diff()
    f[f"{series_id}_ret1"] = lr
    f[f"{series_id}_ret5"] = np.log(f["close"] / f["close"].shift(5))
    f[f"{series_id}_vol20"] = lr.rolling(20, min_periods=20).std(ddof=1)
    vol = lr.rolling(20, min_periods=20).std(ddof=1)
    f[f"{series_id}_ret1_z20"] = lr / vol.replace(0, np.nan)
    f[f"{series_id}_ret5_z20"] = f[f"{series_id}_ret5"] / (vol * np.sqrt(5)).replace(0, np.nan)
    f[f"{series_id}_loglevel"] = np.log(f["close"])
    return f[["date", *[c for c in f.columns if c.startswith(series_id + "_")]]].reset_index(drop=True)


def build_feature_frame(nifty: pd.DataFrame, manifest: dict) -> tuple[dict[str, pd.DataFrame], dict]:
    active_records = {r["id"]: r for r in manifest.get("series", []) if r.get("status") == "ACTIVE"}
    feature_by_source: dict[str, pd.DataFrame] = {}
    # Preserve acquisition failure reasons in the final per-source report rather
    # than downgrading every absent source to a generic "unavailable" label.
    source_state = {
        r["id"]: {
            "status": "BLOCKED_DATA",
            "reason": r.get("reason", f"acquisition status was {r.get('status', 'missing')}"),
        }
        for r in manifest.get("series", [])
        if r.get("status") != "ACTIVE"
    }
    for series_id, record in active_records.items():
        path = ROOT / record["path"]
        if not path.exists():
            source_state[series_id] = {"status": "BLOCKED_DATA", "reason": "manifest path missing"}
            continue
        actual_hash = sha256_file(path)
        if actual_hash != record.get("sha256"):
            raise ValueError(f"source SHA-256 mismatch for {series_id}: manifest={record.get('sha256')} actual={actual_hash}")
        frame = pd.read_csv(path, parse_dates=["date"])
        if len(frame) < 500:
            source_state[series_id] = {"status": "BLOCKED_DATA", "reason": "fewer than 500 source observations"}
            continue
        feature_by_source[series_id] = strict_asof_features(nifty["date"], source_features(series_id, frame))
        source_state[series_id] = {
            "status": "ACTIVE", "rows": int(len(frame)), "sha256": actual_hash,
            "min_date": str(pd.to_datetime(frame["date"]).min().date()),
            "max_date": str(pd.to_datetime(frame["date"]).max().date()),
        }
    return feature_by_source, source_state


def get_source_feature(source_map: dict[str, pd.DataFrame], source_id: str, suffix: str) -> pd.Series | None:
    key = f"{source_id}_{suffix}"
    frame = source_map.get(source_id)
    if frame is None or key not in frame:
        return None
    return frame[key]


def build_candidates(nifty: pd.DataFrame, source_map: dict[str, pd.DataFrame], source_state: dict) -> tuple[dict[str, pd.DataFrame], dict]:
    candidates: dict[str, pd.DataFrame] = {}
    status: dict[str, dict] = {}

    single_series = {
        "G01_SENSEX": "SENSEX",
        "G02_BANKNIFTY": "BANKNIFTY",
        "G04_SP500": "SP500",
        "G05_NASDAQ": "NASDAQ",
        "G08_VIX": "VIX",
        "G09_USDINR": "USDINR",
        "G11_GOLD": "GOLD",
        "G12_CRUDE": "CRUDE",
        "G16_INDIAVIX": "INDIAVIX",
    }
    for method, series_id in single_series.items():
        if series_id not in source_map:
            status[method] = {"status": "BLOCKED_DATA", "reason": source_state.get(series_id, {}).get("reason", "source unavailable")}
            continue
        frame = source_map[series_id].copy()
        needed = [f"{series_id}_ret1", f"{series_id}_ret5", f"{series_id}_vol20"]
        if not set(needed).issubset(frame.columns):
            status[method] = {"status": "BLOCKED_DATA", "reason": "required source features absent"}
            continue
        candidates[method] = frame[needed].copy()
        status[method] = {"status": "REGISTERED", "source_ids": [series_id], "features": needed}

    asia_ids = [s for s in ("NIKKEI", "HANGSENG") if s in source_map]
    if len(asia_ids) == 2:
        candidates["G06_ASIA_COMPOSITE"] = pd.DataFrame({
            "NIKKEI_ret1_z20": source_map["NIKKEI"]["NIKKEI_ret1_z20"],
            "HANGSENG_ret1_z20": source_map["HANGSENG"]["HANGSENG_ret1_z20"],
            "NIKKEI_ret5_z20": source_map["NIKKEI"]["NIKKEI_ret5_z20"],
            "HANGSENG_ret5_z20": source_map["HANGSENG"]["HANGSENG_ret5_z20"],
        })
        status["G06_ASIA_COMPOSITE"] = {"status": "REGISTERED", "source_ids": asia_ids}
    else:
        status["G06_ASIA_COMPOSITE"] = {"status": "BLOCKED_DATA", "reason": "both Nikkei and Hang Seng source histories are required"}

    equity_ids = [s for s in ("SP500", "NASDAQ", "NIKKEI", "HANGSENG") if s in source_map]
    if len(equity_ids) >= 2:
        comp = pd.DataFrame(index=source_map[equity_ids[0]].index)
        ret1_columns = []
        ret5_columns = []
        for sid in equity_ids:
            ret1_col = f"{sid}_ret1"
            ret5_col = f"{sid}_ret5"
            comp[ret1_col] = source_map[sid][ret1_col]
            comp[ret5_col] = source_map[sid][ret5_col]
            ret1_columns.append(ret1_col)
            ret5_columns.append(ret5_col)
        # skipna=False preserves the frozen constituent set; a missing constituent
        # makes that composite row ineligible rather than changing the weights.
        comp["GLOBAL_EQUITY_MEAN_RET1"] = comp[ret1_columns].mean(axis=1, skipna=False)
        comp["GLOBAL_EQUITY_MEAN_RET5"] = comp[ret5_columns].mean(axis=1, skipna=False)
        candidates["G13_GLOBAL_EQUITY_COMPOSITE"] = comp[["GLOBAL_EQUITY_MEAN_RET1", "GLOBAL_EQUITY_MEAN_RET5"]]
        status["G13_GLOBAL_EQUITY_COMPOSITE"] = {
            "status": "REGISTERED", "source_ids": equity_ids,
            "definition": "equal-weight mean of raw causal 1-session and 5-session log returns; frozen constituents; row abstained if any constituent is missing",
        }
    else:
        status["G13_GLOBAL_EQUITY_COMPOSITE"] = {"status": "BLOCKED_DATA", "reason": "fewer than two validated global-equity histories"}

    # Limited calendar control: weekdays and annual cycle; not a complete expiry study.
    dates = pd.to_datetime(nifty["date"])
    cal = pd.DataFrame(index=nifty.index)
    dow = dates.dt.dayofweek
    for d in range(1, 5):
        cal[f"weekday_{d}"] = (dow == d).astype(float)
    day_of_year = dates.dt.dayofyear.to_numpy(dtype=float)
    cal["annual_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    cal["annual_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    candidates["G18_CALENDAR_CONTROL"] = cal
    status["G18_CALENDAR_CONTROL"] = {
        "status": "REGISTERED", "source_ids": ["NIFTY date"],
        "definition": "weekday indicators plus fixed annual-cycle sine/cosine; expiry/holiday claims are excluded",
    }
    return candidates, status


def make_label(df: pd.DataFrame, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    future = np.log(df["close"].shift(-horizon).to_numpy(dtype=float) / df["close"].to_numpy(dtype=float))
    y = np.where(future > 0, 1.0, np.where(future < 0, 0.0, np.nan))
    return y, future


def walk_forward_probabilities(y: np.ndarray, X: pd.DataFrame, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Expanding walk-forward, 20-row blocks, training-only scaling, and H-row label purge."""
    x = X.replace([np.inf, -np.inf], np.nan).to_numpy(dtype=float)
    if len(x) != len(y):
        raise ValueError("feature/label length mismatch")
    pred = np.full(len(y), np.nan, dtype=float)
    baseline = np.full(len(y), np.nan, dtype=float)
    for start in range(MIN_TRAIN + horizon, len(y), TEST_BLOCK):
        train_end = max(0, start - horizon)
        label_idx = np.arange(0, train_end)
        label_idx = label_idx[np.isfinite(y[label_idx])]
        if len(label_idx) < MIN_TRAIN or np.unique(y[label_idx]).size < 2:
            continue
        # The causal historical-rate benchmark is independent of source feature
        # completeness; this keeps the benchmark identical across candidates.
        y_benchmark = y[label_idx].astype(int)
        baseline_p = float(y_benchmark.mean())
        if not 0 < baseline_p < 1:
            continue
        block_end = min(start + TEST_BLOCK, len(y))
        for i in range(start, block_end):
            if np.isfinite(y[i]):
                baseline[i] = baseline_p

        train_idx = label_idx[np.isfinite(x[label_idx]).all(axis=1)]
        if len(train_idx) < MIN_TRAIN or np.unique(y[train_idx]).size < 2:
            continue
        y_train = y[train_idx].astype(int)
        mu = x[train_idx].mean(axis=0)
        sd = x[train_idx].std(axis=0)
        sd[~np.isfinite(sd) | (sd < EPS)] = 1.0
        x_train = (x[train_idx] - mu) / sd
        model = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=SEED)
        model.fit(x_train, y_train)
        for i in range(start, block_end):
            if not np.isfinite(y[i]) or not np.isfinite(x[i]).all():
                continue
            x_test = (x[i:i+1] - mu) / sd
            pred[i] = float(model.predict_proba(x_test)[0, 1])
    return pred, baseline


def calc_metrics(y: np.ndarray, p: np.ndarray) -> dict:
    mask = np.isfinite(y) & np.isfinite(p)
    yy = y[mask].astype(int)
    pp = np.clip(p[mask], 1e-6, 1 - 1e-6)
    n = len(yy)
    if n == 0:
        return {"status": "EXECUTED", "n": 0, "reason": "no eligible out-of-sample predictions"}
    pred = (pp >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(yy, pred, labels=[0, 1]).ravel()
    return {
        "status": "EXECUTED", "n": int(n), "positive_rate": float(yy.mean()),
        "accuracy": float(accuracy_score(yy, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(yy, pred)),
        "roc_auc": float(roc_auc_score(yy, pp)) if np.unique(yy).size == 2 else None,
        "pr_auc": float(average_precision_score(yy, pp)) if np.unique(yy).size == 2 else None,
        "brier": float(brier_score_loss(yy, pp)),
        "log_loss": float(log_loss(yy, pp, labels=[0, 1])),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "prediction_mean": float(pp.mean()), "prediction_std": float(pp.std(ddof=0)),
        "classification_threshold": 0.5,
    }


def paired_baseline_comparison(y: np.ndarray, p: np.ndarray, baseline: np.ndarray) -> dict:
    """Compare a candidate and causal baseline on exactly the same eligible rows."""
    mask = np.isfinite(y) & np.isfinite(p) & np.isfinite(baseline)
    n = int(mask.sum())
    if n == 0:
        return {"status": "NOT_APPLICABLE", "reason": "no common candidate/baseline test rows", "n_common": 0}
    yy = y[mask]
    pp = p[mask]
    bb = baseline[mask]
    candidate_metrics = calc_metrics(yy, pp)
    baseline_metrics = calc_metrics(yy, bb)
    return {
        "status": "EXECUTED",
        "n_common": n,
        "candidate_brier": float(candidate_metrics["brier"]),
        "baseline_brier": float(baseline_metrics["brier"]),
        "brier_improvement": float(baseline_metrics["brier"] - candidate_metrics["brier"]),
        "baseline_metrics": baseline_metrics,
    }


def adjust_horizon_pvalues(family_ps: list[tuple[int, float]]) -> list[dict]:
    """Bonferroni adjustment against the full pre-registered horizon family."""
    family_size = len(HORIZONS)
    adjusted = []
    for horizon, raw_p in family_ps:
        p = float(raw_p)
        if not math.isfinite(p) or not 0.0 <= p <= 1.0:
            raise ValueError(f"invalid raw family p-value for horizon {horizon}: {raw_p}")
        adjusted.append({
            "horizon_sessions": int(horizon),
            "raw_p_value": p,
            "bonferroni_p_value": float(min(1.0, p * family_size)),
        })
    return adjusted


def family_bootstrap(y: np.ndarray, baseline: np.ndarray, predictions: dict[str, np.ndarray], reps: int = BOOTSTRAP_REPS) -> dict:
    names = sorted(predictions)
    if len(names) < 1:
        return {"status": "NOT_APPLICABLE", "reason": "no executed methods"}
    common = np.isfinite(y) & np.isfinite(baseline)
    for name in names:
        common &= np.isfinite(predictions[name])
    idx0 = np.flatnonzero(common)
    if len(idx0) < BOOTSTRAP_BLOCK * 5:
        return {"status": "NOT_APPLICABLE", "reason": "fewer than five blocks in common aligned test sample", "n_common": int(len(idx0))}
    yy = y[idx0].astype(int)
    bb = np.clip(baseline[idx0], 1e-6, 1 - 1e-6)
    pp = {n: np.clip(predictions[n][idx0], 1e-6, 1 - 1e-6) for n in names}
    base_loss = (yy - bb) ** 2
    differential = np.column_stack([base_loss - (yy - pp[n]) ** 2 for n in names])
    observed_by_method = differential.mean(axis=0)
    observed = float(observed_by_method.max())
    centered = differential - observed_by_method.reshape(1, -1)
    rng = np.random.default_rng(SEED)
    n = len(yy)
    length = min(BOOTSTRAP_BLOCK, n)
    starts = np.arange(0, n - length + 1)
    blocks_per_rep = int(math.ceil(n / length))
    max_null = np.empty(reps, dtype=float)
    for b in range(reps):
        chosen = rng.choice(starts, size=blocks_per_rep, replace=True)
        take = np.concatenate([np.arange(s, s + length) for s in chosen])[:n]
        max_null[b] = float(centered[take].mean(axis=0).max())
    p_value = float((1 + np.sum(max_null >= observed)) / (reps + 1))
    return {
        "status": "EXECUTED", "n_common": int(n), "method_count": len(names),
        "bootstrap_reps": int(reps), "block_length": int(length), "seed": SEED,
        "max_mean_brier_improvement": observed,
        "candidate_mean_brier_improvements": {name: float(observed_by_method[i]) for i, name in enumerate(names)},
        "family_p_value": p_value,
    }


def run() -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    nifty = load_nifty_daily()
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"global acquisition manifest not found: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    source_map, source_state = build_feature_frame(nifty, manifest)
    candidates, candidate_status = build_candidates(nifty, source_map, source_state)

    all_results = {"daily": {"horizons": {}}, "source_state": source_state, "method_status": candidate_status}
    family_ps = []
    prediction_panels: list[dict] = []
    for h in HORIZONS:
        y, future = make_label(nifty, h)
        horizon_out = {}
        pred_vectors: dict[str, np.ndarray] = {}
        panel_pred_vectors: dict[str, np.ndarray] = {}
        baseline_vector: np.ndarray | None = None
        for method, X in candidates.items():
            p, baseline = walk_forward_probabilities(y, X, h)
            panel_pred_vectors[method] = p.copy()
            if baseline_vector is None:
                baseline_vector = baseline.copy()
            else:
                # Every method should have the same test block/purge schedule; values can differ only due to input missingness.
                baseline_vector = np.where(np.isfinite(baseline), baseline, baseline_vector)
            m = calc_metrics(y, p)
            m["horizon_sessions"] = h
            m["source_ids"] = candidate_status[method].get("source_ids", [])
            m["feature_columns"] = list(X.columns)
            if m.get("status") == "EXECUTED" and m.get("n", 0) > 0:
                paired = paired_baseline_comparison(y, p, baseline)
                if paired.get("status") != "EXECUTED" or paired.get("n_common") != m["n"]:
                    raise ValueError(f"candidate/baseline comparison sample mismatch for {method} horizon={h}")
                m["paired_baseline_comparison"] = paired
            m["mean_future_log_return_when_predicted_up"] = (
                float(future[np.isfinite(p) & (p >= 0.5)].mean())
                if np.any(np.isfinite(p) & (p >= 0.5)) else None
            )
            if m["n"] <= 0:
                # The source may exist but still fail to produce any eligible
                # walk-forward rows (e.g., insufficient point-in-time overlap).
                # Do not publish a fake EXECUTED metric cell.
                m = {
                    "status": "BLOCKED_DATA",
                    "reason": "no eligible out-of-sample predictions after point-in-time and training guards",
                    "horizon_sessions": h,
                    "source_ids": candidate_status[method].get("source_ids", []),
                    "feature_columns": list(X.columns),
                    "n": 0,
                }
            horizon_out[method] = m
            if m["status"] == "EXECUTED" and m["n"] > 0:
                pred_vectors[method] = p
        for method, state in candidate_status.items():
            if state.get("status") == "BLOCKED_DATA":
                horizon_out[method] = {"status": "BLOCKED_DATA", "reason": state.get("reason"), "horizon_sessions": h}
        if baseline_vector is None:
            horizon_out["_BASELINE"] = {"status": "NOT_APPLICABLE", "reason": "no causal historical-rate predictions"}
            horizon_out["_FAMILY_TEST"] = {"status": "NOT_APPLICABLE", "reason": "no executable candidates"}
        else:
            baseline_metrics = calc_metrics(y, baseline_vector)
            if baseline_metrics.get("n", 0) <= 0:
                horizon_out["_BASELINE"] = {"status": "NOT_APPLICABLE", "reason": "no eligible out-of-sample baseline predictions"}
            else:
                baseline_metrics["horizon_sessions"] = h
                baseline_metrics["description"] = "causal historical positive-rate probability, estimated from each purged training prefix"
                baseline_metrics["evaluation_scope"] = "all eligible out-of-sample label rows; compare candidates on paired_baseline_comparison rows, not directly to this broader cell if n differs"
                horizon_out["_BASELINE"] = baseline_metrics
            family = family_bootstrap(y, baseline_vector, pred_vectors)
            horizon_out["_FAMILY_TEST"] = family
            if family.get("status") == "EXECUTED":
                family_ps.append((h, family["family_p_value"]))

        # Preserve one immutable row per eligible date/horizon/method so an
        # independent tester can recompute headline metrics and family inference.
        label_mask = np.isfinite(y)
        if baseline_vector is not None:
            baseline_mask = label_mask & np.isfinite(baseline_vector)
            for i in np.flatnonzero(baseline_mask):
                prediction_panels.append({
                    "date": pd.Timestamp(nifty["date"].iloc[i]).date().isoformat(),
                    "horizon_sessions": int(h),
                    "method": "_BASELINE",
                    "row_type": "baseline",
                    "cell_status": horizon_out["_BASELINE"]["status"],
                    "actual_direction": int(y[i]),
                    "future_log_return": float(future[i]),
                    "predicted_probability": float(baseline_vector[i]),
                    "baseline_probability": float(baseline_vector[i]),
                    "source_ids_json": "[]",
                    "feature_columns_json": "[]",
                })
            for method, p in panel_pred_vectors.items():
                cell = horizon_out[method]
                source_ids = candidate_status[method].get("source_ids", [])
                feature_columns = list(candidates[method].columns)
                for i in np.flatnonzero(baseline_mask):
                    p_available = bool(np.isfinite(p[i]))
                    prediction_panels.append({
                        "date": pd.Timestamp(nifty["date"].iloc[i]).date().isoformat(),
                        "horizon_sessions": int(h),
                        "method": method,
                        "row_type": "candidate",
                        "cell_status": cell.get("status"),
                        "actual_direction": int(y[i]),
                        "future_log_return": float(future[i]),
                        "predicted_probability": float(p[i]) if p_available else np.nan,
                        "baseline_probability": float(baseline_vector[i]),
                        "prediction_available": p_available,
                        "source_ids_json": json.dumps(source_ids, separators=(",", ":")),
                        "feature_columns_json": json.dumps(feature_columns, separators=(",", ":")),
                    })
        all_results["daily"]["horizons"][str(h)] = horizon_out

    # Bonferroni correction across all reported horizon-specific family tests.
    mtests = len(family_ps)
    all_results["family_inference"] = {
        "status": "EXECUTED" if mtests else "NOT_APPLICABLE",
        "family_tests": mtests,
        "family_tests_executed": mtests,
        "registered_family_size": len(HORIZONS),
        "registered_horizons": list(HORIZONS),
        "bonferroni_adjusted_p_values": adjust_horizon_pvalues(family_ps),
        "bootstrap_method": "common-row paired moving-block bootstrap of Brier-loss improvement over a causal training-rate baseline; candidate differentials recentered under the null; max statistic across executed methods",
        "interpretation": "prediction screening only; no candidate promotion from this extension",
    }
    panel_frame = pd.DataFrame(prediction_panels)
    panel_frame.to_csv(PANEL_PATH, index=False)
    all_results["provenance"] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": os.environ.get("GITHUB_SHA", "local_or_unspecified"),
        "nifty_source_path": str(DAILY_PATH.relative_to(ROOT)),
        "nifty_sha256": sha256_file(DAILY_PATH),
        "global_manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "global_manifest_sha256": sha256_file(MANIFEST_PATH),
        "prediction_panel_path": str(PANEL_PATH.relative_to(ROOT)),
        "prediction_panel_sha256": sha256_file(PANEL_PATH),
        "horizons": list(HORIZONS), "min_train": MIN_TRAIN, "test_block": TEST_BLOCK,
        "bootstrap_reps": BOOTSTRAP_REPS, "bootstrap_block": BOOTSTRAP_BLOCK, "seed": SEED,
        "decision_time_rule": "source-local session date strictly less than NIFTY session date",
        "holdout_status": "final untouched holdout not opened",
        "scope": "prediction-only available-data extension; not option trading strategies",
    }
    OUTPUT_PATH.write_text(json.dumps(all_results, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT_PATH.relative_to(ROOT)),
        "active_sources": sum(v.get("status") == "ACTIVE" for v in source_state.values()),
        "executed_methods": sum(s.get("status") == "REGISTERED" for s in candidate_status.values()),
        "family_tests": mtests,
    }, indent=2))
    return all_results


if __name__ == "__main__":
    run()
