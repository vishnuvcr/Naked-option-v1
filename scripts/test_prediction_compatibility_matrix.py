"""Unit tests for conservative compatibility decisions (no model fitting)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_prediction_compatibility_matrix as matrix


def sample(family: str, rep: str, operator: str) -> dict[str, str]:
    return {
        "method_id": "PM0001",
        "algorithm_family": family,
        "input_representation": rep,
        "inference_operator": operator,
        "inference_definition": "synthetic-test-only",
    }


class CompatibilityMatrixTests(unittest.TestCase):
    def test_family_contracts_cover_the_full_20_family_universe(self):
        self.assertEqual(len(matrix.FAMILY_CONTRACTS), 20)
        self.assertNotIn("survival_first_passage", matrix.PROBABILITY_FAMILIES)

    def test_probability_threshold_is_conditional_for_standard_classifier(self):
        decision, code, rationale, tests = matrix.classify(
            sample("logistic_regression", "raw_lag_stack", "probability_threshold")
        )
        self.assertEqual(decision, "ALLOW_IN_PRINCIPLE")
        self.assertEqual(code, "CONDITIONAL_DIRECTIONAL_PROBABILITY")
        self.assertIn("FAMILY_PROBABILITY_ADAPTER_TEST", tests)

    def test_all_survival_rows_blocked(self):
        for operator in matrix.OPERATOR_CONTRACTS:
            decision, code, _, _ = matrix.classify(
                sample("survival_first_passage", "entropy_regime_state", operator)
            )
            self.assertEqual(decision, "BLOCK", operator)
            self.assertEqual(code, "BLOCKED_SURVIVAL_ESTIMAND", operator)

    def test_cost_sensitive_and_conformal_are_blocked(self):
        for operator, prefix in [
            ("cost_sensitive_threshold", "BLOCKED_UNFROZEN_COST_MATRIX"),
            ("conformal_set_decision", "BLOCKED_TEMPORAL_CONFORMAL"),
        ]:
            decision, code, _, _ = matrix.classify(
                sample("logistic_regression", "raw_lag_stack", operator)
            )
            self.assertEqual(decision, "BLOCK")
            self.assertEqual(code, prefix)

    def test_regime_gate_requires_causal_gate_source(self):
        blocked, code, _, _ = matrix.classify(
            sample("logistic_regression", "raw_lag_stack", "regime_gated_decision")
        )
        allowed, allowed_code, _, _ = matrix.classify(
            sample("logistic_regression", "entropy_regime_state", "regime_gated_decision")
        )
        self.assertEqual((blocked, code), ("BLOCK", "BLOCKED_NO_CAUSAL_GATE_SOURCE"))
        self.assertEqual((allowed, allowed_code), ("ALLOW_IN_PRINCIPLE", "CONDITIONAL_CAUSAL_REGIME_FEATURE"))

    def test_uncertainty_abstention_freezes_coverage_rule(self):
        decision, code, rationale, tests = matrix.classify(
            sample("random_forest", "raw_lag_stack", "uncertainty_abstention")
        )
        self.assertEqual(decision, "ALLOW_IN_PRINCIPLE")
        self.assertEqual(code, "CONDITIONAL_PREDICTIVE_ENTROPY")
        self.assertIn("80%", rationale)
        self.assertIn("COVERAGE_AND_SELECTIVE_LOSS_TEST", tests)

    def test_unknown_operator_must_not_be_silently_allowed(self):
        with self.assertRaises(SystemExit):
            matrix.classify(sample("logistic_regression", "raw_lag_stack", "invented_operator"))


if __name__ == "__main__":
    unittest.main()
