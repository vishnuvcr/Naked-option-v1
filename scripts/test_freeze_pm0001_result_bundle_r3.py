"""Synthetic-only result freeze validation tests; no market data or model fits."""
import unittest

from freeze_pm0001_result_bundle_r3 import (
    EXPECTED_DATA_SHA256,
    FreezeError,
    validate_result_contract,
)


def fixture():
    ids = [f"CFG{i:04d}" for i in range(40)]
    rows = [{
        "config_id": cid,
        "method_id": "PM0001",
        "label_id": f"LABEL_{int(cid[-2:]) % 10}",
        "fold_id": f"F{fold:02d}",
        "terminal_status": "BLOCKED_GATE",
        "failure_reason": "SYNTHETIC_GATE_NOT_AUTHORIZED",
        "baseline_log_loss": None,
        "candidate_log_loss": None,
        "log_loss_improvement": None,
        "brier_score": None,
        "balanced_accuracy": None,
        "roc_auc": None,
        "average_precision": None,
        "lookback_bars": 20,
        "c": 1.0,
    } for cid in ids for fold in range(1, 9)]
    summary = {
        "source_data_sha256": EXPECTED_DATA_SHA256,
        "terminal_rows_written": 320,
        "terminal_status_counts": {"BLOCKED_GATE": 320},
        "results_acquired": False,
    }
    result = {
        "schema_version": "pm0001-result-bundle-r3-v1",
        "source_data_sha256": EXPECTED_DATA_SHA256,
        "configuration_count": 40,
        "outer_fold_count": 8,
        "expected_terminal_rows": 320,
        "terminal_rows_written": 320,
        "holdout_accessed": False,
        "raw_market_rows_emitted": False,
        "results_acquired": False,
        "validation": {"complete_expected_coverage": True},
        "rows": rows,
    }
    return ids, result, summary


class PM0001ResultFreezeTests(unittest.TestCase):
    def test_complete_320_row_grid_with_no_fit_is_recorded_not_misrepresented(self):
        ids, result, summary = fixture()
        contract = validate_result_contract(result, summary, expected_config_ids=ids)
        self.assertEqual(contract["status"], "COMPLETE_TERMINAL_ACCOUNTING_NO_EMPIRICAL_FIT")
        self.assertFalse(contract["results_acquired"])
        self.assertEqual(contract["unique_config_fold_pairs"], 320)
        self.assertEqual(contract["terminal_status_counts"], {"BLOCKED_GATE": 320})

    def test_duplicate_config_fold_pair_fails(self):
        ids, result, summary = fixture()
        result["rows"][8]["config_id"] = result["rows"][0]["config_id"]
        with self.assertRaisesRegex(FreezeError, "DUPLICATE_RESULT_PAIR"):
            validate_result_contract(result, summary, expected_config_ids=ids)

    def test_wrong_source_data_hash_fails(self):
        ids, result, summary = fixture()
        result["source_data_sha256"] = "0" * 64
        with self.assertRaisesRegex(FreezeError, "RESULT_DATASET_SHA256_MISMATCH"):
            validate_result_contract(result, summary, expected_config_ids=ids)

    def test_per_observation_predictions_are_prohibited(self):
        ids, result, summary = fixture()
        result["rows"][0]["probabilities"] = [0.1, 0.9]
        with self.assertRaisesRegex(FreezeError, "PER_OBSERVATION_OR_RAW_FIELDS_FORBIDDEN"):
            validate_result_contract(result, summary, expected_config_ids=ids)

    def test_executed_result_must_have_consistent_loss_improvement(self):
        ids, result, summary = fixture()
        row = result["rows"][0]
        row.update({
            "terminal_status": "EXECUTED_AUDITED",
            "failure_reason": None,
            "baseline_log_loss": 0.70,
            "candidate_log_loss": 0.65,
            "log_loss_improvement": -0.05,
        })
        result["results_acquired"] = True
        summary["results_acquired"] = True
        summary["terminal_status_counts"] = {"BLOCKED_GATE": 319, "EXECUTED_AUDITED": 1}
        with self.assertRaisesRegex(FreezeError, "LOGLOSS_SIGN_OR_ARITHMETIC_MISMATCH"):
            validate_result_contract(result, summary, expected_config_ids=ids)

    def test_terminal_row_count_mismatch_fails(self):
        ids, result, summary = fixture()
        result["rows"].pop()
        with self.assertRaisesRegex(FreezeError, "RESULT_ROWS_MISSING_OR_INCOMPLETE"):
            validate_result_contract(result, summary, expected_config_ids=ids)


if __name__ == "__main__":
    unittest.main()
