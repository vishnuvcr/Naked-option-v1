"""Synthetic contract tests for run-scoped PM0001 precheck provenance."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from run_pm0001_data_execution_precheck_r3a import (
    ROOT, run_precheck_r3a,
    implementation,
)


class PM0001PrecheckR3ATests(unittest.TestCase):
    def test_run_preflight_is_selected_and_report_is_pinned_to_exact_execution(self):
        token = "synthetic-r3a-precheck-test"
        preflight = ROOT / "research/gates" / f".{token}-preflight.json"
        output = ROOT / "research/gates" / f".{token}-output.json"
        old_path = implementation.DATA_PREFLIGHT
        preflight_doc = {
            "status": "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS",
            "canonical_hash_matches": True,
            "canonical_uncompressed_csv_sha256": implementation.DATA_SHA256,
            "holdout_accessed": False,
            "model_fitting_performed": False,
        }
        preflight.write_text(json.dumps(preflight_doc), encoding="utf-8")
        try:
            with patch.object(implementation, "run_precheck", return_value={
                "schema_version": "pm0001-data-execution-precheck-r3-v1",
                "status": "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING",
                "source_csv_sha256": implementation.DATA_SHA256,
                "configuration_count": 40,
                "outer_fold_count": 8,
                "result_row_count": 320,
                "status_counts": {"PRECHECK_PASS": 320},
                "rows": [],
                "feature_batch_diagnostics": {},
                "model_fitting_performed": False,
                "holdout_accessed": False,
                "empirical_fit_authorized": False,
            }) as mocked:
                report = run_precheck_r3a(
                    Path("synthetic-unused.gz"),
                    preflight,
                    output,
                    source_commit="a" * 40,
                    workflow_run_id="123456",
                )
                mocked.assert_called_once_with(Path("synthetic-unused.gz"), output)
                self.assertEqual(implementation.DATA_PREFLIGHT, preflight)
            self.assertEqual(report["source_commit"], "a" * 40)
            self.assertEqual(report["workflow_run_id"], "123456")
            self.assertEqual(report["preflight_report_path"], preflight.relative_to(ROOT).as_posix())
            self.assertEqual(report["preflight_report_sha256"], __import__("hashlib").sha256(preflight.read_bytes()).hexdigest())
            self.assertFalse(report["model_fitting_performed"])
            self.assertFalse(report["holdout_accessed"])
            self.assertEqual(json.loads(output.read_text())["precheck_runner_git_blob_sha1"], report["precheck_runner_git_blob_sha1"])
        finally:
            implementation.DATA_PREFLIGHT = old_path
            preflight.unlink(missing_ok=True)
            output.unlink(missing_ok=True)

    def test_preflight_hash_or_scope_failure_blocks_before_data_precheck(self):
        token = "synthetic-r3a-precheck-negative"
        preflight = ROOT / "research/gates" / f".{token}-preflight.json"
        output = ROOT / "research/gates" / f".{token}-output.json"
        preflight.write_text(json.dumps({
            "canonical_hash_matches": False,
            "canonical_uncompressed_csv_sha256": "0" * 64,
            "holdout_accessed": False,
            "model_fitting_performed": False,
        }), encoding="utf-8")
        try:
            with patch.object(implementation, "run_precheck") as mocked:
                with self.assertRaisesRegex(implementation.PrecheckError, "RUN_PREFLIGHT_CANONICAL_HASH_NOT_VERIFIED"):
                    run_precheck_r3a(
                        Path("synthetic-unused.gz"), preflight, output,
                        source_commit="a" * 40, workflow_run_id="123456",
                    )
                mocked.assert_not_called()
        finally:
            preflight.unlink(missing_ok=True)
            output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
