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
ABSTAIN = {"P05": (0.45, 0.55), "P06": (0.40, 0.60)}
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
            d = np.zeros(n, dtype=float)
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
            "independent reconciliation of 100 method/horizon metric cells",
            "independent reproduction of ten family-level moving-block bootstrap tests",
        ],
        "scientific_promotion": "NOT_GRANTED",
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

                # Recalculate the published per-method metrics independently from the panel arrays.
                published_horizon = aggregate[layer]["horizons"][str(horizon)]
                for name in METHODS:
                    calculated = independently_calculate_metrics(y, probs[name], name)
                    published = published_horizon[name]
                    for field in METRIC_FIELDS:
                        audit.check(f"metric:{layer}:H{horizon}:{name}:{field}",
                                    numeric_match(calculated.get(field), published.get(field)),
                                    {"calculated": calculated.get(field), "published": published.get(field)})
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
