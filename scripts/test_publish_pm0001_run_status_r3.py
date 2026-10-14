"""Unit tests for always-run PM0001 status/error publication."""
import json
import tempfile
import unittest
from pathlib import Path

from publish_pm0001_run_status_r3 import publish_status


class PM0001RunPublisherTests(unittest.TestCase):
    def make_root(self, tmp):
        root=Path(tmp)
        (root/"research/results").mkdir(parents=True)
        (root/"research/gates").mkdir(parents=True)
        (root/"research/logs").mkdir(parents=True)
        (root/"README.md").write_text("# README\n",encoding="utf-8")
        (root/"research/STATUS.md").write_text("# Status\n",encoding="utf-8")
        (root/"research/logs/RESEARCH_LOG.md").write_text("# Research log\n",encoding="utf-8")
        (root/"research/logs/CHAT_LOG.md").write_text("# Chat log\n",encoding="utf-8")
        (root/"research/ERROR_LOG.md").write_text("# Errors\n",encoding="utf-8")
        (root/"research/logs/ERROR_LOG.md").write_text("# Error details\n",encoding="utf-8")
        return root

    def test_successful_acquired_result_updates_status_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(tmp)
            (root/"research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.summary.json").write_text(json.dumps({
                "status":"COMPLETE_EMPIRICAL_RESULTS",
                "results_acquired":True,
                "terminal_status_counts":{"EXECUTED_AUDITED":120,"BLOCKED_DATA":20,"BLOCKED_GATE":180},
                "empirical_fits_performed":120,
                "blocked_or_failed_rows":200,
            }),encoding="utf-8")
            (root/"research/results/PM0001_PREDICTION_RESULT_MANIFEST_R3_2026-10-14.json").write_text("{}",encoding="utf-8")
            (root/"research/gates/PREDICTION_PM0001_DATA_EXECUTION_PRECHECK_R3_2026-10-14.json").write_text(json.dumps({
                "source_csv_sha256":"a"*64,"result_row_count":320,
                "status_counts":{"PRECHECK_PASS":160,"BLOCKED_DATA":20,"BLOCKED_SAMPLE_ELIGIBILITY":140},
            }),encoding="utf-8")
            result=publish_status(root,run_id="123",repository="vishnuvcr/Naked-option-v1",
                                  source_commit="b"*40,job_status="success")
            self.assertTrue(result["results_acquired"])
            for p in ("README.md","research/STATUS.md","research/logs/RESEARCH_LOG.md","research/logs/CHAT_LOG.md"):
                text=(root/p).read_text(encoding="utf-8")
                self.assertIn("pm0001-run:123",text)
                self.assertIn("results acquired: true",text)
            publish_status(root,run_id="123",repository="vishnuvcr/Naked-option-v1",
                           source_commit="b"*40,job_status="success")
            self.assertEqual((root/"README.md").read_text().count("pm0001-run:123"),1)

    def test_failure_writes_error_logs_for_structured_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(tmp)
            (root/"research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.errors.jsonl").write_text(json.dumps({
                "step":"fit_pm0001_outer_fold","config_id":"CFG01","fold_id":"F03",
                "exception_type":"ValueError","exception_message":"SYNTHETIC_TEST_ERROR",
                "traceback_sha256":"c"*64,
            })+"\n",encoding="utf-8")
            result=publish_status(root,run_id="456",repository="vishnuvcr/Naked-option-v1",
                                  source_commit="d"*40,job_status="failure")
            self.assertEqual(result["structured_error_count"],1)
            self.assertIn("SYNTHETIC_TEST_ERROR",(root/"research/ERROR_LOG.md").read_text())
            self.assertIn("run #456",(root/"research/logs/ERROR_LOG.md").read_text())

    def test_unfrozen_partial_result_is_archived_as_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(tmp)
            partial=root/"research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.json"
            partial.write_text(json.dumps({"partial":True,"rows":[]}),encoding="utf-8")
            result=publish_status(root,run_id="789",repository="vishnuvcr/Naked-option-v1",
                                  source_commit="e"*40,job_status="failure")
            self.assertFalse(partial.exists())
            attempts=list((root/"research/gates/attempts").glob("*789_partial.json"))
            self.assertEqual(len(attempts),1)
            self.assertEqual(result["research_status"],"failure")


if __name__=="__main__":
    unittest.main()
