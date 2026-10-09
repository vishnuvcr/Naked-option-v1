from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_phase7_available_global_results as validator


def sample_metrics(n: int = 100, brier: float = 0.24) -> dict:
    q = n // 4
    counts = {"tn": q, "fp": q, "fn": q, "tp": q}
    used = sum(counts.values())
    counts["tn"] += n - used
    return {
        "status": "EXECUTED",
        "n": n,
        "positive_rate": (counts["tp"] + counts["fn"]) / n,
        "accuracy": (counts["tn"] + counts["tp"]) / n,
        "balanced_accuracy": 0.5,
        "roc_auc": 0.52,
        "pr_auc": 0.5,
        "brier": brier,
        "log_loss": 0.69,
        **counts,
        "prediction_mean": 0.5,
        "prediction_std": 0.1,
        "classification_threshold": 0.5,
    }


def valid_payload() -> dict:
    horizons = {}
    method_names = list(validator.METHODS)
    for horizon in validator.HORIZONS:
        cells = {}
        for method in method_names:
            cell = sample_metrics(100, 0.24)
            cell.update({
                "horizon_sessions": horizon,
                "source_ids": [method],
                "feature_columns": ["feature_1"],
                "mean_future_log_return_when_predicted_up": 0.001,
                "paired_baseline_comparison": {
                    "status": "EXECUTED",
                    "n_common": 100,
                    "candidate_brier": 0.24,
                    "baseline_brier": 0.25,
                    "brier_improvement": 0.01,
                    "baseline_metrics": sample_metrics(100, 0.25),
                },
            })
            cells[method] = cell
        baseline = sample_metrics(120, 0.25)
        baseline.update({
            "horizon_sessions": horizon,
            "description": "causal historical rate",
            "evaluation_scope": "all eligible rows; compare on paired rows",
        })
        cells["_BASELINE"] = baseline
        raw_p = 0.03 if horizon == 1 else 0.20
        cells["_FAMILY_TEST"] = {
            "status": "EXECUTED",
            "n_common": 100,
            "method_count": len(method_names),
            "bootstrap_reps": 500,
            "block_length": 20,
            "seed": 42,
            "max_mean_brier_improvement": 0.01,
            "candidate_mean_brier_improvements": {method: 0.01 for method in method_names},
            "family_p_value": raw_p,
        }
        horizons[str(horizon)] = cells
    inference_entries = []
    for horizon in validator.HORIZONS:
        raw_p = horizons[str(horizon)]["_FAMILY_TEST"]["family_p_value"]
        inference_entries.append({
            "horizon_sessions": horizon,
            "raw_p_value": raw_p,
            "bonferroni_p_value": min(1.0, raw_p * len(validator.HORIZONS)),
        })
    method_status = {
        method: {"status": "REGISTERED", "source_ids": [method], "features": ["feature_1"]}
        for method in method_names
    }
    return {
        "daily": {"horizons": horizons},
        "source_state": {"SOURCE_A": {"status": "BLOCKED_DATA", "reason": "test fixture source unavailable"}},
        "method_status": method_status,
        "family_inference": {
            "status": "EXECUTED",
            "family_tests": len(validator.HORIZONS),
            "family_tests_executed": len(validator.HORIZONS),
            "registered_family_size": len(validator.HORIZONS),
            "registered_horizons": list(validator.HORIZONS),
            "bonferroni_adjusted_p_values": inference_entries,
            "bootstrap_method": "test fixture",
            "interpretation": "screening only",
        },
        "provenance": {
            "generated_at_utc": "2026-10-10T00:00:00+00:00",
            "git_sha": "a" * 40,
            "nifty_source_path": "data/cache/raw/phase3/nifty50_daily.csv",
            "nifty_sha256": "0" * 64,
            "global_manifest_path": "data/reports/available_global_source_manifest.json",
            "global_manifest_sha256": "1" * 64,
            "horizons": list(validator.HORIZONS),
            "min_train": 252,
            "test_block": 20,
            "bootstrap_reps": 500,
            "bootstrap_block": 20,
            "seed": 42,
            "decision_time_rule": "strict prior session",
            "holdout_status": "final untouched holdout not opened",
            "scope": "test fixture",
        },
    }


