import unittest

from build_prediction_eligibility_manifest_r3 import FOLD_IDS, build_manifest


def cfg(cid, mid="PM0001", label="INTRA_5M_UP_DOWN"):
    return {
        "config_id": cid,
        "config_sha256": "a" * 64,
        "method_id": mid,
        "configuration": {"label_id": label, "stratum": "intraday"},
    }


def method(mid, decision="ALLOW_IN_PRINCIPLE", eligible=False,
           impl="NOT_IMPLEMENTED_OR_TESTER_APPROVED"):
    return {
        "method_id": mid,
        "compatibility_decision": decision,
        "eligible_for_empirical_fitting": eligible,
        "implementation_status": impl,
        "decision_code": "TEST_BLOCK",
    }


def fold_support(label, blocked=()):
    blocked = set(blocked)
    return [{
        "label_id": label,
        "fold_id": fold,
        "passes_frozen_data_minima": fold not in blocked,
        "block_reasons": ["TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT"] if fold in blocked else [],
        "missing_target_pairs": 2 if fold in blocked else 0,
        "possible_target_pairs": 100,
        "target_pair_missing_fraction": 0.02 if fold in blocked else 0.0,
    } for fold in FOLD_IDS]


class EligibilityManifestTests(unittest.TestCase):
    def test_conditional_method_is_blocked_not_promoted(self):
        m = build_manifest(
            [cfg("C1")], [method("PM0001")],
            {"canonical_hash_matches": True, "holdout_accessed": False,
             "model_fitting_performed": False, "label_sample_support": fold_support("INTRA_5M_UP_DOWN")},
            {"pin": "x"},
        )
        self.assertEqual(m["disposition_counts"], {"BLOCKED_IMPLEMENTATION_OR_AUTHORIZATION": 1})
        self.assertFalse(m["empirical_fit_authorized"])
        self.assertFalse(m["records"][0]["empirical_fit_authorized"])

    def test_compatibility_block_takes_precedence(self):
        m = build_manifest(
            [cfg("C1", "PM0002")], [method("PM0002", "BLOCK", False)],
            {"canonical_hash_matches": True, "holdout_accessed": False,
             "model_fitting_performed": False, "label_sample_support": fold_support("INTRA_5M_UP_DOWN")},
            {},
        )
        self.assertEqual(m["records"][0]["disposition"], "BLOCKED_METHOD_COMPATIBILITY")

    def test_single_fold_block_is_scoped_not_horizon_wide(self):
        m = build_manifest(
            [cfg("C1", "PM0003", "POS_1D_UP_DOWN")],
            [method("PM0003", eligible=True, impl="DEVELOPER_TESTED")],
            {"canonical_hash_matches": True, "holdout_accessed": False,
             "model_fitting_performed": False,
             "label_sample_support": fold_support("POS_1D_UP_DOWN", {"F01"})},
            {},
        )
        row = m["records"][0]
        self.assertEqual(row["disposition"], "ELIGIBLE_PENDING_EXECUTOR_GATE")
        self.assertEqual(row["blocked_outer_fold_ids"], ["F01"])
        self.assertEqual(row["supported_outer_fold_ids"], list(FOLD_IDS[1:]))
        self.assertFalse(row["empirical_fit_authorized"])

    def test_all_folds_blocked_blocks_configuration(self):
        m = build_manifest(
            [cfg("C1", "PM0003", "POS_1D_UP_DOWN")],
            [method("PM0003", eligible=True, impl="DEVELOPER_TESTED")],
            {"canonical_hash_matches": True, "holdout_accessed": False,
             "model_fitting_performed": False,
             "label_sample_support": fold_support("POS_1D_UP_DOWN", FOLD_IDS)},
            {},
        )
        self.assertEqual(m["records"][0]["disposition"], "BLOCKED_DATA_SUPPORT")
        self.assertEqual(m["records"][0]["blocked_outer_fold_ids"], list(FOLD_IDS))

    def test_unknown_method_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "CONFIG_METHOD_NOT_REGISTERED"):
            build_manifest(
                [cfg("C1", "PM404")], [method("PM0001")],
                {"canonical_hash_matches": True, "holdout_accessed": False,
                 "model_fitting_performed": False, "label_sample_support": fold_support("INTRA_5M_UP_DOWN")},
                {},
            )

    def test_duplicate_config_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CONFIG_ID"):
            build_manifest(
                [cfg("C1"), cfg("C1")], [method("PM0001")],
                {"canonical_hash_matches": True, "holdout_accessed": False,
                 "model_fitting_performed": False, "label_sample_support": fold_support("INTRA_5M_UP_DOWN")},
                {},
            )

    def test_incomplete_fold_grid_fails_closed(self):
        rows = fold_support("INTRA_5M_UP_DOWN")[:-1]
        with self.assertRaisesRegex(ValueError, "PREFLIGHT_FOLD_GRID_MISMATCH"):
            build_manifest(
                [cfg("C1")], [method("PM0001")],
                {"canonical_hash_matches": True, "holdout_accessed": False,
                 "model_fitting_performed": False, "label_sample_support": rows},
                {},
            )

    def test_blocked_cell_without_reason_fails_closed(self):
        rows = fold_support("POS_1D_UP_DOWN", {"F01"})
        rows[0]["block_reasons"] = []
        with self.assertRaisesRegex(ValueError, "BLOCKED_FOLD_MISSING_REASON"):
            build_manifest(
                [cfg("C1", label="POS_1D_UP_DOWN")], [method("PM0001")],
                {"canonical_hash_matches": True, "holdout_accessed": False,
                 "model_fitting_performed": False, "label_sample_support": rows},
                {},
            )


if __name__ == "__main__":
    unittest.main()
