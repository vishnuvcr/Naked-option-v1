import unittest
from pathlib import Path

from check_workflow_action_pinning import APPROVED_ACTIONS, inspect_workflow


class WorkflowActionPinningTests(unittest.TestCase):
    def test_current_workflow_complies_with_allowlist(self):
        workflow = Path(".github/workflows/phase-07-offline-preflight-tests.yml")
        self.assertEqual(inspect_workflow(workflow.read_text(encoding="utf-8")), [])

    def test_mutable_tag_is_rejected(self):
        sha = APPROVED_ACTIONS["actions/checkout"]["sha"]
        text = f"""name: Test
workflow_dispatch:
permissions:
  contents: read
jobs:
  test:
    steps:
      - uses: actions/checkout@v7 # {sha}
"""
        errors = inspect_workflow(text)
        self.assertTrue(any("full 40-character lowercase commit SHA" in item for item in errors))

    def test_unapproved_action_is_rejected_even_with_full_sha(self):
        text = """name: Test
workflow_dispatch:
permissions:
  contents: read
jobs:
  test:
    steps:
      - uses: attacker/unknown@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v1.0.0
"""
        self.assertTrue(any("unapproved external action" in item for item in inspect_workflow(text)))

    def test_wrong_approved_sha_is_rejected(self):
        text = """name: Test
workflow_dispatch:
permissions:
  contents: read
jobs:
  test:
    steps:
      - uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v7.0.1
"""
        self.assertTrue(any("does not match the reviewed allowlist" in item for item in inspect_workflow(text)))

    def test_missing_manual_trigger_or_minimal_permissions_is_rejected(self):
        text = """name: Test
jobs:
  test:
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
"""
        errors = inspect_workflow(text)
        self.assertTrue(any("workflow_dispatch" in item for item in errors))
        self.assertTrue(any("contents: read" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
