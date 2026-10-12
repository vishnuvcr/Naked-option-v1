"""Unit tests for R3 data-preflight helpers; never opens the market dataset."""
from __future__ import annotations
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preflight_prediction_dataset_r3 as preflight


class PredictionDataPreflightHelpersTests(unittest.TestCase):
    def test_epoch_unit_detection_seconds_ms_us_ns(self):
        cases = [
            ("1760000000", "seconds"),
            ("1760000000000", "milliseconds"),
            ("1760000000000000", "microseconds"),
            ("1760000000000000000", "nanoseconds"),
        ]
        for raw, expected_unit in cases:
            with self.subTest(raw=raw):
                epoch, dt, unit = preflight.epoch_to_datetime(raw)
                self.assertEqual(unit, expected_unit)
                self.assertTrue(math.isfinite(epoch))
                self.assertIsNotNone(dt.tzinfo)
                self.assertEqual(dt.tzinfo.key, "Asia/Kolkata")

    def test_epoch_rejects_nan_and_infinity(self):
        for raw in ("nan", "inf", "-inf"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                preflight.epoch_to_datetime(raw)

    def test_price_column_selection_is_priority_ordered_and_case_insensitive(self):
        header = ["Timestamp", "SPOT_CLOSE", "close", "index_close"]
        chosen, candidates = preflight.exact_close_column(header)
        self.assertEqual(chosen, "SPOT_CLOSE")
        self.assertEqual(candidates, ["SPOT_CLOSE", "index_close", "close"])
        chosen, candidates = preflight.exact_close_column(["row_type", "timestamp_epoch", "close"])
        self.assertEqual(chosen, "close")
        self.assertEqual(candidates, ["close"])
        chosen, candidates = preflight.exact_close_column(["row_type", "timestamp_epoch", "option_close"])
        self.assertIsNone(chosen)
        self.assertEqual(candidates, [])

    def test_fold_assignment_uses_frozen_inclusive_dates(self):
        folds = [
            {"id":"F01","start":"2023-01-01","end_inclusive":"2023-06-30"},
            {"id":"F02","start":"2023-07-01","end_inclusive":"2023-12-31"},
        ]
        self.assertEqual(preflight.fold_for_day("2023-01-01", folds), "F01")
        self.assertEqual(preflight.fold_for_day("2023-06-30", folds), "F01")
        self.assertEqual(preflight.fold_for_day("2023-07-01", folds), "F02")
        self.assertIsNone(preflight.fold_for_day("2022-12-31", folds))

    def test_validation_minima_fail_closed_on_missingness_rows_or_class_support(self):
        metric = {
            "possible_target_pairs":100,
            "missing_target_pairs":2,
            "flat_exclusions":5,
            "up":40,
            "down":45,
            "classifiable_rows":85,
            "endpoint_ineligible":0,
        }
        ok = preflight.finalize_metric("POS_1D_UP_DOWN","F01",metric,0.01,40,15)
        self.assertFalse(ok["passes_frozen_data_minima"])
        self.assertIn("TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT",ok["block_reasons"])
        below_rows = dict(metric, missing_target_pairs=0, classifiable_rows=39)
        row_fail = preflight.finalize_metric("POS_1D_UP_DOWN","F01",below_rows,0.01,40,15)
        self.assertIn("VALIDATION_ROWS_BELOW_FROZEN_MINIMUM",row_fail["block_reasons"])
        below_classes = dict(metric, missing_target_pairs=0, classifiable_rows=85, up=14)
        class_fail = preflight.finalize_metric("POS_1D_UP_DOWN","F01",below_classes,0.01,40,15)
        self.assertIn("DIRECTION_CLASS_SUPPORT_BELOW_FROZEN_MINIMUM",class_fail["block_reasons"])

    def test_empty_validation_metric_fails_closed_without_nan(self):
        metric = preflight.empty_metric()
        row = preflight.finalize_metric("INTRA_120M_UP_DOWN","F08",metric,0.01,5000,250)
        self.assertIsNone(row["target_pair_missing_fraction"])
        self.assertFalse(row["passes_frozen_data_minima"])
        self.assertIn("NO_POSSIBLE_TARGET_PAIRS",row["block_reasons"])
        self.assertIn("VALIDATION_ROWS_BELOW_FROZEN_MINIMUM",row["block_reasons"])


if __name__ == "__main__":
    unittest.main()
