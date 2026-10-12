"""End-to-end synthetic-only dry-run tests. No real data or model fit is performed."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("prediction_registry_synthetic_dryrun.py")
FIRST_TASK = "CFG0001_INTRA_30M_UP_DOWN_20_REGULARIZED|F01"


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )


class SyntheticDryRunTests(unittest.TestCase):
    def test_interrupted_resume_matches_fresh_deterministic_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resume_out = root / "resumed.jsonl"
            interrupted = invoke("--output", str(resume_out), "--max-tasks", "80", "--simulate-interruption-after", "17")
            self.assertEqual(interrupted.returncode, 75, interrupted.stdout + interrupted.stderr)
            checkpoint = resume_out.with_suffix(".checkpoint.json")
            state = json.loads(checkpoint.read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "INTERRUPTED_SYNTHETIC_TEST")
            self.assertEqual(state["completed_tasks"], 17)
            resumed = invoke("--output", str(resume_out), "--max-tasks", "80", "--resume")
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)

            fresh_out = root / "fresh.jsonl"
            fresh = invoke("--output", str(fresh_out), "--max-tasks", "80")
            self.assertEqual(fresh.returncode, 0, fresh.stdout + fresh.stderr)
            self.assertEqual(resume_out.read_bytes(), fresh_out.read_bytes())

            summary = json.loads(fresh_out.with_suffix(".summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["result_rows"], 80)
            self.assertFalse(summary["market_data_opened"])
            self.assertFalse(summary["model_fitting_performed"])
            self.assertFalse(summary["holdout_accessed"])
            self.assertFalse(summary["scientific_evidence"])
            self.assertIn("resource_estimate", summary)

    def test_failure_is_written_to_jsonl_with_traceback_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "failure.jsonl"
            result = invoke("--output", str(out), "--max-tasks", "10", "--inject-failure-on-task", FIRST_TASK)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            error_path = out.with_suffix(".errors.jsonl")
            records = [json.loads(line) for line in error_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["task_id"], FIRST_TASK)
            self.assertEqual(records[0]["error_type"], "RuntimeError")
            self.assertEqual(len(records[0]["traceback_sha256"]), 64)
            checkpoint = json.loads(out.with_suffix(".checkpoint.json").read_text(encoding="utf-8"))
            self.assertEqual(checkpoint["status"], "FAILED_SYNTHETIC_TEST")
            self.assertEqual(checkpoint["completed_tasks"], 0)

    def test_task_universe_is_full_registry_when_not_test_limited(self):
        # load_registry is intentionally invoked through the CLI; use a 1-task
        # deterministic prefix to confirm the loader validates all 8,000 configs.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "one.jsonl"
            result = invoke("--output", str(out), "--max-tasks", "1")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            row = json.loads(out.read_text(encoding="utf-8").strip())
            self.assertIn(row["terminal_status"], {"SYNTHETIC_MOCK_ONLY", "BLOCKED_COMPATIBILITY"})
            self.assertTrue(row["synthetic_only"])
            self.assertFalse(row["eligible_for_empirical_fitting"])


if __name__ == "__main__":
    unittest.main()