def expect_rejected(payload: dict, message_fragment: str) -> None:
    try:
        validator.validate_result_payload(payload)
    except (ValueError, TypeError) as exc:
        assert message_fragment in str(exc), (message_fragment, str(exc))
        return
    raise AssertionError(f"invalid payload was accepted; expected {message_fragment}")


def check_complete_payload_passes() -> None:
    validator.validate_result_payload(valid_payload())


def check_missing_baseline_cell_fails() -> None:
    payload = valid_payload()
    del payload["daily"]["horizons"]["1"]["_BASELINE"]
    expect_rejected(payload, "cell grid mismatch")


def check_bonferroni_uses_fixed_five_horizon_family() -> None:
    payload = valid_payload()
    payload["family_inference"]["bonferroni_adjusted_p_values"][0]["bonferroni_p_value"] = 0.03
    expect_rejected(payload, "five-horizon family size")


def check_blocked_candidate_requires_reason() -> None:
    payload = valid_payload()
    payload["daily"]["horizons"]["1"]["G08_VIX"] = {
        "status": "BLOCKED_DATA", "reason": "  ", "horizon_sessions": 1, "n": 0
    }
    expect_rejected(payload, "requires a non-empty reason")


def check_paired_baseline_sample_matches_candidate() -> None:
    payload = valid_payload()
    payload["daily"]["horizons"]["1"]["G01_SENSEX"]["paired_baseline_comparison"]["n_common"] = 99
    expect_rejected(payload, "paired comparison row count differs")


def check_horizon_family_inference_count_reconciles() -> None:
    payload = valid_payload()
    payload["family_inference"]["registered_family_size"] = 4
    expect_rejected(payload, "registered_family_size must equal five")


