"""Synthetic-only tests of the R3 walk-forward split and result schema contract."""
from __future__ import annotations

import json
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

from prediction_walkforward_r3 import (
    PREREG_PATH,
    WalkForwardContractError,
    build_fold_indices,
    build_inner_fold_descriptors,
    preflight_block_reason,
    sample_support,
    terminal_result_row,
    validate_outer_windows,
    validate_result_rows,
)


def business_sessions(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    out = []
    while len(out) < count:
        if current.weekday() < 5:
            out.append(current.isoformat())
        current += timedelta(days=1)
    return out


def rows_for_sessions(sessions: list[str], horizon: int = 0):
    out = []
    for i, _ in enumerate(sessions):
        if i + horizon >= len(sessions):
            continue
        out.append(SimpleNamespace(
            decision_session_index=i,
            target_endpoint_session_index=i + horizon,
            y=i % 2,
        ))
    return out


def minimal_prereg():
    return {
        "labels": {"POS_1D_UP_DOWN": {}},
        "sample_eligibility": {
            "minimum_train_rows": {"POS_1D_UP_DOWN": 6},
            "minimum_class_support_each_direction_training": {"POS_1D_UP_DOWN": 2},
            "minimum_validation_rows": {"POS_1D_UP_DOWN": 4},
            "minimum_class_support_each_direction_per_validation_fold": {"POS_1D_UP_DOWN": 2},
        },
        "fitting_and_calibration": {
            "minimum_inner_training_rows": {"POS_1D_UP_DOWN": 4},
            "minimum_inner_validation_rows": {"POS_1D_UP_DOWN": 2},
        },
        "chronological_validation": {
            "inner_validation": {
                "class_support_each_direction_minimum": {"POS_1D_UP_DOWN": 1}
            }
        },
    }


def example_config():
    return {
        "config_id": "CFG-SYNTHETIC-001",
        "method_id": "PM0001",
        "configuration": {"label_id": "POS_1D_UP_DOWN", "method_id": "PM0001"},
    }


class WalkForwardR3Tests(unittest.TestCase):
    def test_frozen_outer_windows_are_eight_ordered_nonoverlapping_windows(self):
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        windows = validate_outer_windows(prereg["chronological_validation"]["fold_calendar_windows"])
        self.assertEqual([r["id"] for r in windows], [f"F{i:02d}" for i in range(1, 9)])
        self.assertEqual(windows[0]["start"], "2023-01-01")
        self.assertEqual(windows[-1]["end_inclusive"], "2026-10-10")

    def test_outer_fold_applies_purge_and_embargo_by_exchange_session_index(self):
        sessions = business_sessions("2025-01-02", 30)
        samples = rows_for_sessions(sessions, horizon=0)  # intraday target endpoint stays in decision session
        plan = build_fold_indices(
            samples, sessions, fold_id="F03",
            validation_start_position=20, validation_end_position_exclusive=26,
            purge_sessions=2, embargo_sessions=2,
        )
        self.assertEqual(plan.train_indices, tuple(range(18)))
        self.assertEqual(plan.validation_indices, (22, 23, 24, 25))
        self.assertEqual(plan.counts["purged_training_rows"], 2)
        self.assertEqual(plan.counts["embargoed_validation_rows"], 2)
        self.assertEqual(plan.counts["eligible_train_rows"], 18)
        self.assertEqual(plan.counts["eligible_validation_rows"], 4)

    def test_positional_target_maturity_prevents_unmatured_training_labels(self):
        sessions = business_sessions("2025-01-02", 30)
        samples = rows_for_sessions(sessions, horizon=3)
        plan = build_fold_indices(
            samples, sessions, fold_id="F04",
            validation_start_position=20, validation_end_position_exclusive=26,
            purge_sessions=3, embargo_sessions=3,
        )
        self.assertTrue(all(samples[i].target_endpoint_session_index < 20 for i in plan.train_indices))
        self.assertTrue(all(samples[i].decision_session_index < 17 for i in plan.train_indices))
        self.assertEqual(plan.counts["immature_training_targets_excluded"], 3)
        self.assertTrue(all(samples[i].target_endpoint_session_index < 26 for i in plan.validation_indices))

    def test_validation_target_must_end_inside_same_fold(self):
        sessions = business_sessions("2025-01-02", 30)
        samples = rows_for_sessions(sessions, horizon=3)
        plan = build_fold_indices(
            samples, sessions, fold_id="F05",
            validation_start_position=20, validation_end_position_exclusive=26,
            purge_sessions=3, embargo_sessions=3,
        )
        self.assertEqual(plan.validation_indices, (23,))
        self.assertEqual(plan.counts["validation_targets_outside_window"], 3)
        self.assertEqual(plan.counts["embargoed_validation_rows"], 3)

    def test_inner_folds_are_deterministic_expanding_quantile_windows(self):
        sessions = business_sessions("2025-01-02", 30)
        inner = build_inner_fold_descriptors(sessions, outer_validation_start_position=20)
        self.assertEqual(len(inner), 3)
        self.assertEqual([(x.validation_start_position, x.validation_end_position_exclusive) for x in inner],
                         [(8, 12), (12, 16), (16, 20)])
        self.assertEqual(inner[-1].validation_end_session_index_exclusive, 20)
        self.assertLess(inner[0].validation_end_session_index_exclusive,
                        inner[1].validation_start_session_index_exclusive + 1)

    def test_inner_fold_rejects_insufficient_outer_training_history(self):
        sessions = business_sessions("2025-01-02", 8)
        with self.assertRaisesRegex(WalkForwardContractError, "INNER_QUANTILE_SPLIT_EMPTY_OR_INVALID"):
            build_inner_fold_descriptors(sessions, outer_validation_start_position=5)

    def test_fold_builder_rejects_nonmature_reverse_or_out_of_range_target(self):
        sessions = business_sessions("2025-01-02", 10)
        samples = [SimpleNamespace(decision_session_index=5, target_endpoint_session_index=4, y=1)]
        with self.assertRaisesRegex(WalkForwardContractError, "TARGET_ENDPOINT_PRECEDES_DECISION"):
            build_fold_indices(samples, sessions, fold_id="F01", validation_start_position=7,
                               validation_end_position_exclusive=9, purge_sessions=1, embargo_sessions=1)
        samples = [SimpleNamespace(decision_session_index=5, target_endpoint_session_index=12, y=1)]
        with self.assertRaisesRegex(WalkForwardContractError, "SAMPLE_SESSION_INDEX_OUT_OF_RANGE"):
            build_fold_indices(samples, sessions, fold_id="F01", validation_start_position=7,
                               validation_end_position_exclusive=9, purge_sessions=1, embargo_sessions=1)

    def test_support_gate_uses_frozen_role_specific_minima(self):
        prereg = minimal_prereg()
        labels = [0, 1, 0, 1, 0, 1, 0, 1]
        passed = sample_support(labels, list(range(8)), "POS_1D_UP_DOWN", "OUTER_TRAIN", prereg)
        failed = sample_support(labels, list(range(3)), "POS_1D_UP_DOWN", "OUTER_TRAIN", prereg)
        self.assertTrue(passed["passes"])
        self.assertFalse(failed["passes"])
        self.assertIn("ROW_COUNT_BELOW_FROZEN_MINIMUM", failed["block_reasons"])

    def test_support_gate_rejects_nonbinary_labels(self):
        prereg = minimal_prereg()
        with self.assertRaisesRegex(WalkForwardContractError, "BINARY_LABELS_REQUIRED"):
            sample_support([0, 1, 2], [0, 1, 2], "POS_1D_UP_DOWN", "OUTER_TRAIN", prereg)

    def test_preflight_f01_blocks_are_label_fold_specific(self):
        preflight = {"label_sample_support": [
            {"label_id": "POS_1D_UP_DOWN", "fold_id": "F01",
             "passes_frozen_data_minima": False, "block_reasons": ["TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT"]},
            {"label_id": "POS_1D_UP_DOWN", "fold_id": "F02",
             "passes_frozen_data_minima": True, "block_reasons": []},
        ]}
        self.assertEqual(preflight_block_reason(preflight, "POS_1D_UP_DOWN", "F01"),
                         "TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT")
        self.assertIsNone(preflight_block_reason(preflight, "POS_1D_UP_DOWN", "F02"))
        with self.assertRaisesRegex(WalkForwardContractError, "PREFLIGHT_CELL_MISSING_OR_DUPLICATE"):
            preflight_block_reason(preflight, "POS_1D_UP_DOWN", "F03")

    def test_terminal_row_populates_mandatory_schema_and_unwraps_config_label(self):
        row = terminal_result_row(
            config=example_config(), fold_id="F01",
            train_start="2021-10-11", train_end="2022-12-30",
            validation_start="2023-01-01", validation_end="2023-06-30",
            status="BLOCKED_DATA", failure_reason="TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT",
            eligible_train_rows=0, eligible_validation_rows=0,
            train_positive_support=0, train_negative_support=0,
            validation_positive_support=0, validation_negative_support=0,
            purge_sessions=1, embargo_sessions=1, label_exclusion_count=None,
            feature_missingness=None, label_target_endpoint=None,
            source_manifest_sha256="a" * 64,
        )
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        required = set(prereg["output_and_failure_rules"]["mandatory_fields"])
        self.assertTrue(required.issubset(row))
        self.assertEqual(row["label_id"], "POS_1D_UP_DOWN")
        self.assertEqual(row["by_family_id"], "POS_1D_UP_DOWN")
        self.assertEqual(row["terminal_status"], "BLOCKED_DATA")
        self.assertTrue(all(row[k] is None for k in ("baseline_log_loss", "candidate_log_loss", "raw_p_value")))

    def test_blocked_row_rejects_numeric_performance_metrics(self):
        with self.assertRaisesRegex(WalkForwardContractError, "BLOCKED_OR_FAILED_ROW_MUST_HAVE_NULL_METRICS"):
            terminal_result_row(
                config=example_config(), fold_id="F01",
                train_start="2021-10-11", train_end="2022-12-30",
                validation_start="2023-01-01", validation_end="2023-06-30",
                status="BLOCKED_GATE", failure_reason="NOT_AUTHORIZED",
                purge_sessions=1, embargo_sessions=1, label_exclusion_count=0,
                feature_missingness={}, label_target_endpoint=None,
                source_manifest_sha256="b" * 64,
                metrics={"candidate_log_loss": 0.5},
            )

    def test_result_row_validator_checks_coverage_and_logloss_sign(self):
        row = terminal_result_row(
            config=example_config(), fold_id="F01",
            train_start="2021-10-11", train_end="2022-12-30",
            validation_start="2023-01-01", validation_end="2023-06-30",
            status="EXECUTED_AUDITED", failure_reason=None,
            eligible_train_rows=100, eligible_validation_rows=50,
            train_positive_support=50, train_negative_support=50,
            validation_positive_support=25, validation_negative_support=25,
            purge_sessions=1, embargo_sessions=1, label_exclusion_count=0,
            feature_missingness={}, label_target_endpoint="2023-06-30T15:30:00+05:30",
            source_manifest_sha256="c" * 64,
            metrics={
                "baseline_log_loss": 0.70, "candidate_log_loss": 0.65,
                "log_loss_improvement": 0.05, "raw_p_value": 0.04,
                "by_adjusted_p_value": 0.2, "bootstrap_ci_lower": 0.01,
                "bootstrap_ci_upper": 0.08, "brier_score": 0.23,
                "balanced_accuracy": 0.6, "roc_auc": 0.62,
                "average_precision": 0.63, "calibration_intercept": 0.01,
                "calibration_slope": 0.95, "bootstrap_status": "PASS",
                "bootstrap_replicates": 10000,
            },
        )
        result = validate_result_rows([row], [("CFG-SYNTHETIC-001", "F01")])
        self.assertTrue(result["complete_expected_coverage"])
        self.assertEqual(result["metrics_arithmetic_checked"], 1)
        bad = dict(row)
        bad["log_loss_improvement"] = -0.05
        with self.assertRaisesRegex(WalkForwardContractError, "LOG_LOSS_IMPROVEMENT_ARITHMETIC_MISMATCH"):
            validate_result_rows([bad], [("CFG-SYNTHETIC-001", "F01")])

    def test_result_row_validator_rejects_duplicates_and_missing_rows(self):
        row = terminal_result_row(
            config=example_config(), fold_id="F01",
            train_start="2021-10-11", train_end="2022-12-30",
            validation_start="2023-01-01", validation_end="2023-06-30",
            status="BLOCKED_GATE", failure_reason="NO_IMPLEMENTATION_AUTHORIZATION",
            purge_sessions=1, embargo_sessions=1, label_exclusion_count=None,
            feature_missingness=None, label_target_endpoint=None,
            source_manifest_sha256="d" * 64,
        )
        with self.assertRaisesRegex(WalkForwardContractError, "DUPLICATE_CONFIG_FOLD_RESULT_ROW"):
            validate_result_rows([row, dict(row)], [("CFG-SYNTHETIC-001", "F01")])
        with self.assertRaisesRegex(WalkForwardContractError, "RESULT_ROW_COVERAGE_MISMATCH"):
            validate_result_rows([], [("CFG-SYNTHETIC-001", "F01")])

    def test_result_row_validator_rejects_invalid_probability_metrics(self):
        row = terminal_result_row(
            config=example_config(), fold_id="F01",
            train_start="2021-10-11", train_end="2022-12-30",
            validation_start="2023-01-01", validation_end="2023-06-30",
            status="REJECTED_EMPIRICAL", failure_reason="NOT_SIGNIFICANT",
            eligible_train_rows=100, eligible_validation_rows=50,
            purge_sessions=1, embargo_sessions=1, label_exclusion_count=0,
            feature_missingness={}, label_target_endpoint=None,
            source_manifest_sha256="e" * 64,
            metrics={"baseline_log_loss": 0.7, "candidate_log_loss": 0.65,
                     "log_loss_improvement": 0.05, "brier_score": 1.2},
        )
        with self.assertRaisesRegex(WalkForwardContractError, "SCALAR_METRIC_OUT_OF_RANGE"):
            validate_result_rows([row], [("CFG-SYNTHETIC-001", "F01")])


if __name__ == "__main__":
    unittest.main()
