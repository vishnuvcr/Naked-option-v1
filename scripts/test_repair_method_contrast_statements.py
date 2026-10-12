import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import repair_method_contrast_statements as repair

FIELDS = ("algorithm_family", "architecture_or_decision_function", "learning_objective", "input_representation", "feature_construction", "inference_operator", "inference_definition", "target_family", "probability_adapter", "survival_mapping", "causal_information_policy")
BASE = dict(zip(FIELDS, ["logistic_regression", "linear_logit", "log_loss", "raw_lag_stack", "lagged_returns", "probability_threshold", "threshold_0_5", "directional_probability", "inner_fold_calibration", "not_applicable", "past_only"]))

def row(mid, **changes):
    value = dict(BASE)
    value.update(changes)
    value["method_id"] = mid
    value["nearest_neighbor_contrast"] = "generic inaccurate text"
    return value

class ContrastTests(unittest.TestCase):
    def test_contrast_is_field_exact(self):
        a = row("PM0001")
        b = row("PM0002", inference_operator="cost_sensitive_threshold")
        c = row("PM0003", input_representation="cross_asset_lead_lag")
        self.assertEqual(repair.repair_records([a, b, c]), 3)
        self.assertEqual(a["nearest_neighbor_method_id"], "PM0002")
        self.assertIn("differs in inference_operator", a["nearest_neighbor_contrast"])
        self.assertIn("'probability_threshold' vs 'cost_sensitive_threshold'", a["nearest_neighbor_contrast"])
        self.assertNotIn("input_representation", a["nearest_neighbor_contrast"].split("(")[0])

    def test_identical_semantic_rows_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Semantically duplicate"):
            repair.repair_records([row("PM0001"), row("PM0002")])

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique non-empty"):
            repair.repair_records([row("PM0001"), row("PM0001")])

if __name__ == "__main__":
    unittest.main()
