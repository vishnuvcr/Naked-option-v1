"""Synthetic-only tests for PM0001 sweep guardrails and statistics plumbing."""
from types import SimpleNamespace
import unittest

from run_pm0001_prediction_sweep_r3 import (
    _expected_config_ids,
    precheck_to_terminal_status,
    session_loss_deltas,
)


def fake_result():
    # One synthetic exchange session with two binary predictions; not market data.
    return SimpleNamespace(
        validation_indices=(0, 1),
        y_validation=(1, 0),
        probabilities=(0.8, 0.3),
        baseline_probabilities=(0.6, 0.4),
    )


def fake_samples(positions=(0, 0)):
    return [
        SimpleNamespace(decision_session_index=positions[0]),
        SimpleNamespace(decision_session_index=positions[1]),
    ]


class PM0001SweepTests(unittest.TestCase):
    def test_only_exactly_40_unique_pm0001_configs_are_accepted(self):
        configs = [{"config_id": f"CFG{i:04d}", "method_id": "PM0001"} for i in range(40)]
        self.assertEqual(len(_expected_config_ids(configs)), 40)
        with self.assertRaisesRegex(ValueError, "EXPECTED_40_UNIQUE_PM0001_CONFIGS"):
            _expected_config_ids(configs[:-1])
        with self.assertRaisesRegex(ValueError, "NON_PM0001_CONFIG_IN_SWEEP"):
            _expected_config_ids(configs[:-1] + [{"config_id": "OTHER", "method_id": "PM0002"}])

    def test_precheck_blocks_are_preserved_without_fitting(self):
        status, reason = precheck_to_terminal_status({
            "status": "BLOCKED_SAMPLE_ELIGIBILITY",
            "reason_codes": ["OUTER_TRAIN_ROWS_BELOW_MINIMUM"],
        }, True)
        self.assertEqual(status, "BLOCKED_DATA")
        self.assertIn("OUTER_TRAIN_ROWS_BELOW_MINIMUM", reason)

    def test_missing_or_invalid_gate_never_authorizes_fit(self):
        status, reason = precheck_to_terminal_status({"status": "PRECHECK_PASS"}, False)
        self.assertEqual(status, "BLOCKED_GATE")
        self.assertIn("NO_FITTING_PERFORMED", reason)

    def test_failed_precheck_cell_is_terminal_technical_failure(self):
        status, reason = precheck_to_terminal_status({
            "status": "FAILED_PRECHECK", "reason_codes": ["FeatureBuildError:PIN_MISMATCH"],
        }, False)
        self.assertEqual(status, "FAILED_TECHNICAL")
        self.assertIn("PIN_MISMATCH", reason)

    def test_paired_loss_improvement_sign_and_session_unit(self):
        result = SimpleNamespace(
            validation_indices=(0, 1, 2),
            y_validation=(1, 0, 1),
            probabilities=(0.9, 0.1, 0.4),
            baseline_probabilities=(0.7, 0.3, 0.5),
        )
        samples = [
            SimpleNamespace(decision_session_index=0),
            SimpleNamespace(decision_session_index=0),
            SimpleNamespace(decision_session_index=1),
        ]
        positions, deltas, metrics = session_loss_deltas(result, samples, ["2026-01-01", "2026-01-02"])
        self.assertEqual(positions, [0, 1])
        self.assertEqual(len(deltas), 2)
        self.assertGreater(deltas[0], 0.0)
        self.assertLess(deltas[1], 0.0)
        self.assertAlmostEqual(metrics["baseline_log_loss"] - metrics["candidate_log_loss"],
                               sum(deltas) / len(deltas), places=10)

    def test_session_bootstrap_rejects_gaps_in_exchange_session_sequence(self):
        result = SimpleNamespace(
            validation_indices=(0, 1),
            y_validation=(1, 0),
            probabilities=(0.8, 0.2),
            baseline_probabilities=(0.7, 0.3),
        )
        samples = [
            SimpleNamespace(decision_session_index=1),
            SimpleNamespace(decision_session_index=3),
        ]
        with self.assertRaisesRegex(ValueError, "BOOTSTRAP_SESSION_SEQUENCE_NOT_CONTIGUOUS"):
            session_loss_deltas(result, samples, ["2026-01-01", "2026-01-02", "2026-01-05", "2026-01-06"])

    def test_prediction_and_baseline_vector_length_mismatch_is_rejected(self):
        result = SimpleNamespace(
            validation_indices=(0,),
            y_validation=(1,),
            probabilities=(0.8, 0.7),
            baseline_probabilities=(0.5,),
        )
        with self.assertRaisesRegex(ValueError, "PREDICTION_VECTOR_LENGTH_MISMATCH"):
            session_loss_deltas(result, fake_samples((0, 0)), ["2026-01-01"])


if __name__ == "__main__":
    unittest.main()
