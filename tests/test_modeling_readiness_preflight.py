import unittest
from scripts.modeling_readiness_preflight import (
    direction_label, map_session_horizons, validate_ohlc, classify_feature_family,
    validate_split, validate_session_metadata, sanitize_report
)

class ReadinessPrimitiveTests(unittest.TestCase):
    def test_direction_sign_and_flat_tolerance(self):
        self.assertEqual(direction_label(100, 99), "DOWN")
        self.assertEqual(direction_label(100, 100), "FLAT")
        self.assertEqual(direction_label(100, 101), "UP")
        self.assertEqual(direction_label(100, 100*(1+1e-8)), "FLAT")

    def test_bad_prices_fail_closed(self):
        with self.assertRaises(ValueError):
            direction_label(0, 1)
        with self.assertRaises(ValueError):
            direction_label(float("nan"), 1)

    def test_horizons_use_ordered_sessions_not_calendar_days(self):
        sessions=["2026-01-01","2026-01-02","2026-01-05","2026-01-06"]
        mapped=map_session_horizons(sessions, horizons=(1,2))
        self.assertEqual(mapped["2026-01-02"][1], "2026-01-05")
        self.assertIsNone(mapped["2026-01-05"][2])

    def test_generator_horizons_are_reused_for_each_session(self):
        mapped = map_session_horizons(
            ["2026-01-01", "2026-01-02", "2026-01-05"],
            horizons=iter((1, 2)),
        )
        self.assertTrue(all(set(values) == {1, 2} for values in mapped.values()))

    def test_duplicate_or_unsorted_session_list_rejected(self):
        with self.assertRaises(ValueError):
            map_session_horizons(["2026-01-02","2026-01-02"])
        with self.assertRaises(ValueError):
            map_session_horizons(["2026-01-05","2026-01-01"])

    def test_ohlc_inequalities_and_missingness(self):
        self.assertTrue(validate_ohlc(100,102,98,101)[0])
        self.assertEqual(validate_ohlc(100,99,98,101)[1], "OHLC_INEQUALITY_FAILURE")
        self.assertEqual(validate_ohlc(None,102,98,101)[1], "MISSING_OR_NONFINITE_OHLC")

    def test_feature_availability_and_blank_fields(self):
        self.assertEqual(classify_feature_family(nonblank_count=0,total_count=10,point_in_time_proven=True).status,"BLOCKED_DATA")
        self.assertEqual(classify_feature_family(nonblank_count=5,total_count=10,point_in_time_proven=False).status,"NOT_ESTIMABLE")
        self.assertEqual(classify_feature_family(nonblank_count=5,total_count=10,point_in_time_proven=True,join_validity_proven=False).status,"PASS_WITH_RESTRICTIONS")

    def test_holdout_missing_or_leakage_blocks(self):
        self.assertEqual(validate_split(train_origins=300,common_validation_origins=300,label_endpoints_before_validation=True,holdout_manifest_verified=False).status,"BLOCKED_HOLDOUT_PROOF")
        self.assertEqual(validate_split(train_origins=300,common_validation_origins=300,label_endpoints_before_validation=False,holdout_manifest_verified=True).status,"BLOCKED_LEAKAGE")
        self.assertEqual(validate_split(train_origins=251,common_validation_origins=250,label_endpoints_before_validation=True,holdout_manifest_verified=True).status,"INCOMPLETE_NOT_PROMOTABLE")
        self.assertEqual(validate_split(train_origins=252,common_validation_origins=250,label_endpoints_before_validation=True,holdout_manifest_verified=True).status,"PASS")

    def test_session_provenance_and_ambiguity(self):
        self.assertEqual(validate_session_metadata(calendar_provenance=False,candle_semantics="BAR_END",unresolved_session_flags=0,spot_duplicate_keys=0).status,"NOT_ESTIMABLE")
        self.assertEqual(validate_session_metadata(calendar_provenance=True,candle_semantics="UNKNOWN",unresolved_session_flags=0,spot_duplicate_keys=0).status,"NOT_ESTIMABLE")
        self.assertEqual(validate_session_metadata(calendar_provenance=True,candle_semantics="BAR_END",unresolved_session_flags=2,spot_duplicate_keys=0).status,"PASS_WITH_EXCLUSIONS")
        self.assertEqual(validate_session_metadata(calendar_provenance=True,candle_semantics="BAR_END",unresolved_session_flags=0,spot_duplicate_keys=1).status,"BLOCKED")

    def test_report_allowlist_prevents_row_level_output(self):
        self.assertEqual(sanitize_report({"rows":100,"columns":47})["rows"],100)
        with self.assertRaises(ValueError):
            sanitize_report({"rows":100,"last_price":22000.0})

if __name__=="__main__":
    unittest.main()
