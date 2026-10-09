from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, log_loss, roc_auc_score,
)

EXPECTED_DAILY = [1, 2, 3, 5, 10]
EXPECTED_INTRADAY = [5, 15, 30, 60, 120]
METHODS = [f"P{i:02d}" for i in range(1, 11)]
METRIC_FIELDS = (
    "n", "positive_rate", "accuracy", "balanced_accuracy", "brier",
    "log_loss", "tn", "fp", "fn", "tp", "roc_auc", "pr_auc",
)
ABSTAIN = {"P05": (0.45, 0.55), "P06": (0.40, 0.60), "P10": (0.45, 0.55)}
TOL = 1e-9


class Audit:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []
        self.notes = []

    def check(self, name, condition, details=""):
        if bool(condition):
            self.passed += 1
        else:
            self.failed += 1
            self.failures.append({"check": name, "details": str(details)})

    def note(self, name, details):
        self.notes.append({"check": name, "details": details})

    def summary(self):
        return {
            "checks_passed": self.passed,
            "checks_failed": self.failed,
            "failures": self.failures,
            "notes": self.notes,
        }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def numeric_match(actual, expected, tol=TOL):
    if expected is None or actual is None:
        return actual is None and expected is None
    if isinstance(expected, (int, float, np.number)) and isinstance(actual, (int, float, np.number)):
        if not np.isfinite(float(expected)) or not np.isfinite(float(actual)):
            return bool(np.isnan(expected) and np.isnan(actual))
        return abs(float(actual) - float(expected)) <= tol
    return actual == expected


def arrays_match(actual, expected, tol=1e-12):
    a = np.asarray(actual, dtype=float)
    b = np.asarray(expected, dtype=float)
    return a.shape == b.shape and np.allclose(a, b, rtol=0.0, atol=tol, equal_nan=True)


