"""Synthetic-only tests for PM0051 sweep guardrails and statistics plumbing."""
from types import SimpleNamespace
import unittest

from run_pm0051_prediction_sweep_r3 import (
    _expected_config_ids,
    normalize_bootstrap_result,
    precheck_to_terminal_status,
    session_loss_deltas,
    classification_diagnostics,
    session_accuracy_deltas,
    build_daily_regime_context,
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


class PM0051SweepTests(unittest.TestCase):
    def test_only_exactly_40_unique_pm0051_configs_are_accepted(self):
        configs = [{"config_id": f"CFG{i:04d}", "method_id": "PM0051"} for i in range(40)]
        self.assertEqual(len(_expected_config_ids(configs)), 40)
        with self.assertRaisesRegex(ValueError, "EXPECTED_40_UNIQUE_PM0051_CONFIGS"):
            _expected_config_ids(configs[:-1])
        with self.assertRaisesRegex(ValueError, "NON_PM0051_CONFIG_IN_SWEEP"):
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


    def test_classification_confusion_calibration_and_baseline_metrics(self):
        m=classification_diagnostics([1,0,1,0],[0.9,0.8,0.2,0.1],[0.6,0.4,0.6,0.4])
        self.assertAlmostEqual(m["accuracy"],0.5); self.assertAlmostEqual(m["balanced_accuracy_from_confusion"],0.5)
        self.assertEqual((m["true_positive"],m["false_positive"],m["true_negative"],m["false_negative"]),(1,1,1,1))
        self.assertAlmostEqual(m["baseline_accuracy"],1.0); self.assertEqual(sum(v["count"] for v in m["calibration_bins"]),4)

    def test_paired_session_accuracy_difference(self):
        r=SimpleNamespace(validation_indices=(0,1,2),y_validation=(1,0,1),probabilities=(0.9,0.1,0.4),baseline_probabilities=(0.5,0.5,0.5))
        s=[SimpleNamespace(decision_session_index=0),SimpleNamespace(decision_session_index=0),SimpleNamespace(decision_session_index=1)]
        pos,d,m=session_accuracy_deltas(r,s,["2026-01-01","2026-01-02"])
        self.assertEqual(pos,[0,1]); self.assertAlmostEqual(d[0],0.5); self.assertAlmostEqual(d[1],-1.0)
        self.assertAlmostEqual(m["candidate_session_weighted_accuracy"],0.5); self.assertAlmostEqual(m["baseline_session_weighted_accuracy"],0.75)

    def test_regime_context_never_imputes_missing_close(self):
        from datetime import date,timedelta
        dates=[(date(2026,1,1)+timedelta(days=i)).isoformat() for i in range(30)]; rows=[]; close=20000.0
        for i,day in enumerate(dates):
            close*=1.0+(0.001 if i%3 else -0.0015)
            if i==24: continue
            rows.append({"row_type":"SPOT","session_date":day,"timestamp_ist":day+"T15:29:00+05:30","nifty_close":str(close)})
        ctx=build_daily_regime_context(rows,dates)
        self.assertIsNone(ctx[20]); self.assertIsNotNone(ctx[21]); self.assertIsNone(ctx[25]); self.assertIsNone(ctx[26])

    def test_classification_metrics_include_confusion_and_calibration(self):
        m = classification_diagnostics([1, 0, 1, 0], [0.9, 0.8, 0.2, 0.1], [0.6, 0.4, 0.6, 0.4])
        self.assertAlmostEqual(m["accuracy"], 0.5)
        self.assertAlmostEqual(m["balanced_accuracy_from_confusion"], 0.5)
        self.assertEqual((m["true_positive"], m["false_positive"], m["true_negative"], m["false_negative"]), (1, 1, 1, 1))
        self.assertAlmostEqual(m["baseline_accuracy"], 1.0)
        self.assertEqual(sum(x["count"] for x in m["calibration_bins"]), 4)

    def test_session_accuracy_differences_are_paired(self):
        r = SimpleNamespace(validation_indices=(0, 1, 2), y_validation=(1, 0, 1),
            probabilities=(0.9, 0.1, 0.4), baseline_probabilities=(0.5, 0.5, 0.5))
        samples = [SimpleNamespace(decision_session_index=0), SimpleNamespace(decision_session_index=0),
                   SimpleNamespace(decision_session_index=1)]
        positions, deltas, metrics = session_accuracy_deltas(r, samples, ["2026-01-01", "2026-01-02"])
        self.assertEqual(positions, [0, 1])
        self.assertAlmostEqual(deltas[0], 0.5)
        self.assertAlmostEqual(deltas[1], -1.0)
        self.assertAlmostEqual(metrics["candidate_session_weighted_accuracy"], 0.5)
        self.assertAlmostEqual(metrics["baseline_session_weighted_accuracy"], 0.75)

    def test_daily_regime_context_never_imputes_missing_close(self):
        from datetime import date, timedelta
        dates = [(date(2026, 1, 1) + timedelta(days=i)).isoformat() for i in range(30)]
        rows, close = [], 20000.0
        for i, day in enumerate(dates):
            close *= 1.0 + (0.001 if i % 3 else -0.0015)
            if i == 24:
                continue
            rows.append({"row_type": "SPOT", "session_date": day,
                         "timestamp_ist": day + "T15:29:00+05:30", "nifty_close": str(close)})
        context = build_daily_regime_context(rows, dates)
        self.assertIsNone(context[20])
        self.assertIsNotNone(context[21])
        self.assertIsNone(context[25])
        self.assertIsNone(context[26])

    def test_bootstrap_p_value_field_is_normalized_for_result_schema(self):
        normalized = normalize_bootstrap_result({
            "raw_two_sided_p_value_centered_bootstrap": 0.0123,
            "ci_low": 0.01,
            "ci_high": 0.09,
            "replicates": 10000,
        })
        self.assertAlmostEqual(normalized["raw_p_value"], 0.0123)
        degenerate = normalize_bootstrap_result({
            "raw_two_sided_p_value_centered_bootstrap": None,
            "ci_low": None,
            "ci_high": None,
            "replicates": 10000,
        })
        self.assertIsNone(degenerate["raw_p_value"])

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
