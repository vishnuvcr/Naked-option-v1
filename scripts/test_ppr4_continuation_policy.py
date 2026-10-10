#!/usr/bin/env python3
"""Regression tests for PPR-4 user-directed data continuation policy."""
from __future__ import annotations
import unittest
from validate_ppr4_continuation_policy import validate

class TestPPR4ContinuationPolicy(unittest.TestCase):
    def test_policy_and_user_waiver_are_consistent(self) -> None:
        self.assertEqual(validate(), [])

    def test_source_absence_is_not_global_stop(self) -> None:
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parents[1]
        policy = json.loads((root / "research/phase7/PPR4_USER_DIRECTED_DATA_CONTINUATION_POLICY.json").read_text())
        self.assertFalse(policy["continuation_rules"]["global_research_stop_on_source_unavailability"])
        self.assertEqual(policy["continuation_rules"]["source_failure_scope"], "SOURCE_OR_FEATURE_FAMILY_ONLY")

    def test_one_minute_grid_and_greek_provenance_are_explicit(self) -> None:
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parents[1]
        policy = json.loads((root / "research/phase7/PPR4_USER_DIRECTED_DATA_CONTINUATION_POLICY.json").read_text())
        options = policy["acquisition_budget_contract"]["rolling_options"]
        self.assertEqual(options["interval_minutes"], 1)
        self.assertEqual(len(options["strike_grid_by_expiry_code"]["0"]), 21)
        self.assertEqual(len(options["strike_grid_by_expiry_code"]["1"]), 7)
        self.assertEqual(len(options["strike_grid_by_expiry_code"]["2"]), 7)
        self.assertIn("historical Greeks", options["greeks_policy"])
        self.assertEqual(policy["acquisition_budget_contract"]["base_planned_requests"], 8601)

    def test_dhan_cross_source_reconciliation_is_waived(self) -> None:
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parents[1]
        waiver = json.loads((root / "research/gates/DHAN_SAMPLE_USER_ACCEPTANCE_WAIVER.json").read_text())
        self.assertTrue(waiver["user_directives"]["accept_provider_values_without_external_market_value_cross_check"])
        self.assertFalse(waiver["user_directives"]["require_nse_or_third_party_price_reconciliation"])

    def test_live_request_does_not_self_authorize(self) -> None:
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parents[1]
        policy = json.loads((root / "research/phase7/PPR4_USER_DIRECTED_DATA_CONTINUATION_POLICY.json").read_text())
        self.assertFalse(policy["execution_gate"]["live_data_requests_authorized_by_this_policy_file"])
        self.assertFalse(policy["execution_gate"]["existing_one_use_dhan_approval_reusable"])


    def test_hard_budgets_and_durable_cache_are_defined(self) -> None:
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parents[1]
        policy = json.loads((root / "research/phase7/PPR4_USER_DIRECTED_DATA_CONTINUATION_POLICY.json").read_text())
        budget = policy["acquisition_budget_contract"]
        self.assertEqual(budget["serial_requests_per_second_max"], 2)
        self.assertEqual(budget["daily_dhan_request_budget_max"], 8701)
        self.assertEqual(budget["daily_index"]["request_max"], 40)
        self.assertEqual(budget["intraday_index"]["request_max"], 70)
        self.assertEqual(budget["rolling_options"]["request_max"], 8540)
        self.assertFalse(policy["execution_gate"]["live_data_requests_authorized_by_this_policy_file"])
        cache = policy["cache_contract"]
        self.assertTrue(cache["verify_before_fetch"])
        self.assertIn("GitHub Actions artifacts are temporary diagnostics, not authoritative cache", cache["authoritative_cache_hierarchy"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
