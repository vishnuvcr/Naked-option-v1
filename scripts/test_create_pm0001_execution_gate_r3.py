"""Synthetic-only tests for the PM0001 execution precheck."""
import unittest

from create_pm0001_execution_gate_r3 import EXPECTED_DATA_SHA256, build_execution_gate


def fixture():
    gate = {
        "method_id": "PM0001",
        "status": "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY",
        "empirical_fit_authorized": False,
    }
    records = [{
        "config_id": f"CFG{i:04d}",
        "method_id": "PM0001",
        "disposition": "ELIGIBLE_PENDING_EXECUTOR_GATE",
        "empirical_fit_authorized": False,
        "manual_authorization_required": False,
    } for i in range(40)]
    eligibility = {
        "record_count": 40000, "unique_config_count": 40000,
        "manual_authorization_required": False, "empirical_fit_authorized": False,
        "implementation_gate_status": "PASS_SYNTHETIC_DEVELOPER_TESTED_ONLY",
        "source_pins": {
            "implementation_gate_git_blob_sha1": "implsha",
            "canonical_uncompressed_csv_sha256": EXPECTED_DATA_SHA256,
        },
        "records": records,
    }
    preflight = {
        "canonical_hash_matches": True,
        "canonical_uncompressed_csv_sha256": EXPECTED_DATA_SHA256,
        "status": "BLOCKED_SAMPLE_ELIGIBILITY", "blockers": [],
        "holdout_accessed": False, "model_fitting_performed": False,
        "eligible_fold_label_cells": 75, "blocked_fold_label_cells": 5,
    }
    return eligibility, preflight, gate


class PM0001ExecutionGateTests(unittest.TestCase):
    def test_gate_authorizes_only_registered_pm0001_scope(self):
        eligibility, preflight, implementation = fixture()
        gate = build_execution_gate(
            eligibility, preflight, implementation,
            eligibility_blob_sha1="el", preflight_blob_sha1="pre",
            implementation_gate_blob_sha1="implsha", prereg_blob_sha1="pr",
            runner_blob_sha1="runner", source_commit="abc", workflow_run_id="1",
        )
        self.assertEqual(gate["status"], "PASS_PM0001_EXECUTION_PRECHECK")
        self.assertEqual(gate["configuration_count"], 40)
        self.assertEqual(len(gate["config_ids"]), 40)
        self.assertTrue(gate["empirical_fit_authorized"])
        self.assertFalse(gate["manual_authorization_required"])
        self.assertFalse(gate["holdout_accessed"])

    def test_wrong_data_hash_fails_closed(self):
        eligibility, preflight, implementation = fixture()
        preflight["canonical_uncompressed_csv_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "DATASET_HASH_MISMATCH"):
            build_execution_gate(
                eligibility, preflight, implementation,
                eligibility_blob_sha1="el", preflight_blob_sha1="pre",
                implementation_gate_blob_sha1="implsha", prereg_blob_sha1="pr",
                runner_blob_sha1="runner", source_commit="abc", workflow_run_id="1",
            )

    def test_blocked_or_extra_method_cannot_enter_pm0001_scope(self):
        eligibility, preflight, implementation = fixture()
        eligibility["records"][0]["method_id"] = "PM0002"
        with self.assertRaisesRegex(ValueError, "EXPECTED_EXACTLY_40_PM0001"):
            build_execution_gate(
                eligibility, preflight, implementation,
                eligibility_blob_sha1="el", preflight_blob_sha1="pre",
                implementation_gate_blob_sha1="implsha", prereg_blob_sha1="pr",
                runner_blob_sha1="runner", source_commit="abc", workflow_run_id="1",
            )


if __name__ == "__main__":
    unittest.main()
