"""Synthetic-only tests for independent R3 PM0001 result auditing."""
import unittest

from independent_pm0001_results_audit_r3 import independent_by_adjustment, validate_precheck, validate_result_rows


def configs():
    return {
        f"CFG{i:04d}": {
            "config_id": f"CFG{i:04d}",
            "method_id": "PM0001",
            "configuration": {
                "label_id": f"L{i//4:02d}",
                "lookback_bars": 20 + 20*(i % 4),
                "model_parameters": {"C": 1.0},
            },
        }
        for i in range(40)
    }


def precheck_fixture(config_map):
    rows = [{
        "config_id": cid,
        "method_id": "PM0001",
        "label_id": cfg["configuration"]["label_id"],
        "lookback_bars": cfg["configuration"]["lookback_bars"],
        "c": cfg["configuration"]["model_parameters"]["C"],
        "fold_id": f"F{f:02d}",
        "status": "PRECHECK_PASS",
        "empirical_fit_authorized": False,
        "model_fitting_performed": False,
        "holdout_accessed": False,
    } for cid, cfg in config_map.items() for f in range(1, 9)]
    return {
        "schema_version": "pm0001-data-execution-precheck-r3-v1",
        "status": "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING",
        "source_csv_sha256": "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204",
        "configuration_count": 40,
        "outer_fold_count": 8,
        "result_row_count": 320,
        "status_counts": {"PRECHECK_PASS": 320},
        "rows": rows,
        "empirical_fit_authorized": False,
        "model_fitting_performed": False,
        "holdout_accessed": False,
    }


def blocked_rows(config_map):
    return [{
        "config_id": cid,
        "method_id": "PM0001",
        "label_id": cfg["configuration"]["label_id"],
        "fold_id": f"F{f:02d}",
        "terminal_status": "BLOCKED_GATE",
        "failure_reason": "SYNTHETIC_TEST_ONLY",
        **{k: None for k in (
            "baseline_log_loss", "candidate_log_loss", "log_loss_improvement",
            "bootstrap_ci_lower", "bootstrap_ci_upper", "raw_p_value", "by_adjusted_p_value",
            "class_prior_baseline_log_loss", "previous_sign_baseline_log_loss",
            "brier_score", "balanced_accuracy", "roc_auc", "average_precision",
            "calibration_intercept", "calibration_slope",
        )},
    } for cid, cfg in config_map.items() for f in range(1, 9)]


class IndependentPM0001ResultsAuditTests(unittest.TestCase):
    def test_by_adjusted_values_and_rejections_are_recomputed_independently(self):
        values = independent_by_adjustment({"A": 0.001, "B": 0.02, "C": 0.8}, q=0.05)
        self.assertEqual(set(values), {"A", "B", "C"})
        for value in values.values():
            self.assertGreaterEqual(value["by_adjusted_p_value"], value["raw_p_value"])
            self.assertLessEqual(value["by_adjusted_p_value"], 1.0)
        self.assertFalse(values["C"]["reject_at_q"])

    def test_complete_320_cell_precheck_passes_and_counts_are_recomputed(self):
        cmap = configs()
        precheck = precheck_fixture(cmap)
        issues = []
        counts = validate_precheck(precheck, cmap, issues)
        self.assertEqual(counts, {"PRECHECK_PASS": 320})
        self.assertEqual(issues, [])

    def test_precheck_label_mismatch_is_detected(self):
        cmap = configs()
        precheck = precheck_fixture(cmap)
        precheck["rows"][0]["label_id"] = "WRONG_LABEL"
        issues = []
        validate_precheck(precheck, cmap, issues)
        self.assertIn("PRECHECK_LABEL_MISMATCH", {x["code"] for x in issues})

    def test_complete_terminal_result_grid_with_blocked_rows_passes(self):
        cmap = configs()
        result = {"rows": blocked_rows(cmap)}
        issues = []
        counts = validate_result_rows(result, cmap, issues)
        self.assertEqual(counts, {"BLOCKED_GATE": 320})
        self.assertEqual(issues, [])

    def test_duplicate_pair_and_loss_sign_error_are_detected(self):
        cmap = configs()
        rows = blocked_rows(cmap)
        rows[8]["config_id"] = rows[0]["config_id"]
        rows[0].update({
            "terminal_status": "EXECUTED_AUDITED",
            "failure_reason": None,
            "baseline_log_loss": 0.7,
            "candidate_log_loss": 0.6,
            "log_loss_improvement": -0.1,
            "brier_score": 0.2,
            "balanced_accuracy": 0.6,
            "roc_auc": 0.7,
            "average_precision": 0.7,
            "observed_session_count": 120,
        })
        issues = []
        validate_result_rows({"rows": rows}, cmap, issues)
        codes = {x["code"] for x in issues}
        self.assertIn("RESULT_DUPLICATE_PAIR", codes)
        self.assertIn("LOGLOSS_SIGN_OR_ARITHMETIC_ERROR", codes)

    def test_nonfinite_and_out_of_range_metrics_are_detected(self):
        cmap = configs()
        rows = blocked_rows(cmap)
        rows[0].update({
            "terminal_status": "EXECUTED_AUDITED",
            "failure_reason": None,
            "baseline_log_loss": 0.7,
            "candidate_log_loss": 0.6,
            "log_loss_improvement": 0.1,
            "brier_score": 1.2,
            "balanced_accuracy": 0.6,
            "roc_auc": float("nan"),
            "average_precision": 0.6,
            "observed_session_count": 120,
        })
        issues = []
        validate_result_rows({"rows": rows}, cmap, issues)
        codes = {x["code"] for x in issues}
        self.assertIn("BOUNDED_METRIC_INVALID", codes)
        self.assertIn("BOUNDED_METRIC_INVALID", codes)

    def test_raw_prediction_fields_are_rejected(self):
        cmap = configs()
        rows = blocked_rows(cmap)
        rows[0]["probabilities"] = [0.1, 0.9]
        issues = []
        validate_result_rows({"rows": rows}, cmap, issues)
        self.assertIn("RAW_OR_PER_OBSERVATION_FIELDS_PERSISTED", {x["code"] for x in issues})


if __name__ == "__main__":
    unittest.main()