def build_reconcilable_panel_case():
    payload = valid_payload()
    methods = list(validator.METHODS)
    y = [i % 2 for i in range(100)]
    baseline_metrics = {
        "status": "EXECUTED", "n": 100, "positive_rate": 0.5,
        "accuracy": 0.5, "balanced_accuracy": 0.5, "roc_auc": 0.5, "pr_auc": 0.5,
        "brier": 0.25, "log_loss": 0.6931471805599453,
        "tn": 0, "fp": 50, "fn": 0, "tp": 50,
        "prediction_mean": 0.5, "prediction_std": 0.0, "classification_threshold": 0.5,
    }
    candidate_metrics = {
        "status": "EXECUTED", "n": 100, "positive_rate": 0.5,
        "accuracy": 1.0, "balanced_accuracy": 1.0, "roc_auc": 1.0, "pr_auc": 1.0,
        "brier": 0.0625, "log_loss": 0.2876820724517809,
        "tn": 50, "fp": 0, "fn": 0, "tp": 50,
        "prediction_mean": 0.5, "prediction_std": 0.25, "classification_threshold": 0.5,
    }
    improvement = 0.1875
    raw_p = 1.0 / 501.0
    horizon_map = {}
    panel_rows = []
    date_values = [str(validator.pd.Timestamp("2020-01-01") + validator.pd.Timedelta(days=i))[:10] for i in range(100)]
    for h in validator.HORIZONS:
        cells = {}
        for method in methods:
            cell = dict(candidate_metrics)
            cell.update({
                "horizon_sessions": h,
                "source_ids": [method],
                "feature_columns": ["feature_1"],
                "mean_future_log_return_when_predicted_up": 0.01,
                "paired_baseline_comparison": {
                    "status": "EXECUTED", "n_common": 100,
                    "candidate_brier": 0.0625, "baseline_brier": 0.25,
                    "brier_improvement": improvement,
                    "baseline_metrics": dict(baseline_metrics),
                },
            })
            cells[method] = cell
        baseline_cell = dict(baseline_metrics)
        baseline_cell.update({
            "horizon_sessions": h,
            "description": "causal history-rate baseline",
            "evaluation_scope": "all eligible rows; row-level panel exact",
        })
        cells["_BASELINE"] = baseline_cell
        cells["_FAMILY_TEST"] = {
            "status": "EXECUTED", "n_common": 100, "method_count": len(methods),
            "bootstrap_reps": 500, "block_length": 20, "seed": 42,
            "max_mean_brier_improvement": improvement,
            "candidate_mean_brier_improvements": {m: improvement for m in methods},
            "family_p_value": raw_p,
        }
        horizon_map[str(h)] = cells
        for i, date in enumerate(date_values):
            label = y[i]
            ret = 0.01 if label == 1 else -0.01
            panel_rows.append({
                "date": date, "horizon_sessions": h, "method": "_BASELINE",
                "row_type": "baseline", "cell_status": "EXECUTED",
                "actual_direction": label, "future_log_return": ret,
                "predicted_probability": 0.5, "baseline_probability": 0.5,
                "prediction_available": None, "source_ids_json": "[]", "feature_columns_json": "[]",
            })
        for method in methods:
            for i, date in enumerate(date_values):
                label = y[i]
                ret = 0.01 if label == 1 else -0.01
                prob = 0.75 if label == 1 else 0.25
                panel_rows.append({
                    "date": date, "horizon_sessions": h, "method": method,
                    "row_type": "candidate", "cell_status": "EXECUTED",
                    "actual_direction": label, "future_log_return": ret,
                    "predicted_probability": prob, "baseline_probability": 0.5,
                    "prediction_available": True, "source_ids_json": __import__("json").dumps([method]),
                    "feature_columns_json": '["feature_1"]',
                })
    payload["daily"]["horizons"] = horizon_map
    payload["family_inference"] = {
        "status": "EXECUTED",
        "family_tests": len(validator.HORIZONS),
        "family_tests_executed": len(validator.HORIZONS),
        "registered_family_size": len(validator.HORIZONS),
        "registered_horizons": list(validator.HORIZONS),
        "bonferroni_adjusted_p_values": [
            {"horizon_sessions": h, "raw_p_value": raw_p, "bonferroni_p_value": min(1.0, raw_p * 5)}
            for h in validator.HORIZONS
        ],
        "bootstrap_method": "fixed-seed moving-block bootstrap",
        "interpretation": "synthetic test only",
    }
    return payload, validator.pd.DataFrame(panel_rows)


def check_row_level_panels_reconcile_metrics_and_family_bootstrap() -> None:
    payload, panel = build_reconcilable_panel_case()
    validator.validate_result_payload(payload)
    validator.validate_prediction_panels(payload, panel)


def check_row_level_panel_detects_mutated_probability() -> None:
    payload, panel = build_reconcilable_panel_case()
    idx = panel.index[(panel["horizon_sessions"] == 1) & (panel["method"] == "G01_SENSEX")][0]
    panel.loc[idx, "predicted_probability"] = 0.75
    try:
        validator.validate_prediction_panels(payload, panel)
    except ValueError as exc:
        assert "row-level" in str(exc) or "does not reconcile" in str(exc) or "availability flag" in str(exc)
        return
    raise AssertionError("mutated row-level probability was accepted")


def main() -> None:
    checks = [
        check_complete_payload_passes,
        check_missing_baseline_cell_fails,
        check_bonferroni_uses_fixed_five_horizon_family,
        check_blocked_candidate_requires_reason,
        check_paired_baseline_sample_matches_candidate,
        check_horizon_family_inference_count_reconciles,
        check_row_level_panels_reconcile_metrics_and_family_bootstrap,
        check_row_level_panel_detects_mutated_probability,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print(f"PASS {len(checks)} result-schema regression checks")


if __name__ == "__main__":
    main()
