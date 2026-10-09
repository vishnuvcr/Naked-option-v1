from __future__ import annotations

import json
import math
import re

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, log_loss, roc_auc_score,
)
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "reports" / "available_global_prediction_results.json"
HORIZONS = (1, 2, 3, 5, 10)
METHODS = (
    "G01_SENSEX", "G02_BANKNIFTY", "G04_SP500", "G05_NASDAQ",
    "G06_ASIA_COMPOSITE", "G08_VIX", "G09_USDINR", "G11_GOLD",
    "G12_CRUDE", "G13_GLOBAL_EQUITY_COMPOSITE", "G16_INDIAVIX",
    "G18_CALENDAR_CONTROL",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _fail(message: str) -> None:
    raise ValueError(message)


def _finite_number(value: Any, name: str, low: float | None = None, high: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        _fail(f"{name} must be a finite number")
    result = float(value)
    if low is not None and result < low:
        _fail(f"{name} is below {low}")
    if high is not None and result > high:
        _fail(f"{name} is above {high}")
    return result


def _validate_metrics(cell: dict, name: str, *, require_paired: bool = False) -> None:
    n = cell.get("n")
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        _fail(f"{name}: executed metric cell must have n > 0")
    counts = []
    for key in ("tn", "fp", "fn", "tp"):
        value = cell.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _fail(f"{name}: {key} must be a non-negative integer")
        counts.append(value)
    if sum(counts) != n:
        _fail(f"{name}: confusion counts do not sum to n")
    acc = _finite_number(cell.get("accuracy"), f"{name}.accuracy", 0.0, 1.0)
    expected_acc = (cell["tn"] + cell["tp"]) / n
    if abs(acc - expected_acc) > 1e-12:
        _fail(f"{name}: accuracy does not reconcile with confusion counts")
    positive_rate = _finite_number(cell.get("positive_rate"), f"{name}.positive_rate", 0.0, 1.0)
    if abs(positive_rate - (cell["tp"] + cell["fn"]) / n) > 1e-12:
        _fail(f"{name}: positive rate does not reconcile with confusion counts")
    for key in ("balanced_accuracy", "brier", "prediction_mean"):
        high = 1.0 if key in {"balanced_accuracy", "brier", "prediction_mean"} else None
        _finite_number(cell.get(key), f"{name}.{key}", 0.0 if key in {"balanced_accuracy", "brier"} else None, high)
    if cell.get("prediction_std") is not None:
        _finite_number(cell.get("prediction_std"), f"{name}.prediction_std", 0.0)
    _finite_number(cell.get("log_loss"), f"{name}.log_loss", 0.0)
    for key in ("roc_auc", "pr_auc"):
        value = cell.get(key)
        if value is not None:
            _finite_number(value, f"{name}.{key}", 0.0, 1.0)
    if cell["tn"] + cell["fp"] > 0 and cell["tp"] + cell["fn"] > 0:
        sensitivity = cell["tp"] / (cell["tp"] + cell["fn"])
        specificity = cell["tn"] / (cell["tn"] + cell["fp"])
        expected_balanced = (sensitivity + specificity) / 2.0
        if abs(float(cell["balanced_accuracy"]) - expected_balanced) > 1e-12:
            _fail(f"{name}: balanced accuracy does not reconcile with confusion counts")
    if require_paired:
        paired = cell.get("paired_baseline_comparison")
        if not isinstance(paired, dict) or paired.get("status") != "EXECUTED":
            _fail(f"{name}: missing executed paired baseline comparison")
        if paired.get("n_common") != n:
            _fail(f"{name}: paired comparison row count differs from candidate metric n")
        baseline_metrics = paired.get("baseline_metrics")
        if not isinstance(baseline_metrics, dict):
            _fail(f"{name}: paired baseline metrics missing")
        _validate_metrics(baseline_metrics, f"{name}.paired_baseline_metrics")
        candidate_brier = _finite_number(paired.get("candidate_brier"), f"{name}.paired_candidate_brier", 0.0, 1.0)
        baseline_brier = _finite_number(paired.get("baseline_brier"), f"{name}.paired_baseline_brier", 0.0, 1.0)
        improvement = _finite_number(paired.get("brier_improvement"), f"{name}.paired_brier_improvement")
        if baseline_metrics.get("n") != n:
            _fail(f"{name}: paired baseline sample count differs from candidate count")
        if abs(candidate_brier - float(cell["brier"])) > 1e-12:
            _fail(f"{name}: paired candidate Brier score differs from reported candidate Brier")
        if abs(baseline_brier - float(baseline_metrics["brier"])) > 1e-12:
            _fail(f"{name}: paired baseline Brier score does not reconcile")
        if abs(improvement - (baseline_brier - candidate_brier)) > 1e-12:
            _fail(f"{name}: paired Brier improvement sign/formula is wrong")


def validate_result_payload(result: dict) -> None:
    """Validate complete result grid, paired baselines, and frozen inference contract."""
    if not isinstance(result, dict):
        _fail("result root must be a JSON object")
    daily = result.get("daily")
    if not isinstance(daily, dict) or not isinstance(daily.get("horizons"), dict):
        _fail("missing daily.horizons object")
    horizons = daily["horizons"]
    expected_horizon_keys = {str(h) for h in HORIZONS}
    if set(horizons) != expected_horizon_keys:
        _fail(f"horizon grid differs from registered set: {sorted(horizons)}")
    expected_cells = set(METHODS) | {"_BASELINE", "_FAMILY_TEST"}
    executed_family = {}
    for horizon in HORIZONS:
        cells = horizons[str(horizon)]
        if not isinstance(cells, dict) or set(cells) != expected_cells:
            missing = sorted(expected_cells - set(cells if isinstance(cells, dict) else {}))
            unexpected = sorted(set(cells if isinstance(cells, dict) else {}) - expected_cells)
            _fail(f"horizon {horizon}: cell grid mismatch missing={missing} unexpected={unexpected}")
        for method in METHODS:
            cell = cells[method]
            name = f"horizon={horizon}/{method}"
            if not isinstance(cell, dict):
                _fail(f"{name}: cell must be an object")
            status = cell.get("status")
            if status == "BLOCKED_DATA":
                if not isinstance(cell.get("reason"), str) or not cell["reason"].strip():
                    _fail(f"{name}: BLOCKED_DATA cell requires a non-empty reason")
                if "n" in cell and cell["n"] != 0:
                    _fail(f"{name}: BLOCKED_DATA cell with n must have n=0")
                continue
            if status != "EXECUTED":
                _fail(f"{name}: status must be EXECUTED or BLOCKED_DATA")
            _validate_metrics(cell, name, require_paired=True)
            if cell.get("horizon_sessions") != horizon:
                _fail(f"{name}: horizon metadata mismatch")
            if not isinstance(cell.get("source_ids"), list) or not isinstance(cell.get("feature_columns"), list):
                _fail(f"{name}: source_ids and feature_columns must be arrays")
        baseline = cells["_BASELINE"]
        if not isinstance(baseline, dict):
            _fail(f"horizon={horizon}/_BASELINE must be an object")
        if baseline.get("status") == "EXECUTED":
            _validate_metrics(baseline, f"horizon={horizon}/_BASELINE")
            if baseline.get("horizon_sessions") != horizon:
                _fail(f"horizon={horizon}/_BASELINE horizon metadata mismatch")
            if not isinstance(baseline.get("evaluation_scope"), str) or not baseline["evaluation_scope"].strip():
                _fail(f"horizon={horizon}/_BASELINE requires explicit evaluation_scope")
        elif baseline.get("status") == "NOT_APPLICABLE":
            if not isinstance(baseline.get("reason"), str) or not baseline["reason"].strip():
                _fail(f"horizon={horizon}/_BASELINE NOT_APPLICABLE requires a reason")
        else:
            _fail(f"horizon={horizon}/_BASELINE has invalid status")

        family = cells["_FAMILY_TEST"]
        if not isinstance(family, dict):
            _fail(f"horizon={horizon}/_FAMILY_TEST must be an object")
        if family.get("status") == "EXECUTED":
            raw_p = _finite_number(family.get("family_p_value"), f"horizon={horizon}/family_p_value", 0.0, 1.0)
            n_common = family.get("n_common")
            if isinstance(n_common, bool) or not isinstance(n_common, int) or n_common < 100:
                _fail(f"horizon={horizon}: executed family test needs at least 100 common observations")
            if family.get("bootstrap_reps") != 500 or family.get("block_length") != 20 or family.get("seed") != 42:
                _fail(f"horizon={horizon}: bootstrap settings differ from registered values")
            executed_methods = [m for m in METHODS if cells[m].get("status") == "EXECUTED"]
            if family.get("method_count") != len(executed_methods):
                _fail(f"horizon={horizon}: family method count does not equal executed candidate count")
            improvements = family.get("candidate_mean_brier_improvements")
            if not isinstance(improvements, dict) or set(improvements) != set(executed_methods):
                _fail(f"horizon={horizon}: family candidate improvement set mismatch")
            for method, value in improvements.items():
                _finite_number(value, f"horizon={horizon}/{method}.mean_brier_improvement")
            _finite_number(family.get("max_mean_brier_improvement"), f"horizon={horizon}.max_mean_brier_improvement")
            executed_family[horizon] = raw_p
        elif family.get("status") == "NOT_APPLICABLE":
            if not isinstance(family.get("reason"), str) or not family["reason"].strip():
                _fail(f"horizon={horizon}/_FAMILY_TEST NOT_APPLICABLE requires a reason")
        else:
            _fail(f"horizon={horizon}/_FAMILY_TEST has invalid status")

    inference = result.get("family_inference")
    if not isinstance(inference, dict):
        _fail("missing family_inference object")
    if inference.get("registered_family_size") != len(HORIZONS):
        _fail("family_inference registered_family_size must equal five registered horizons")
    if inference.get("registered_horizons") != list(HORIZONS):
        _fail("family_inference registered_horizons differs from the frozen horizon set")
    if inference.get("family_tests") != len(executed_family) or inference.get("family_tests_executed") != len(executed_family):
        _fail("family_inference executed test count does not reconcile")
    if inference.get("status") != ("EXECUTED" if executed_family else "NOT_APPLICABLE"):
        _fail("family_inference status does not reconcile with horizon tests")
    adjusted = inference.get("bonferroni_adjusted_p_values")
    if not isinstance(adjusted, list) or len(adjusted) != len(executed_family):
        _fail("family_inference adjusted-p list does not reconcile with executed tests")
    seen = set()
    for item in adjusted:
        if not isinstance(item, dict):
            _fail("Bonferroni p-value entry must be an object")
        h = item.get("horizon_sessions")
        if h not in executed_family or h in seen:
            _fail(f"unexpected/duplicate horizon in adjusted-p list: {h}")
        seen.add(h)
        raw = _finite_number(item.get("raw_p_value"), f"horizon={h}.raw_p_value", 0.0, 1.0)
        adj = _finite_number(item.get("bonferroni_p_value"), f"horizon={h}.bonferroni_p_value", 0.0, 1.0)
        if abs(raw - executed_family[h]) > 1e-12:
            _fail(f"horizon={h}: family raw p-value differs from horizon report")
        if abs(adj - min(1.0, raw * len(HORIZONS))) > 1e-12:
            _fail(f"horizon={h}: Bonferroni correction does not use the five-horizon family size")

    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        _fail("missing provenance object")
    if provenance.get("horizons") != list(HORIZONS):
        _fail("provenance horizon set mismatch")
    if provenance.get("holdout_status") != "final untouched holdout not opened":
        _fail("final untouched holdout must remain unopened")
    for key in ("nifty_sha256", "global_manifest_sha256"):
        value = provenance.get(key)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            _fail(f"provenance {key} must be a 64-character lowercase SHA-256")
    source_state = result.get("source_state")
    method_status = result.get("method_status")
    if not isinstance(source_state, dict) or not isinstance(method_status, dict):
        _fail("source_state and method_status must be objects")
    if set(method_status) != set(METHODS):
        _fail("top-level method_status set differs from registered candidate universe")
    for method, state in method_status.items():
        if not isinstance(state, dict):
            _fail(f"method_status/{method} must be an object")
        if state.get("status") == "BLOCKED_DATA":
            if not isinstance(state.get("reason"), str) or not state["reason"].strip():
                _fail(f"method_status/{method} BLOCKED_DATA requires a reason")
        elif state.get("status") == "REGISTERED":
            if not isinstance(state.get("source_ids"), list):
                _fail(f"method_status/{method} REGISTERED requires source_ids")
        else:
            _fail(f"method_status/{method} has invalid status")
    for source_id, state in source_state.items():
        if not isinstance(state, dict):
            _fail(f"source_state/{source_id} must be an object")
        if state.get("status") == "BLOCKED_DATA":
            if not isinstance(state.get("reason"), str) or not state["reason"].strip():
                _fail(f"source_state/{source_id} BLOCKED_DATA requires a reason")
        elif state.get("status") == "ACTIVE":
            if not isinstance(state.get("sha256"), str) or not SHA256_RE.fullmatch(state["sha256"]):
                _fail(f"source_state/{source_id} ACTIVE requires a SHA-256")
        else:
            _fail(f"source_state/{source_id} has invalid status")


def _metric_summary_from_rows(labels: np.ndarray, probabilities: np.ndarray, name: str) -> dict:
    y = np.asarray(labels, dtype=float)
    p = np.asarray(probabilities, dtype=float)
    mask = np.isfinite(y) & np.isfinite(p)
    yy = y[mask].astype(int)
    pp = np.clip(p[mask], 1e-6, 1 - 1e-6)
    if len(yy) == 0:
        _fail(f"{name}: row-level panel has no finite forecast rows")
    pred = (pp >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(yy, pred, labels=[0, 1]).ravel()
    return {
        "n": int(len(yy)),
        "positive_rate": float(yy.mean()),
        "accuracy": float(accuracy_score(yy, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(yy, pred)),
        "roc_auc": float(roc_auc_score(yy, pp)) if np.unique(yy).size == 2 else None,
        "pr_auc": float(average_precision_score(yy, pp)) if np.unique(yy).size == 2 else None,
        "brier": float(brier_score_loss(yy, pp)),
        "log_loss": float(log_loss(yy, pp, labels=[0, 1])),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "prediction_mean": float(pp.mean()),
        "prediction_std": float(pp.std(ddof=0)),
    }


def _match_metric_fields(expected: dict, actual: dict, name: str) -> None:
    for key in ("n", "tn", "fp", "fn", "tp"):
        if actual.get(key) != expected[key]:
            _fail(f"{name}: row-level {key} does not reconcile")
    for key in ("positive_rate", "accuracy", "balanced_accuracy", "brier", "log_loss", "prediction_mean", "prediction_std"):
        value = _finite_number(actual.get(key), f"{name}.{key}")
        if abs(value - float(expected[key])) > 1e-10:
            _fail(f"{name}: row-level {key} does not reconcile")
    for key in ("roc_auc", "pr_auc"):
        got = actual.get(key)
        want = expected[key]
        if got is None or want is None:
            if got is not None or want is not None:
                _fail(f"{name}: row-level {key} definedness does not reconcile")
        elif abs(_finite_number(got, f"{name}.{key}") - float(want)) > 1e-10:
            _fail(f"{name}: row-level {key} does not reconcile")


def _validate_family_from_panels(panel: pd.DataFrame, horizon: int, cells: dict) -> None:
    rows = panel.loc[panel["horizon_sessions"] == horizon]
    baseline = rows.loc[(rows["row_type"] == "baseline") & (rows["method"] == "_BASELINE")].sort_values("date")
    executed = [m for m in METHODS if cells[m].get("status") == "EXECUTED"]
    family = cells["_FAMILY_TEST"]
    if not executed:
        if family.get("status") != "NOT_APPLICABLE":
            _fail(f"horizon={horizon}: family test executed with no executed candidates")
        return
    if baseline.empty:
        if family.get("status") != "NOT_APPLICABLE":
            _fail(f"horizon={horizon}: family test executed without baseline panel rows")
        return
    baseline_by_date = baseline.set_index("date")["predicted_probability"].astype(float).to_dict()
    candidate_frames = {}
    common_dates = set(baseline_by_date)
    for method in executed:
        item = rows.loc[(rows["row_type"] == "candidate") & (rows["method"] == method)].copy()
        item["prediction_available"] = item["prediction_available"].map(
            lambda v: str(v).strip().lower() in {"true", "1"} if pd.notna(v) else False
        )
        available = item.loc[item["prediction_available"]].sort_values("date")
        candidate_frames[method] = available
        common_dates &= set(available["date"])
    dates = sorted(common_dates)
    if len(dates) < 100:
        if family.get("status") != "NOT_APPLICABLE":
            _fail(f"horizon={horizon}: family test executed with fewer than 100 common panel rows")
        if family.get("n_common", len(dates)) != len(dates):
            _fail(f"horizon={horizon}: not-applicable family common-row count does not reconcile")
        return
    if family.get("status") != "EXECUTED":
        _fail(f"horizon={horizon}: family test marked not applicable despite sufficient common panel rows")

    y_base = baseline.set_index("date")["actual_direction"].astype(int).to_dict()
    yy = np.asarray([y_base[d] for d in dates], dtype=int)
    bb = np.clip(np.asarray([baseline_by_date[d] for d in dates], dtype=float), 1e-6, 1 - 1e-6)
    names = sorted(executed)
    pmap = {}
    for method in names:
        item = candidate_frames[method].set_index("date")
        yy_method = item.loc[dates, "actual_direction"].astype(int).to_numpy()
        if not np.array_equal(yy_method, yy):
            _fail(f"horizon={horizon}/{method}: actual labels differ within common panel rows")
        candidate_baseline = item.loc[dates, "baseline_probability"].astype(float).to_numpy()
        if not np.allclose(candidate_baseline, bb, rtol=0.0, atol=1e-12):
            _fail(f"horizon={horizon}/{method}: baseline probabilities differ from common baseline panel")
        pmap[method] = np.clip(item.loc[dates, "predicted_probability"].astype(float).to_numpy(), 1e-6, 1 - 1e-6)

    base_loss = (yy - bb) ** 2
    differential = np.column_stack([base_loss - (yy - pmap[name]) ** 2 for name in names])
    observed_by_method = differential.mean(axis=0)
    observed = float(observed_by_method.max())
    centered = differential - observed_by_method.reshape(1, -1)
    rng = np.random.default_rng(42)
    n = len(yy)
    length = 20
    starts = np.arange(0, n - length + 1)
    blocks_per_rep = int(math.ceil(n / length))
    max_null = np.empty(500, dtype=float)
    for b in range(500):
        chosen = rng.choice(starts, size=blocks_per_rep, replace=True)
        take = np.concatenate([np.arange(s, s + length) for s in chosen])[:n]
        max_null[b] = float(centered[take].mean(axis=0).max())
    p_value = float((1 + np.sum(max_null >= observed)) / 501)
    if family.get("n_common") != n or family.get("method_count") != len(names):
        _fail(f"horizon={horizon}: family row/method count does not reconcile with panels")
    if abs(_finite_number(family.get("max_mean_brier_improvement"), f"horizon={horizon}.max_brier_improvement") - observed) > 1e-10:
        _fail(f"horizon={horizon}: maximum Brier improvement does not reconcile with panels")
    improvements = family.get("candidate_mean_brier_improvements", {})
    if set(improvements) != set(names):
        _fail(f"horizon={horizon}: family improvement map differs from executed panel methods")
    for i, name in enumerate(names):
        value = _finite_number(improvements[name], f"horizon={horizon}/{name}.family_improvement")
        if abs(value - float(observed_by_method[i])) > 1e-10:
            _fail(f"horizon={horizon}/{name}: family Brier improvement does not reconcile with panels")
    reported_p = _finite_number(family.get("family_p_value"), f"horizon={horizon}.family_p_value", 0.0, 1.0)
    if abs(reported_p - p_value) > 1e-12:
        _fail(f"horizon={horizon}: family bootstrap p-value does not reproduce from row-level panels")


def validate_prediction_panels(result: dict, panel: pd.DataFrame) -> None:
    """Independently recalculate candidate/baseline metrics and family tests from row-level outputs."""
    required = {
        "date", "horizon_sessions", "method", "row_type", "cell_status",
        "actual_direction", "future_log_return", "predicted_probability",
        "baseline_probability", "source_ids_json", "feature_columns_json", "prediction_available",
    }
    if not required.issubset(panel.columns):
        _fail(f"prediction panel missing columns: {sorted(required - set(panel.columns))}")
    if panel.empty:
        for h in HORIZONS:
            cells = result["daily"]["horizons"][str(h)]
            if cells["_BASELINE"].get("status") != "NOT_APPLICABLE" or any(cells[m].get("status") == "EXECUTED" for m in METHODS):
                _fail("prediction panel is empty despite executed forecast cells")
        return
    panel = panel.copy()
    panel["date"] = pd.to_datetime(panel["date"], errors="raise").dt.strftime("%Y-%m-%d")
    panel["horizon_sessions"] = pd.to_numeric(panel["horizon_sessions"], errors="raise").astype(int)
    panel["actual_direction"] = pd.to_numeric(panel["actual_direction"], errors="raise")
    panel["future_log_return"] = pd.to_numeric(panel["future_log_return"], errors="raise")
    panel["predicted_probability"] = pd.to_numeric(panel["predicted_probability"], errors="coerce")
    panel["baseline_probability"] = pd.to_numeric(panel["baseline_probability"], errors="coerce")
    if not set(panel["horizon_sessions"]).issubset(set(HORIZONS)):
        _fail("prediction panel contains an unregistered horizon")
    if panel[["date", "horizon_sessions", "method"]].duplicated().any():
        _fail("prediction panel has duplicate date/horizon/method keys")
    if not panel["row_type"].isin(["baseline", "candidate"]).all():
        _fail("prediction panel has an invalid row_type")
    if not panel["actual_direction"].isin([0, 1]).all():
        _fail("prediction panel labels must be binary 0/1")
    if not np.isfinite(panel["future_log_return"].to_numpy(dtype=float)).all():
        _fail("prediction panel has non-finite future returns")
    if not np.isfinite(panel["baseline_probability"].to_numpy(dtype=float)).all():
        _fail("prediction panel baseline probabilities must be finite")
    if ((panel["baseline_probability"] < 0) | (panel["baseline_probability"] > 1)).any():
        _fail("prediction panel baseline probabilities outside [0,1]")
    direction = np.where(panel["future_log_return"].to_numpy(dtype=float) > 0, 1,
                         np.where(panel["future_log_return"].to_numpy(dtype=float) < 0, 0, -1))
    if not np.array_equal(direction, panel["actual_direction"].to_numpy(dtype=int)):
        _fail("prediction panel actual direction does not match the sign of future log returns")
    for horizon in HORIZONS:
        cells = result["daily"]["horizons"][str(horizon)]
        rows = panel.loc[panel["horizon_sessions"] == horizon]
        base_rows = rows.loc[(rows["row_type"] == "baseline") & (rows["method"] == "_BASELINE")].sort_values("date")
        baseline = cells["_BASELINE"]
        if len(base_rows):
            if base_rows["cell_status"].nunique() != 1 or base_rows["cell_status"].iloc[0] != baseline.get("status"):
                _fail(f"horizon={horizon}: baseline panel status mismatch")
            if base_rows["predicted_probability"].isna().any():
                _fail(f"horizon={horizon}: baseline panel has missing probability")
            if not np.allclose(base_rows["predicted_probability"], base_rows["baseline_probability"], rtol=0.0, atol=1e-12):
                _fail(f"horizon={horizon}: baseline panel probabilities mismatch")
        if baseline.get("status") == "EXECUTED":
            if base_rows.empty or len(base_rows) != baseline.get("n"):
                _fail(f"horizon={horizon}: baseline panel count does not match headline metrics")
            metric = _metric_summary_from_rows(
                base_rows["actual_direction"].to_numpy(dtype=float),
                base_rows["predicted_probability"].to_numpy(dtype=float),
                f"horizon={horizon}/_BASELINE",
            )
            _match_metric_fields(metric, baseline, f"horizon={horizon}/_BASELINE")
        elif not base_rows.empty:
            _fail(f"horizon={horizon}: baseline rows exist for a not-applicable baseline")

        for method in METHODS:
            cell = cells[method]
            method_state = result["method_status"][method]
            item = rows.loc[(rows["row_type"] == "candidate") & (rows["method"] == method)].copy()
            if method_state.get("status") == "BLOCKED_DATA":
                if not item.empty or cell.get("status") != "BLOCKED_DATA":
                    _fail(f"horizon={horizon}/{method}: blocked source should not have candidate forecast rows")
                continue
            if baseline.get("status") != "EXECUTED" or base_rows.empty:
                if not item.empty:
                    _fail(f"horizon={horizon}/{method}: candidate rows exist without baseline row schedule")
                continue
            if item.empty or set(item["date"]) != set(base_rows["date"]):
                _fail(f"horizon={horizon}/{method}: candidate rows do not align with baseline label rows")
            if item["cell_status"].nunique() != 1 or item["cell_status"].iloc[0] != cell.get("status"):
                _fail(f"horizon={horizon}/{method}: candidate panel status mismatch")
            expected_sources = cell.get("source_ids", method_state.get("source_ids", []))
            expected_features = cell.get("feature_columns", [])
            if item["source_ids_json"].nunique() != 1 or json.loads(item["source_ids_json"].iloc[0]) != expected_sources:
                _fail(f"horizon={horizon}/{method}: source IDs do not match candidate metadata")
            if item["feature_columns_json"].nunique() != 1 or json.loads(item["feature_columns_json"].iloc[0]) != expected_features:
                _fail(f"horizon={horizon}/{method}: feature columns do not match candidate metadata")
            item = item.sort_values("date")
            base_sorted = base_rows.sort_values("date")
            if not np.array_equal(item["actual_direction"].astype(int).to_numpy(), base_sorted["actual_direction"].astype(int).to_numpy()):
                _fail(f"horizon={horizon}/{method}: actual labels do not align with baseline panel")
            if not np.allclose(item["future_log_return"], base_sorted["future_log_return"], rtol=0.0, atol=1e-12):
                _fail(f"horizon={horizon}/{method}: realized returns do not align with baseline panel")
            avail_raw = item["prediction_available"]
            if avail_raw.isna().any():
                _fail(f"horizon={horizon}/{method}: prediction_available missing for candidate row")
            available = avail_raw.map(lambda v: str(v).strip().lower() in {"true", "1"})
            finite_prob = np.isfinite(item["predicted_probability"].to_numpy(dtype=float))
            if not np.array_equal(available.to_numpy(dtype=bool), finite_prob):
                _fail(f"horizon={horizon}/{method}: prediction availability flag mismatches probability")
            if ((item.loc[available, "predicted_probability"] < 0) | (item.loc[available, "predicted_probability"] > 1)).any():
                _fail(f"horizon={horizon}/{method}: candidate probability outside [0,1]")
            candidate_rows = item.loc[available]
            if cell.get("status") == "EXECUTED":
                metric = _metric_summary_from_rows(
                    candidate_rows["actual_direction"].to_numpy(dtype=float),
                    candidate_rows["predicted_probability"].to_numpy(dtype=float),
                    f"horizon={horizon}/{method}",
                )
                _match_metric_fields(metric, cell, f"horizon={horizon}/{method}")
                paired_base_metric = _metric_summary_from_rows(
                    candidate_rows["actual_direction"].to_numpy(dtype=float),
                    candidate_rows["baseline_probability"].to_numpy(dtype=float),
                    f"horizon={horizon}/{method}/paired_baseline",
                )
                paired = cell["paired_baseline_comparison"]
                _match_metric_fields(paired_base_metric, paired["baseline_metrics"], f"horizon={horizon}/{method}/paired_baseline")
                candidate_brier = metric["brier"]
                baseline_brier = paired_base_metric["brier"]
                if paired.get("n_common") != metric["n"] or abs(float(paired["candidate_brier"]) - candidate_brier) > 1e-10:
                    _fail(f"horizon={horizon}/{method}: paired candidate sample/Brier mismatch")
                if abs(float(paired["baseline_brier"]) - baseline_brier) > 1e-10 or abs(float(paired["brier_improvement"]) - (baseline_brier - candidate_brier)) > 1e-10:
                    _fail(f"horizon={horizon}/{method}: paired baseline improvement sign or metric mismatch")
            elif cell.get("status") == "BLOCKED_DATA":
                if len(candidate_rows) or cell.get("n", 0) not in (None, 0):
                    _fail(f"horizon={horizon}/{method}: blocked cell contains finite predictions")
            else:
                _fail(f"horizon={horizon}/{method}: invalid status")
        _validate_family_from_panels(panel, horizon, cells)


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_output_file(path: Path = OUTPUT_PATH) -> dict:
    if not path.exists():
        _fail(f"result file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_result_payload(payload)
    nifty_path = ROOT / payload["provenance"]["nifty_source_path"]
    manifest_path = ROOT / payload["provenance"]["global_manifest_path"]
    if not nifty_path.is_file() or sha256_file(nifty_path) != payload["provenance"]["nifty_sha256"]:
        _fail("NIFTY source hash/path does not match provenance")
    if not manifest_path.is_file() or sha256_file(manifest_path) != payload["provenance"]["global_manifest_sha256"]:
        _fail("global manifest hash/path does not match provenance")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_ids = {r.get("id") for r in manifest.get("series", [])}
    if manifest_ids != set(payload["source_state"]):
        _fail("source_state IDs do not match acquisition manifest IDs")
    for record in manifest.get("series", []):
        if record.get("status") != "ACTIVE":
            continue
        source_path = ROOT / record["path"]
        if not source_path.is_file() or sha256_file(source_path) != record.get("sha256"):
            _fail(f"acquisition source path/hash mismatch: {record.get('id')}")
    panel_path = ROOT / payload["provenance"].get("prediction_panel_path", "")
    expected_panel_hash = payload["provenance"].get("prediction_panel_sha256", "")
    if not panel_path.is_file() or not SHA256_RE.fullmatch(expected_panel_hash):
        _fail("row-level prediction panel path/hash is missing or invalid")
    if sha256_file(panel_path) != expected_panel_hash:
        _fail("row-level prediction panel hash does not match provenance")
    panel = pd.read_csv(panel_path)
    validate_prediction_panels(payload, panel)
    return payload


def main() -> None:
    result = validate_output_file()
    print(json.dumps({
        "status": "PASS",
        "horizons": len(HORIZONS),
        "methods_per_horizon": len(METHODS),
        "executed_family_tests": result["family_inference"]["family_tests"],
        "registered_family_size": result["family_inference"]["registered_family_size"],
    }, indent=2))


if __name__ == "__main__":
    main()
