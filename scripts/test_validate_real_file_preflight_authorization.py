import json
import tempfile
import unittest
from pathlib import Path

from validate_real_file_preflight_authorization import blob_sha, evaluate


class AuthorizationValidationTests(unittest.TestCase):
    def setup_case(self, root):
        source = root / "source.py"
        source.write_text("pass\n", encoding="utf-8")
        decision = root / "decision.json"
        decision.write_text("{}", encoding="utf-8")
        request = {"requested": True, "tester_decision_blob_sha": blob_sha(decision)}
        approval = {
            "verdict": "PASS_WITH_SCOPED_RESTRICTIONS",
            "real_file_preflight_execution_authorized": True,
            "reviewed_files": {"source.py": blob_sha(source)},
        }
        decision.write_text(json.dumps(approval), encoding="utf-8")
        request["tester_decision_blob_sha"] = blob_sha(decision)
        return source, decision, request, approval

    def test_exact_matching_approval_authorizes(self):
        with tempfile.TemporaryDirectory() as td:
            source, decision_path, request, approval = self.setup_case(Path(td))
            result = evaluate(approval, request, decision_path, ["source.py"])
            self.assertTrue(result["authorized"], result)

    def test_missing_real_file_permission_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            source, decision_path, request, approval = self.setup_case(Path(td))
            approval["real_file_preflight_execution_authorized"] = False
            decision_path.write_text(json.dumps(approval), encoding="utf-8")
            request["tester_decision_blob_sha"] = blob_sha(decision_path)
            self.assertFalse(evaluate(approval, request, decision_path, ["source.py"])["authorized"])

    def test_stale_file_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            source, decision_path, request, approval = self.setup_case(Path(td))
            source.write_text("changed\n", encoding="utf-8")
            result = evaluate(approval, request, decision_path, ["source.py"])
            self.assertFalse(result["authorized"])
            self.assertIn("REVIEWED_FILE_HASH_MISMATCH:source.py", result["failures"])

    def test_changed_decision_blob_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            source, decision_path, request, approval = self.setup_case(Path(td))
            request["tester_decision_blob_sha"] = "0" * 40
            self.assertFalse(evaluate(approval, request, decision_path, ["source.py"])["authorized"])

    def test_unapproved_verdict_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            source, decision_path, request, approval = self.setup_case(Path(td))
            approval["verdict"] = "REQUEST_CHANGES"
            decision_path.write_text(json.dumps(approval), encoding="utf-8")
            request["tester_decision_blob_sha"] = blob_sha(decision_path)
            self.assertFalse(evaluate(approval, request, decision_path, ["source.py"])["authorized"])

    def test_missing_reviewed_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            source, decision_path, request, approval = self.setup_case(Path(td))
            result = evaluate(approval, request, decision_path, ["missing.py"])
            self.assertFalse(result["authorized"])
            self.assertIn("REQUIRED_FILE_MISSING:missing.py", result["failures"])


if __name__ == "__main__":
    unittest.main()
