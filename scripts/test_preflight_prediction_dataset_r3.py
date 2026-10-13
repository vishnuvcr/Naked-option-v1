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

    def test_validation_sample_rules_are_loaded_before_use_and_range_checked(self):
        prereg = {
            "sample_eligibility": {
                "target_pair_missing_fraction_max": 0.005,
                "minimum_validation_rows": {"INTRA_5M_UP_DOWN": 100},
                "minimum_class_support_each_direction_per_validation_fold": {"INTRA_5M_UP_DOWN": 20},
            }
        }
        sample_rules, missing_fraction = preflight.validation_sample_rules(prereg)
        self.assertIs(sample_rules, prereg["sample_eligibility"])
        self.assertAlmostEqual(missing_fraction, 0.005)
        for invalid in (float("nan"), float("inf"), -0.01, 1.01, "not-a-number"):
            with self.subTest(invalid=invalid), self.assertRaises(preflight.PreflightBlocked):
                preflight.validation_sample_rules({"sample_eligibility": {"target_pair_missing_fraction_max": invalid}})
        with self.assertRaises(preflight.PreflightBlocked):
            preflight.validation_sample_rules({})

    def test_spot_quarantine_rule_excludes_only_ineligible_observations(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        tz=ZoneInfo("Asia/Kolkata")
        regular={"is_exchange_trading_session":True,"regular_hours_compatible":True,"intraday_label_eligible":True,"positional_label_eligible":True}
        closed={"is_exchange_trading_session":False,"regular_hours_compatible":False,"intraday_label_eligible":False,"positional_label_eligible":False}
        special={"is_exchange_trading_session":True,"regular_hours_compatible":False,"intraday_label_eligible":False,"positional_label_eligible":False}
        self.assertIsNone(preflight.spot_quarantine_reason(regular,datetime(2024,1,2,9,16,tzinfo=tz),"21000"))
        self.assertEqual(preflight.spot_quarantine_reason(closed,datetime(2024,1,6,10,0,tzinfo=tz),"21000"),"CLOSED_OR_UNMAPPED_SESSION")
        self.assertEqual(preflight.spot_quarantine_reason(special,datetime(2024,11,1,10,0,tzinfo=tz),"21000"),"NON_STANDARD_OR_INELIGIBLE_SESSION")
        self.assertEqual(preflight.spot_quarantine_reason(regular,datetime(2024,1,2,15,31,tzinfo=tz),"21000"),"OUTSIDE_REGULAR_SESSION")
        self.assertEqual(preflight.spot_quarantine_reason(regular,datetime(2024,1,2,9,16,1,tzinfo=tz),"21000"),"NON_MINUTE_TIMESTAMP")
        for value in ("", "not-a-price", "nan", "inf", "0", "-1"):
            with self.subTest(value=value):
                self.assertEqual(preflight.spot_quarantine_reason(regular,datetime(2024,1,2,9,16,tzinfo=tz),value),"INVALID_OR_MISSING_SPOT_CLOSE")

    def test_preprocessing_rules_are_pinned_by_git_blob_and_sha256(self):
        import hashlib, json
        rel=preflight.ROOT/"research"/"data"/"_test_preprocessing_policy.json"
        raw=json.dumps({"status":"FROZEN_PRE_RESULTS","amendment_id":"PHASE8P_DATA_PREPROCESSING_AMENDMENT_R3_2026-10-13"},sort_keys=True).encode()
        try:
            rel.write_bytes(raw)
            prereg={"scope":{
              "data_preprocessing_amendment_id":"PHASE8P_DATA_PREPROCESSING_AMENDMENT_R3_2026-10-13",
              "data_preprocessing_rules_path":rel.relative_to(preflight.ROOT).as_posix(),
              "data_preprocessing_rules_git_blob_sha1":preflight.git_blob_sha1(raw),
              "data_preprocessing_rules_sha256":hashlib.sha256(raw).hexdigest(),
            }}
            self.assertEqual(preflight.validate_preprocessing_rules(prereg,rel)["status"],"FROZEN_PRE_RESULTS")
            prereg["scope"]["data_preprocessing_rules_git_blob_sha1"]="0"*40
            with self.assertRaisesRegex(preflight.PreflightBlocked,"GIT_BLOB_PIN_MISMATCH"):
                preflight.validate_preprocessing_rules(prereg,rel)
        finally:
            rel.unlink(missing_ok=True)

    def test_empty_validation_metric_fails_closed_without_nan(self):
        metric = preflight.empty_metric()
        row = preflight.finalize_metric("INTRA_120M_UP_DOWN","F08",metric,0.01,5000,250)
        self.assertIsNone(row["target_pair_missing_fraction"])
        self.assertFalse(row["passes_frozen_data_minima"])
        self.assertIn("NO_POSSIBLE_TARGET_PAIRS",row["block_reasons"])
        self.assertIn("VALIDATION_ROWS_BELOW_FROZEN_MINIMUM",row["block_reasons"])


if __name__ == "__main__":
    unittest.main()
