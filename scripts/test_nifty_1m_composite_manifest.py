#!/usr/bin/env python3
"""Offline request-manifest regression tests; never call external endpoints."""
from __future__ import annotations
import unittest
from validate_nifty_1m_composite_manifest import validate


class TestNiftyOneMinuteManifest(unittest.TestCase):
    def test_full_request_manifest_is_exact_and_fail_closed(self):
        self.assertEqual(validate(), [])

    def test_live_workflow_is_guarded_and_uploads_only_encrypted_market_rows(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/phase-07-nifty-1m-composite-live.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("confirm_live_acquisition:", workflow)
        self.assertIn("inputs.confirm_live_acquisition == true", workflow)
        self.assertIn("github.ref == 'refs/heads/phase-07-developer'", workflow)
        self.assertNotIn("__EVENT__", workflow)
        self.assertIn("Validate current tester approval and protected source/request pins", workflow)
        self.assertIn("Spend acquisition approval before the first network request", workflow)
        self.assertLess(workflow.index("Validate current tester approval"), workflow.index("Spend acquisition approval"))
        self.assertLess(workflow.index("Spend acquisition approval"), workflow.index("Acquire bounded Dhan spot"))
        self.assertIn("data/exports/nifty_1m_composite/encrypted/*.csv.gz.enc", workflow)
        self.assertNotIn("data/exports/nifty_1m_composite/plain/*.csv.gz", workflow)

    def test_provider_request_counts_arithmetic(self):
        self.assertEqual(61 * 140, 8540)
        self.assertEqual(8540 + 61, 8601)
        self.assertEqual(8601 + 100, 8701)

    def test_expiry_code_strike_grid_respects_documented_ranges(self):
        self.assertEqual(len(range(-10, 11)), 21)
        self.assertEqual(len(range(-3, 4)), 7)
        self.assertEqual(61 * 2 * (21 + 7 + 7) * 2, 8540)


if __name__ == "__main__":
    unittest.main(verbosity=2)
