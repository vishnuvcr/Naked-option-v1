#!/usr/bin/env python3
"""Offline tests for the bounded one-week Dhan spot patch authorization."""
from __future__ import annotations

import copy
import datetime as dt
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import validate_nifty_1m_spot_failed_window_patch as validator

PROPOSAL_PATH = pathlib.Path(__file__).resolve().parents[1] / "research/gates/NIFTY_1M_SPOT_FAILED_WINDOW_PATCH_PROPOSAL.json"


class TestFailedWindowPatchProposal(unittest.TestCase):
    def setUp(self):
        self.proposal = validator.load_json(PROPOSAL_PATH)

    def test_exact_seven_shards_cover_only_failed_window(self):
        self.assertEqual(validator.validate_proposal(self.proposal), [])
        requests = self.proposal["requests"]
        self.assertEqual(len(requests), 7)
        self.assertEqual(requests[0]["window_start_inclusive"], "2021-11-08")
        self.assertEqual(requests[-1]["window_end_exclusive"], "2021-11-15")
        self.assertTrue(all(r["max_rows"] == 500 and r["max_response_bytes"] == 4_194_304 and r["max_attempts"] == 1 for r in requests))
        self.assertTrue(all((dt.date.fromisoformat(r["window_end_exclusive"]) - dt.date.fromisoformat(r["window_start_inclusive"])).days == 1 for r in requests))
        self.assertFalse(self.proposal["live_requests_authorized"])
        self.assertFalse(self.proposal["live_option_requests_allowed"])

    def test_rejects_wrong_base_artifact(self):
        bad = copy.deepcopy(self.proposal)
        bad["base_partial_artifact"]["artifact_sha256"] = "0" * 64
        self.assertIn("base_artifact_hash_mismatch", validator.validate_proposal(bad))

    def test_rejects_row_cap_increase(self):
        bad = copy.deepcopy(self.proposal)
        bad["requests"][0]["max_rows"] = 4000
        self.assertIn("request_0_caps_invalid", validator.validate_proposal(bad))

    def test_rejects_window_expansion_or_gap(self):
        bad = copy.deepcopy(self.proposal)
        bad["requests"][1]["window_start_inclusive"] = "2021-11-10"
        self.assertIn("request_1_not_contiguous_single_day", validator.validate_proposal(bad))

    def test_stale_developer_sha_cannot_authorize(self):
        sha = "a" * 40
        workflow_sha = "b" * 40
        decision = {
            "reviewed_developer_commit": "c" * 40,
            "patch_proposal_blob_sha": sha,
            "reviewed_workflow_blob_sha": workflow_sha,
            "decision": "PASS_WITH_SCOPED_RESTRICTIONS",
            "decision_scope": "FAILED_WINDOW_PATCH_EXECUTION",
            "spot_failed_window_patch_authorized": True,
            "live_requests_authorized": True,
            "patch_request_limit": 7,
            "patch_retry_limit": 0,
            "live_option_requests_allowed": False,
            "model_fitting_authorized": False,
            "holdout_access_authorized": False,
            "strategy_testing_authorized": False,
        }
        errors = validator.validate_authorization(self.proposal, sha, "d" * 40, workflow_sha, decision)
        self.assertIn("tester_developer_sha_mismatch", errors)

    def test_runner_reads_existing_spot_count_from_pinned_artifact_manifest(self):
        runner_path = pathlib.Path(__file__).resolve().parent / "run_nifty_1m_spot_failed_window_patch.py"
        source = runner_path.read_text(encoding="utf-8")
        self.assertIn('base_spot_rows = int(base["existing_spot_rows"])', source)
        self.assertNotIn('proposal["expected_existing_spot_rows"]', source)
        self.assertEqual(self.proposal["base_partial_artifact"]["existing_spot_rows"], 506_898)

    def test_scope_does_not_authorize_models_or_options(self):
        sha, dev, wf = "a" * 40, "b" * 40, "c" * 40
        decision = {
            "reviewed_developer_commit": dev,
            "patch_proposal_blob_sha": sha,
            "reviewed_workflow_blob_sha": wf,
            "decision": "PASS_WITH_SCOPED_RESTRICTIONS",
            "decision_scope": "FAILED_WINDOW_PATCH_EXECUTION",
            "spot_failed_window_patch_authorized": True,
            "live_requests_authorized": True,
            "patch_request_limit": 7,
            "patch_retry_limit": 0,
            "live_option_requests_allowed": True,
            "model_fitting_authorized": True,
            "holdout_access_authorized": False,
            "strategy_testing_authorized": False,
        }
        errors = validator.validate_authorization(self.proposal, sha, dev, wf, decision)
        self.assertIn("option_requests_must_remain_false", errors)
        self.assertIn("model_fitting_authorized_must_remain_false", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
