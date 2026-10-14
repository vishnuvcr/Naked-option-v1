"""Synthetic-only tests for the run-scoped PM0001 execution gate."""
import unittest

from create_pm0001_execution_gate_r3 import EXPECTED_DATA_SHA256, build_execution_gate, validate_precheck


FOLDS = [f"F{i:02d}" for i in range(1, 9)]


def fixture():
    implementation = {
        "method_id": "PM0001",
        "status": "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY",
        "empirical_fit_authorized": False,
    }
    ids = [f"CFG{i:04d}" for i in range(40)]
    pending = [{
        "config_id": cfg,
        "method_id": "PM0001",
        "disposition": "ELIGIBLE_PENDING_EXECUTOR_GATE",
        "empirical_fit_authorized": False,
        "manual_authorization_required": False,
    } for cfg in ids]
    blocked = [{
        "config_id": f"OTHER{i:05d}",
        "method_id": "PM0002",
        "disposition": "BLOCKED_METHOD_COMPATIBILITY",
        "empirical_fit_authorized": False,
        "manual_authorization_required": False,
    } for i in range(39960)]
    eligibility = {
        "record_count": 40000, "unique_config_count": 40000,
        "manual_authorization_required": False, "empirical_fit_authorized": False,
        "implementation_gate_status": "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY",
        "source_pins": {
            "implementation_gate_git_blob_sha1": "implsha",
            "canonical_uncompressed_csv_sha256": EXPECTED_DATA_SHA256,
        },
        "records": blocked + pending,
    }
    preflight = {
        "canonical_hash_matches": True,
        "canonical_uncompressed_csv_sha256": EXPECTED_DATA_SHA256,
        "status": "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS", "blockers": [],
        "holdout_accessed": False, "model_fitting_performed": False,
        "eligible_fold_label_cells": 75, "blocked_fold_label_cells": 5,
    }
    rows = [{
        "config_id": cfg, "method_id": "PM0001", "fold_id": fold,
        "status": "PRECHECK_PASS", "empirical_fit_authorized": False,
        "model_fitting_performed": False, "holdout_accessed": False,
    } for cfg in ids for fold in FOLDS]
    precheck = {
        "schema_version": "pm0001-data-execution-precheck-r3-v1",
        "status": "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING",
        "source_csv_sha256": EXPECTED_DATA_SHA256,
        "configuration_count": 40, "outer_fold_count": 8, "result_row_count": 320,
        "status_counts": {"PRECHECK_PASS": 320}, "rows": rows,
        "model_fitting_performed": False, "holdout_accessed": False,
        "empirical_fit_authorized": False,
    }
    feature_report = {
        "status": "PASS_FEATURE_CONTRACT_WITH_FITTING_BLOCKED",
        "fitting_gate": {
            "empirical_fit_authorized": False,
            "model_fitting_performed": False,
            "holdout_accessed": False,
        },
        "verified_source_hashes": {
            "feature_builder_git_blob_sha1": "feature-builder",
            "feature_tests_git_blob_sha1": "feature-tests",
            "feature_correction_git_blob_sha1": "feature-correction",
            "feature_correction_sha256": "c" * 64,
            "contract_validator_git_blob_sha1": "validator",
        },
    }
    args = {
        "feature_report": feature_report,
        "feature_report_blob_sha1": "feature-report-blob",
        "feature_report_sha256": "d" * 64,
        "eligibility_blob_sha1": "el",
        "preflight_blob_sha1": "pre",
        "implementation_gate_blob_sha1": "implsha",
        "prereg_blob_sha1": "pr",
        "precheck_blob_sha1": "precheckblob",
        "precheck_sha256": "a" * 64,
        "runner_blob_sha1": "runner",
        "source_commit": "b" * 40,
        "workflow_run_id": "123",
    }
    return eligibility, preflight, implementation, precheck, args


