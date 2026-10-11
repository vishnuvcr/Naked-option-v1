import json
import tempfile
import unittest
from pathlib import Path

from validate_real_file_preflight_authorization import blob_sha


class AuthorizationValidationTests(unittest.TestCase):
    def test_valid_exact_snapshot_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.py"
            source.write_text("pass\n", encoding="utf-8")
            decision = root / "decision.json"
            decision.write_text(json.dumps({
                "verdict": "PASS_WITH_SCOPED_RESTRICTIONS",
                "real_file_preflight_execution_authorized": True,
                "reviewed_files": {"source.py": blob_sha(source)},
            }), encoding="utf-8")
            request = root / "request.json"
            request.write_text(json.dumps({
                "requested": True,
                "tester_decision_blob_sha": blob_sha(decision),
            }), encoding="utf-8")
            self.assertEqual(json.loads(decision.read_text())["reviewed_files"]["source.py"], blob_sha(source))
            self.assertEqual(json.loads(request.read_text())["tester_decision_blob_sha"], blob_sha(decision))

    def test_missing_decision_and_request_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertFalse((root / "decision.json").exists())
            self.assertFalse((root / "request.json").exists())

    def test_mutated_reviewed_file_changes_blob_hash(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.py"
            source.write_text("pass\n", encoding="utf-8")
            approved = blob_sha(source)
            source.write_text("fail\n", encoding="utf-8")
            self.assertNotEqual(approved, blob_sha(source))

    def test_decision_hash_changes_when_approval_changes(self):
        with tempfile.TemporaryDirectory() as td:
            decision = Path(td) / "decision.json"
            decision.write_text('{"real_file_preflight_execution_authorized": false}', encoding="utf-8")
            old_hash = blob_sha(decision)
            decision.write_text('{"real_file_preflight_execution_authorized": true}', encoding="utf-8")
            self.assertNotEqual(old_hash, blob_sha(decision))


if __name__ == "__main__":
    unittest.main()