def independently_calculate_metrics(y, p, name):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    mask = np.isfinite(y) & np.isfinite(p)
    if name in ABSTAIN:
        lo, hi = ABSTAIN[name]
        mask &= ~((p >= lo) & (p <= hi))
    yy = y[mask].astype(int)
    pp = np.clip(p[mask], 1e-6, 1 - 1e-6)
    if len(yy) == 0:
        return {"status": "EXECUTED", "n": 0}
    pred = (pp >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(yy, pred, labels=[0, 1]).ravel()
    unique = np.unique(yy)
    return {
        "status": "EXECUTED",
        "n": int(len(yy)),
        "positive_rate": float(np.mean(yy)),
        "accuracy": float(accuracy_score(yy, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(yy, pred)),
        "brier": float(brier_score_loss(yy, pp)),
        "log_loss": float(log_loss(yy, pp, labels=[0, 1])),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "roc_auc": float(roc_auc_score(yy, pp)) if len(unique) == 2 else None,
        "pr_auc": float(average_precision_score(yy, pp)) if len(unique) == 2 else None,
    }


def nearly_equal_json(actual, expected, tol=TOL):
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            nearly_equal_json(actual[k], expected[k], tol) for k in actual
        )
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(
            nearly_equal_json(a, b, tol) for a, b in zip(actual, expected)
        )
    if isinstance(actual, (int, float, np.number)) and isinstance(expected, (int, float, np.number)):
        return numeric_match(actual, expected, tol)
    return actual == expected


def independently_calculate_accuracy_bootstrap(y, p, block_len, reps=200, seed=42):
    z = pd.DataFrame({"y": np.asarray(y, float), "p": np.asarray(p, float)}).dropna()
    if len(z) < block_len:
        return {"lower": None, "upper": None, "median": None}
    rng = np.random.default_rng(seed)
    n = len(z)
    blocks = [np.arange(i, min(i + block_len, n)) for i in range(0, n, block_len)]
    yy, pp = z["y"].to_numpy(), z["p"].to_numpy()
    values = []
    for _ in range(reps):
        selected = rng.integers(0, len(blocks), size=len(blocks))
        idx = np.concatenate([blocks[j] for j in selected])[:n]
        values.append(float(np.mean((pp[idx] >= 0.5) == yy[idx])))
    return {
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
        "median": float(np.median(values)),
    }


def independently_calculate_fixed_bins(y, p, future):
    z = pd.DataFrame({
        "y": np.asarray(y, float), "p": np.asarray(p, float), "future": np.asarray(future, float)
    }).replace([np.inf, -np.inf], np.nan).dropna(subset=["y", "p", "future"])
    edges = [0.0, 0.45, 0.50, 0.55, 0.60, 1.0000001]
    names = ["<0.45", "0.45-0.50", "0.50-0.55", "0.55-0.60", ">=0.60"]
    output = {}
    for lo, hi, name in zip(edges[:-1], edges[1:], names):
        mask = (z["p"] >= lo) & (z["p"] < hi)
        output[name] = {
            "n": int(mask.sum()),
            "mean_future_return": float(z.loc[mask, "future"].mean()) if mask.any() else None,
        }
    return output


def independently_calculate_regime_predictions(y, p1, p4, vol, trend, block_index):
    n = len(y)
    p8 = np.full(n, np.nan, dtype=float)
    p9 = np.full(n, np.nan, dtype=float)
    diagnostics = []
    fallback_count = 0
    for block_id in range(int(np.max(block_index)) + 1):
        rows = np.flatnonzero(block_index == block_id)
        if not len(rows):
            continue
        train_rows = np.arange(int(rows[0]))
        train_vol = vol[train_rows][np.isfinite(vol[train_rows])]
        train_trend = trend[train_rows][np.isfinite(trend[train_rows])]
        if len(train_vol) < 200 or len(train_trend) < 200:
            continue
        vol_cut = float(np.median(train_vol))
        trend_cut = float(np.median(train_trend))
        valid_y = np.isfinite(y[train_rows])
        pooled = float(np.mean(y[train_rows][valid_y])) if valid_y.any() else 0.5
        valid_state = valid_y & np.isfinite(vol[train_rows]) & np.isfinite(trend[train_rows])
        state_rates = {}
        train_counts = {}
        for vol_state in (0, 1):
            for trend_state in (0, 1):
                state_mask = (
                    valid_state
                    & ((vol[train_rows] > vol_cut).astype(int) == vol_state)
                    & ((trend[train_rows] > trend_cut).astype(int) == trend_state)
                )
                count = int(state_mask.sum())
                key = f"{vol_state}{trend_state}"
                train_counts[key] = count
                if count >= 50:
                    state_rates[(vol_state, trend_state)] = float(np.mean(y[train_rows][state_mask]))
                else:
                    state_rates[(vol_state, trend_state)] = pooled
                    fallback_count += 1
        test_counts = {f"{v}{t}": 0 for v in (0, 1) for t in (0, 1)}
        eval_mask = (
            np.isfinite(y[rows]) & np.isfinite(p1[rows]) & np.isfinite(p4[rows])
            & np.isfinite(vol[rows]) & np.isfinite(trend[rows])
        )
        for row in rows:
            if np.isfinite(p1[row]) and np.isfinite(p4[row]) and np.isfinite(vol[row]) and np.isfinite(trend[row]):
                state = (int(vol[row] > vol_cut), int(trend[row] > trend_cut))
                rate = state_rates[state]
                p8[row] = 0.5 * p1[row] + 0.5 * rate
                p9[row] = 0.5 * p4[row] + 0.5 * rate
                if np.isfinite(y[row]):
                    test_counts[f"{state[0]}{state[1]}"] += 1
        if eval_mask.any():
            diagnostics.append({
                "train_counts": train_counts,
                "test_counts": test_counts,
                "vol_cut": vol_cut,
                "trend_cut": trend_cut,
            })
    return p8, p9, diagnostics, fallback_count


def block_resample(n, block_len, rng):
    if n <= 0:
        return np.array([], dtype=int)
    length = min(int(block_len), int(n))
    count = int(math.ceil(n / length))
    starts = rng.integers(0, n - length + 1, size=count)
    return np.concatenate(
        [np.arange(start, start + length, dtype=int) for start in starts]
    )[:n]


def independently_calculate_family_test(y, candidates, block_index, block_len):
    y = np.asarray(y, dtype=float)
    n = len(y)
    blocks = [np.flatnonzero(block_index == b) for b in range(int(np.max(block_index)) + 1)]
    baseline = np.full(n, np.nan, dtype=float)
    for rows in blocks:
        if len(rows) == 0:
            continue
        training_y = y[:int(rows[0])]
        training_y = training_y[np.isfinite(training_y)]
        if len(training_y) >= 200:
            baseline[rows] = float(np.mean(training_y))

    differences = np.full((n, len(METHODS)), np.nan, dtype=float)
    for col, name in enumerate(METHODS):
        p = np.asarray(candidates[name], dtype=float)
        finite = np.isfinite(y) & np.isfinite(p) & np.isfinite(baseline)
        if name in ABSTAIN:
            lo, hi = ABSTAIN[name]
            trade = finite & ~((p >= lo) & (p <= hi))
            d = np.full(n, np.nan, dtype=float)
            d[finite] = 0.0
            d[trade] = (baseline[trade] - y[trade]) ** 2 - (p[trade] - y[trade]) ** 2
            differences[:, col] = d
        else:
            differences[finite, col] = (
                (baseline[finite] - y[finite]) ** 2
                - (p[finite] - y[finite]) ** 2
            )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        means = np.nanmean(differences, axis=0)
        observed = float(np.nanmax(means))
        centered = differences - means
        rng = np.random.default_rng(42)
        bootstrap = np.empty(500, dtype=float)
        for b in range(500):
            idx = block_resample(n, block_len, rng)
            bootstrap[b] = float(np.nanmax(np.nanmean(centered[idx], axis=0)))
    return {
        "observed_max_brier_improvement": observed,
        "family_p_value": float(np.mean(bootstrap >= observed)),
        "candidate_mean_brier_improvement": {
            name: float(value) for name, value in zip(METHODS, means)
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--results-root", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    audit = Audit()
    report = {
        "purpose": "Independent technical audit of Phase 7 Run #925 reference panels",
        "expected_run_id": args.expected_run_id,
        "expected_commit": args.expected_commit,
        "scope": [
            "immutable manifest, source and code hashes",
            "all ten Parquet panels and provenance columns",
            "source-derived labels, future returns, timestamps and block assignments",
            "independent reconciliation of 100 method/horizon metric cells and bootstrap accuracy intervals",
            "independent reconciliation of probability-bin future returns and chronological block diagnostics",
            "independent reproduction of ten family-level moving-block bootstrap tests against frozen abstention semantics",
            "independent audit of finite regime-feature eligibility against the frozen P08/P09/P10 specification",
        ],
        "scientific_promotion": "NOT_GRANTED",
        "method_specification": "research/phase7/PHASE7_METHOD_SPEC.md",
        "tester_observation": "A REQUEST CHANGES decision means no empirical candidate or trading strategy can be promoted; source and numerical reconciliations are evaluated separately from protocol-compliance failures.",
    }

    try:
        root = args.artifact_root
        result_root = args.results_root
        source = args.source_root
        manifest_path = root / "phase7_reference" / "phase7_reference_manifest.json"
        aggregate_path = root / "phase7_ensemble_results.json"
        results_copy = result_root / "phase7_ensemble_results.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        aggregate_bytes = aggregate_path.read_bytes()
        aggregate = json.loads(aggregate_bytes)
        manifest_hash = sha256(manifest_path)

        audit.check("manifest_complete", manifest.get("status") == "COMPLETE", manifest.get("status"))
        audit.check("schema_version", manifest.get("schema_version") == 1, manifest.get("schema_version"))
        audit.check("run_id_exact", str(manifest.get("run_id")) == args.expected_run_id, manifest.get("run_id"))
        audit.check("commit_exact", manifest.get("commit") == args.expected_commit, manifest.get("commit"))
        audit.check("seed_frozen", manifest.get("seed") == 42, manifest.get("seed"))
        audit.check("protocol_path_frozen", manifest.get("protocol") == "research/phase7/PHASE7_METHOD_SPEC.md", manifest.get("protocol"))
        audit.check("aggregate_hash", sha256(aggregate_path) == manifest["aggregate_result"]["sha256"],
                    {"expected": manifest["aggregate_result"]["sha256"], "actual": sha256(aggregate_path)})
        audit.check("results_artifact_exists", results_copy.is_file(), str(results_copy))
        if results_copy.is_file():
            audit.check("aggregate_artifact_byte_identity", results_copy.read_bytes() == aggregate_bytes,
                        {"reference_sha256": sha256(aggregate_path), "results_sha256": sha256(results_copy)})

        expected_panels = {
            ("daily", h) for h in EXPECTED_DAILY
        } | {("intraday", h) for h in EXPECTED_INTRADAY}
        actual_panels = {(p.get("layer"), int(p.get("horizon", -1))) for p in manifest.get("prediction_panels", [])}
        audit.check("ten_expected_panel_identities", len(manifest.get("prediction_panels", [])) == 10 and actual_panels == expected_panels,
                    {"count": len(manifest.get("prediction_panels", [])), "identities": sorted(map(str, actual_panels))})

        for path, expected_hash in manifest.get("code_files", {}).items():
            actual_path = source / path
            actual_hash = sha256(actual_path) if actual_path.is_file() else None
            audit.check("code_hash:" + path, actual_hash == expected_hash,
                        {"expected": expected_hash, "actual": actual_hash})
        for _, record in manifest.get("source_files", {}).items():
            path = source / record["path"]
            actual_hash = sha256(path) if path.is_file() else None
            audit.check("source_hash:" + record["path"], actual_hash == record["sha256"],
                        {"expected": record["sha256"], "actual": actual_hash})

        # Import the frozen source modules from the exact source snapshot, not from this tester branch.
        sys.path.insert(0, str(source / "scripts"))
        import run_phase3_daily_baselines as p3d
        import run_phase3_intraday_baselines as p3i
        import run_phase6_novel as p6

        daily = p3d.load_daily()
        intraday = p3i.load()
        audit.check("daily_source_rows", int(len(daily)) == int(aggregate["daily"]["rows"]),
                    {"source": len(daily), "artifact": aggregate["daily"]["rows"]})
        audit.check("intraday_source_rows", int(len(intraday)) == int(aggregate["intraday"]["rows"]),
                    {"source": len(intraday), "artifact": aggregate["intraday"]["rows"]})

        summary = {"layers": {}, "per_cell_metrics_checked": 0, "family_tests_checked": 0}
        for layer, horizons in (("daily", EXPECTED_DAILY), ("intraday", EXPECTED_INTRADAY)):
            summary["layers"][layer] = {"horizons": {}, "panels": 0}
            for horizon in horizons:
                identity = (layer, horizon)
                panel_record = next(
                    p for p in manifest["prediction_panels"]
                    if (p["layer"], int(p["horizon"])) == identity
                )
                rel = Path(panel_record["path"]).relative_to("data/reports")
                panel_path = root / rel
                panel_hash = sha256(panel_path) if panel_path.is_file() else None
                audit.check(f"panel_file_hash:{layer}:H{horizon}", panel_hash == panel_record["sha256"],
                            {"expected": panel_record["sha256"], "actual": panel_hash})
                panel = pd.read_parquet(panel_path)
                audit.check(f"panel_row_count:{layer}:H{horizon}", len(panel) == panel_record["rows"],
                            {"actual": len(panel), "expected": panel_record["rows"]})
                audit.check(f"panel_columns:{layer}:H{horizon}", list(panel.columns) == panel_record["columns"],
                            {"actual": list(panel.columns), "expected": panel_record["columns"]})

                required = ["layer", "horizon", "source_row_index", "decision_timestamp",
                            "label_direction", "future_return", "block_index"] + METHODS + ["source_run_id", "source_commit"]
                audit.check(f"required_columns:{layer}:H{horizon}", list(panel.columns) == required,
                            {"actual": list(panel.columns), "expected": required})
                audit.check(f"layer_value:{layer}:H{horizon}", set(panel["layer"].astype(str)) == {layer},
                            set(panel["layer"].astype(str).unique()))
                audit.check(f"horizon_value:{layer}:H{horizon}", set(pd.to_numeric(panel["horizon"]).astype(int)) == {horizon},
                            set(pd.to_numeric(panel["horizon"]).astype(int).unique()))
                audit.check(f"source_run_id:{layer}:H{horizon}", set(panel["source_run_id"].astype(str)) == {args.expected_run_id},
                            set(panel["source_run_id"].astype(str).unique()))
                audit.check(f"source_commit:{layer}:H{horizon}", set(panel["source_commit"].astype(str)) == {args.expected_commit},
                            set(panel["source_commit"].astype(str).unique()))
                expected_index = np.arange(len(panel), dtype=int)
                panel_index = pd.to_numeric(panel["source_row_index"], errors="raise").to_numpy(dtype=int)
                audit.check(f"source_row_index:{layer}:H{horizon}", np.array_equal(panel_index, expected_index),
                            {"first": panel_index[:3].tolist(), "last": panel_index[-3:].tolist()})
                y = pd.to_numeric(panel["label_direction"], errors="coerce").to_numpy(dtype=float)
                future = pd.to_numeric(panel["future_return"], errors="coerce").to_numpy(dtype=float)
                block_index = pd.to_numeric(panel["block_index"], errors="raise").to_numpy(dtype=int)
                audit.check(f"binary_or_missing_labels:{layer}:H{horizon}",
                            np.isin(y[np.isfinite(y)], [0.0, 1.0]).all(), "labels must be 0, 1 or NaN")
                audit.check(f"block_indices_nonnegative:{layer}:H{horizon}", np.all(block_index >= 0),
                            {"min": int(block_index.min()), "max": int(block_index.max())})
                audit.check(f"block_indices_contiguous:{layer}:H{horizon}",
                            np.array_equal(np.unique(block_index), np.arange(int(block_index.max()) + 1)),
                            np.unique(block_index).tolist())
                probs = {name: pd.to_numeric(panel[name], errors="coerce").to_numpy(dtype=float) for name in METHODS}
                probability_bounds = all(np.isfinite(v[np.isfinite(v)]).all() and
                                         ((v[np.isfinite(v)] >= 0) & (v[np.isfinite(v)] <= 1)).all()
                                         for v in probs.values())
                audit.check(f"probability_bounds:{layer}:H{horizon}", probability_bounds, "finite prediction values must be within [0,1]")
                audit.check(f"P05_duplicate_of_P01:{layer}:H{horizon}", np.array_equal(probs["P05"], probs["P01"], equal_nan=True), "")
                audit.check(f"P06_duplicate_of_P01:{layer}:H{horizon}", np.array_equal(probs["P06"], probs["P01"], equal_nan=True), "")
                audit.check(f"P10_duplicate_of_P09:{layer}:H{horizon}", np.array_equal(probs["P10"], probs["P09"], equal_nan=True), "")

                # Reconstruct label, forward return and timestamp arrays from the frozen raw source.
                if layer == "daily":
                    source_y, source_future = p3d.make_label(daily, horizon)
                    expected_y = source_y.to_numpy(dtype=float)
                    expected_future = source_future.to_numpy(dtype=float)
                    expected_times = pd.to_datetime(daily["date"], errors="raise").reset_index(drop=True)
                    expected_blocks = np.arange(len(panel), dtype=int) // 20
                    block_len = 20
                else:
                    grid = (
                        (intraday["minute_of_day"] >= 570)
                        & (intraday["minute_of_day"] <= 930)
                        & (((intraday["minute_of_day"] - 570) % 60) == 0)
                    )
                    decision_idx = np.flatnonzero(grid.to_numpy())
                    source_y, source_future, _ = p6.intraday_labels(intraday["timestamp"], intraday["spot"], horizon)
                    expected_y = source_y.iloc[decision_idx].to_numpy(dtype=float)
                    expected_future = source_future.iloc[decision_idx].to_numpy(dtype=float)
                    expected_times = pd.to_datetime(intraday.loc[grid, "timestamp"], utc=True).reset_index(drop=True)
                    session_dates = expected_times.dt.tz_convert("Asia/Kolkata").dt.date
                    unique_dates = pd.Index(session_dates).drop_duplicates()
                    date_block = {day: idx // 20 for idx, day in enumerate(unique_dates)}
                    expected_blocks = np.asarray([date_block[day] for day in session_dates], dtype=int)
                    block_len = 60

                if layer == "daily":
                    actual_times = pd.to_datetime(panel["decision_timestamp"], errors="raise").reset_index(drop=True)
                    time_match = actual_times.equals(expected_times)
                else:
                    actual_times = pd.to_datetime(panel["decision_timestamp"], utc=True).reset_index(drop=True)
                    time_match = actual_times.equals(expected_times)
                audit.check(f"source_timestamps:{layer}:H{horizon}", time_match,
                            {"panel_start": str(actual_times.iloc[0]), "source_start": str(expected_times.iloc[0]),
                             "panel_end": str(actual_times.iloc[-1]), "source_end": str(expected_times.iloc[-1])})
                audit.check(f"source_labels:{layer}:H{horizon}", arrays_match(y, expected_y),
                            {"panel_rows": len(y), "source_rows": len(expected_y)})
                audit.check(f"source_future_returns:{layer}:H{horizon}", arrays_match(future, expected_future),
                            {"panel_rows": len(future), "source_rows": len(expected_future)})
                audit.check(f"chronological_block_assignment:{layer}:H{horizon}",
                            np.array_equal(block_index, expected_blocks),
                            {"actual_blocks": int(block_index.max()) + 1, "expected_blocks": int(expected_blocks.max()) + 1})

                # Independently apply the frozen regime definition. Rows without finite vol/trend
                # cannot belong to a low/low state; they remain eligible only for the pooled prior.
                regime_source = daily if layer == "daily" else intraday
                if layer == "daily":
                    regime_returns = daily["log_close"].diff().to_numpy(dtype=float)
                    selected_rows = np.arange(len(daily), dtype=int)
                else:
                    regime_returns = np.log(intraday["spot"].astype(float)).diff().to_numpy(dtype=float)
                    selected_rows = decision_idx
                full_vol = pd.Series(regime_returns).rolling(20).std(ddof=1).to_numpy()
                full_trend = np.abs(pd.Series(regime_returns).rolling(20).mean().to_numpy()) / (full_vol + 1e-12)
                regime_vol, regime_trend = full_vol[selected_rows], full_trend[selected_rows]
                expected_p8, expected_p9, expected_regime_diag, expected_fallback = (
                    independently_calculate_regime_predictions(
                        y, probs["P01"], probs["P04"], regime_vol, regime_trend, block_index
                    )
                )
                audit.check(f"spec_regime_P08_predictions:{layer}:H{horizon}",
                            arrays_match(probs["P08"], expected_p8),
                            "P08 should use state rates built only from training rows with finite volatility and trend")
                audit.check(f"spec_regime_P09_predictions:{layer}:H{horizon}",
                            arrays_match(probs["P09"], expected_p9),
                            "P09 should use state rates built only from training rows with finite volatility and trend")

                # Recalculate the published per-method metrics independently from the panel arrays.
                published_horizon = aggregate[layer]["horizons"][str(horizon)]
                actual_regime_diag = published_horizon["P08"].get("regime_diagnostics", [])
                audit.check(f"spec_regime_training_counts:{layer}:H{horizon}",
                            nearly_equal_json(actual_regime_diag, expected_regime_diag),
                            {"published_first": actual_regime_diag[:1], "spec_first": expected_regime_diag[:1]})
                audit.check(f"spec_regime_fallback_count:{layer}:H{horizon}",
                            published_horizon["P08"].get("regime_fallback_count") == expected_fallback,
                            {"published": published_horizon["P08"].get("regime_fallback_count"),
                             "spec": expected_fallback})
                audit.check(f"spec_regime_P09_diagnostics:{layer}:H{horizon}",
                            nearly_equal_json(published_horizon["P09"].get("regime_diagnostics", []), expected_regime_diag),
                            "")
                audit.check(f"spec_regime_P10_diagnostics:{layer}:H{horizon}",
                            nearly_equal_json(published_horizon["P10"].get("regime_diagnostics", []), expected_regime_diag),
                            "")
                for name in METHODS:
                    calculated = independently_calculate_metrics(y, probs[name], name)
                    published = published_horizon[name]
                    for field in METRIC_FIELDS:
                        audit.check(f"metric:{layer}:H{horizon}:{name}:{field}",
                                    numeric_match(calculated.get(field), published.get(field)),
                                    {"calculated": calculated.get(field), "published": published.get(field)})

                    metric_mask = np.isfinite(y) & np.isfinite(probs[name])
                    if name in ABSTAIN:
                        lo, hi = ABSTAIN[name]
                        metric_mask &= ~((probs[name] >= lo) & (probs[name] <= hi))
                    yy = y[metric_mask].astype(int)
                    pp = np.clip(probs[name][metric_mask], 1e-6, 1 - 1e-6)
                    ff = future[metric_mask]
                    accuracy_ci = independently_calculate_accuracy_bootstrap(yy, pp, block_len)
                    stored_ci = published.get("accuracy_block_bootstrap_95", {})
                    for field in ("lower", "upper", "median"):
                        audit.check(f"accuracy_ci:{layer}:H{horizon}:{name}:{field}",
                                    numeric_match(accuracy_ci.get(field), stored_ci.get(field)),
                                    {"calculated": accuracy_ci.get(field), "published": stored_ci.get(field)})
                    fixed_bins = independently_calculate_fixed_bins(yy, pp, ff)
                    stored_bins = published.get("future_return_by_probability_bin", {})
                    for bin_name, bin_record in fixed_bins.items():
                        stored_record = stored_bins.get(bin_name, {})
                        audit.check(f"future_bin_n:{layer}:H{horizon}:{name}:{bin_name}",
                                    bin_record["n"] == stored_record.get("n"),
                                    {"calculated": bin_record["n"], "published": stored_record.get("n")})
                        audit.check(f"future_bin_mean:{layer}:H{horizon}:{name}:{bin_name}",
                                    numeric_match(bin_record["mean_future_return"], stored_record.get("mean_future_return")),
                                    {"calculated": bin_record["mean_future_return"], "published": stored_record.get("mean_future_return")})
                    finite_predictions = np.isfinite(probs[name])
                    if name in ABSTAIN:
                        lo, hi = ABSTAIN[name]
                        expected_trade_n = int((finite_predictions & ~((probs[name] >= lo) & (probs[name] <= hi))).sum())
                        expected_evaluable_n = int(finite_predictions.sum())
                        expected_coverage = float(expected_trade_n / expected_evaluable_n) if expected_evaluable_n else 0.0
                        metadata_match = (
                            published.get("trade_n") == expected_trade_n
                            and published.get("evaluable_n") == expected_evaluable_n
                            and numeric_match(published.get("coverage"), expected_coverage)
                        )
                    else:
                        expected_trade_n = None
                        expected_evaluable_n = None
                        expected_coverage = None
                        metadata_match = "trade_n" not in published and "coverage" not in published
                    audit.check(f"abstention_counts:{layer}:H{horizon}:{name}", metadata_match,
                                {"published_trade_n": published.get("trade_n"),
                                 "expected_trade_n": expected_trade_n,
                                 "published_evaluable_n": published.get("evaluable_n"),
                                 "expected_evaluable_n": expected_evaluable_n,
                                 "published_coverage": published.get("coverage"),
                                 "expected_coverage": expected_coverage})
                    # Chronological block diagnostics should use the candidate's same eligibility mask,
                    # including the abstention rule where one is frozen.
                    stored_blocks = published.get("chronological_blocks", [])
                    expected_blocks_diag = []
                    for block_id in range(int(block_index.max()) + 1):
                        rows = np.flatnonzero(block_index == block_id)
                        keep = np.isfinite(y[rows]) & np.isfinite(probs[name][rows])
                        if name in ABSTAIN:
                            lo, hi = ABSTAIN[name]
                            keep &= ~((probs[name][rows] >= lo) & (probs[name][rows] <= hi))
                        if not keep.any():
                            continue
                        by = y[rows][keep].astype(int)
                        bp = np.clip(probs[name][rows][keep], 1e-6, 1 - 1e-6)
                        expected_blocks_diag.append({
                            "n": int(len(by)),
                            "accuracy": float(np.mean((bp >= 0.5) == by)),
                            "balanced_accuracy": float(balanced_accuracy_score(by, (bp >= 0.5).astype(int))),
                            "brier": float(np.mean((bp - by) ** 2)),
                        })
                    audit.check(f"chronological_block_metrics:{layer}:H{horizon}:{name}",
                                nearly_equal_json(stored_blocks, expected_blocks_diag),
                                {"published_count": len(stored_blocks), "expected_count": len(expected_blocks_diag)})
                    summary["per_cell_metrics_checked"] += 1

                # Independently reproduce the family-wise maximum-statistic block bootstrap.
                family = independently_calculate_family_test(
                    y, probs, block_index, block_len
                )
                published_family = published_horizon["_FAMILY_TEST"]
                for field in ("observed_max_brier_improvement", "family_p_value"):
                    audit.check(f"family_metric:{layer}:H{horizon}:{field}",
                                numeric_match(family[field], published_family[field]),
                                {"calculated": family[field], "published": published_family[field]})
                stored_means = published_family.get("candidate_mean_brier_improvement", {})
                for name, val in family["candidate_mean_brier_improvement"].items():
                    audit.check(f"family_mean:{layer}:H{horizon}:{name}",
                                numeric_match(val, stored_means.get(name)),
                                {"calculated": val, "published": stored_means.get(name)})
                summary["family_tests_checked"] += 1
                summary["layers"][layer]["horizons"][str(horizon)] = {
                    "n_rows": int(len(panel)),
                    "family_max_brier_improvement": family["observed_max_brier_improvement"],
                    "family_p_value": family["family_p_value"],
                    "P08": {
                        "n": published_horizon["P08"].get("n"),
                        "accuracy": published_horizon["P08"].get("accuracy"),
                        "balanced_accuracy": published_horizon["P08"].get("balanced_accuracy"),
                        "brier": published_horizon["P08"].get("brier"),
                        "roc_auc": published_horizon["P08"].get("roc_auc"),
                    },
                }
                summary["layers"][layer]["panels"] += 1

        report["summary"] = summary
        report["manifest_sha256"] = manifest_hash
        report["source_commit"] = manifest.get("commit")
        report["source_runtime"] = manifest.get("runtime")
        report["audit"] = audit.summary()
        report["decision"] = (
            "PASS WITH SCOPED RESTRICTIONS — artifact integrity, source alignment, metric reconciliation and family inference"
            if audit.failed == 0 else "REQUEST CHANGES — one or more independent artifact checks failed"
        )
    except Exception as exc:
        audit.check("fatal_audit_exception", False, f"{type(exc).__name__}: {exc}")
        report["audit"] = audit.summary()
        report["decision"] = "REQUEST CHANGES — audit terminated before full reconciliation"
        report["exception"] = f"{type(exc).__name__}: {exc}"

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "decision": report.get("decision"),
        "checks_passed": report.get("audit", {}).get("checks_passed"),
        "checks_failed": report.get("audit", {}).get("checks_failed"),
        "summary": report.get("summary", {}),
        "exception": report.get("exception"),
        "report": str(args.report),
    }, indent=2, sort_keys=True))
    raise SystemExit(0 if report.get("decision", "").startswith("PASS") else 1)


if __name__ == "__main__":
    main()