class PM0001ExecutionGateTests(unittest.TestCase):
    def test_gate_requires_complete_320_cell_grid_and_authorizes_only_40_pm0001_configs(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        gate = build_execution_gate(eligibility, preflight, implementation, precheck, **args)
        self.assertEqual(gate["status"], "PASS_PM0001_EXECUTION_PRECHECK")
        self.assertEqual(gate["configuration_count"], 40)
        self.assertEqual(len(gate["config_ids"]), 40)
        self.assertEqual(gate["expected_result_rows"], 320)
        self.assertEqual(gate["precheck_status_counts"], {"PRECHECK_PASS": 320})
        self.assertTrue(gate["empirical_fit_authorized"])
        self.assertFalse(gate["manual_authorization_required"])
        self.assertFalse(gate["holdout_accessed"])
        self.assertEqual(gate["precheck_report_sha256"], "a" * 64)

    def test_wrong_dataset_hash_fails_closed(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        preflight["canonical_uncompressed_csv_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "DATA_PREFLIGHT_DATASET_HASH_MISMATCH"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)

    def test_missing_configuration_fold_cell_fails_closed(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        precheck["rows"].pop()
        precheck["result_row_count"] = 319
        with self.assertRaisesRegex(ValueError, "PM0001_DATA_PRECHECK_COUNT_OR_FIT_SCOPE_INVALID"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)

    def test_failed_precheck_cannot_authorize_any_empirical_fit(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        precheck["rows"][0]["status"] = "FAILED_PRECHECK"
        precheck["status"] = "FAIL_PRECHECK_COMPLETE_WITH_FAILURES"
        with self.assertRaisesRegex(ValueError, "PM0001_DATA_PRECHECK_NOT_COMPLETE_PASS"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)

    def test_wrong_method_and_holdout_access_are_rejected(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        precheck["rows"][0]["method_id"] = "PM0002"
        with self.assertRaisesRegex(ValueError, "PM0001_DATA_PRECHECK_METHOD_MISMATCH"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)
        eligibility, preflight, implementation, precheck, args = fixture()
        precheck["rows"][0]["holdout_accessed"] = True
        with self.assertRaisesRegex(ValueError, "PM0001_DATA_PRECHECK_ROW_HOLDOUT_SCOPE_INVALID"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)

    def test_scoped_data_blocks_are_allowed_but_never_authorized_for_fitting(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        precheck["rows"][0]["status"] = "BLOCKED_DATA"
        precheck["status_counts"] = {"PRECHECK_PASS": 319, "BLOCKED_DATA": 1}
        gate = build_execution_gate(eligibility, preflight, implementation, precheck, **args)
        self.assertTrue(gate["empirical_fit_authorized"])
        self.assertEqual(gate["precheck_status_counts"]["BLOCKED_DATA"], 1)
        self.assertFalse(precheck["rows"][0]["empirical_fit_authorized"])

    def test_feature_report_must_pass_and_must_not_claim_fitting(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        args["feature_report"]["status"] = "FAIL_FEATURE_CONTRACT"
        with self.assertRaisesRegex(ValueError, "FEATURE_CONSTRUCTION_REPORT_NOT_PASS"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)
        eligibility, preflight, implementation, precheck, args = fixture()
        args["feature_report"]["fitting_gate"]["model_fitting_performed"] = True
        with self.assertRaisesRegex(ValueError, "FEATURE_CONSTRUCTION_REPORT_SCOPE_INVALID"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)

    def test_wrong_pending_method_or_count_fails_closed(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        eligibility["records"][39960]["method_id"] = "PM0002"
        with self.assertRaisesRegex(ValueError, "EXPECTED_EXACTLY_40_PM0001"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)

    def test_precheck_pair_uniqueness_and_exact_expected_universe(self):
        eligibility, preflight, implementation, precheck, args = fixture()
        precheck["rows"][8]["config_id"] = precheck["rows"][0]["config_id"]
        with self.assertRaisesRegex(ValueError, "PM0001_DATA_PRECHECK_DUPLICATE_PAIR"):
            build_execution_gate(eligibility, preflight, implementation, precheck, **args)


if __name__ == "__main__":
    unittest.main()
