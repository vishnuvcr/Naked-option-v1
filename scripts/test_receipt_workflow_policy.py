import re
import unittest
from pathlib import Path


class ReceiptWorkflowPolicyTests(unittest.TestCase):
    def test_all_external_actions_are_full_sha_pinned(self):
        path = Path(".github/workflows/phase-07-publish-preflight-receipt.yml")
        refs = re.findall(r"(?m)^\s*-\s+uses:\s*([^\s]+)", path.read_text(encoding="utf-8"))
        self.assertTrue(refs)
        for ref in refs:
            self.assertRegex(ref, r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

    def test_permissions_are_minimal_for_receipt_publishing(self):
        text = Path(".github/workflows/phase-07-publish-preflight-receipt.yml").read_text(encoding="utf-8")
        block = text.split("permissions:", 1)[1].split("\nconcurrency:", 1)[0]
        self.assertRegex(block, r"(?m)^\s{2}actions:\s*read\s*$")
        self.assertRegex(block, r"(?m)^\s{2}contents:\s*write\s*$")
        self.assertNotRegex(block, r"(?m)^\s{2}(?:id-token|packages|pull-requests|issues):")

    def test_only_github_token_secret_is_referenced(self):
        text = Path(".github/workflows/phase-07-publish-preflight-receipt.yml").read_text(encoding="utf-8")
        secrets = set(re.findall(r"secrets\.([A-Z_]+)", text))
        self.assertEqual(secrets, {"GITHUB_TOKEN"})

    def test_publisher_writes_only_receipt_json_to_developer_branch(self):
        text = Path(".github/workflows/phase-07-publish-preflight-receipt.yml").read_text(encoding="utf-8")
        self.assertIn("research/data/preflight/REAL_FILE_PREFLIGHT_RECEIPT_RUN_", text)
        self.assertIn("branch=phase-07-developer", text)
        self.assertNotIn("contents:write-all", text)


if __name__ == "__main__":
    unittest.main()
