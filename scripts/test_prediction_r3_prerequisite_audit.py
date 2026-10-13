"""Synthetic regression tests for the Phase 8P R3 prerequisite audit."""
from __future__ import annotations

import unittest
from collections import Counter

import audit_prediction_r3_prerequisites as audit


def support_fixture(blocked=None):
    blocked = blocked or set()
    rows = []
    for label in audit.ALL_LABELS:
        for fold in audit.FOLD_IDS:
            is_blocked = (label, fold) in blocked
            rows.append({
                "label_id": label,
                "fold_id": fold,
                "passes_frozen_data_minima": not is_blocked,
                "block_reasons": ["TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT"] if is_blocked else [],
                "missing_target_pairs": 4 if is_blocked else 0,
                "possible_target_pairs": 100,
                "target_pair_missing_fraction": 0.04 if is_blocked else 0.0,
            })
    return rows


class R3PrerequisiteAuditTests(unittest.TestCase):
    def test_git_blob_sha1_uses_git_blob_header(self):
        self.assertEqual(
            audit.git_blob_sha1(b"hello\n"),
            "ce013625030ba8dba906f756967f9e9ca394464a",
        )

    def test_exact_80_cell_grid_passes_with_only_frozen_positional_f01_blocks(self):
        preflight = {
            "status": "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS",
            "canonical_hash_matches": True,
            "holdout_accessed": False,
            "model_fitting_performed": False,
            "plaintext_uploaded": False,
            "raw_rows_emitted": False,
            "raw_rows_retained": False,
            "expected_rows": 8999865,
            "rows_read": 8999865,
            "rows_by_type": {"OPTION": 8490723, "SPOT": 509142},
            "timestamp_min_local": "2021-10-11T09:16:00+05:30",
            "timestamp_max_local": "2026-10-09T15:39:00+05:30",
            "canonical_uncompressed_csv_sha256": "same",
            "expected_canonical_csv_sha256": "same",
            "label_sample_support": support_fixture(audit.EXPECTED_BLOCKED_CELLS),
        }
        result = audit.validate_preflight(preflight)
        self.assertEqual(result["label_fold_cells"], 80)
        self.assertEqual(result["supported_cells"], 75)
        self.assertEqual(result["blocked_cells"], 5)

    def test_frozen_fold_blocks_cannot_be_relabelled_as_supported(self):
        wrong = {("POS_1D_UP_DOWN", "F02")}
        preflight = {
            "status": "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS",
            "canonical_hash_matches": True,
            "holdout_accessed": False,
            "model_fitting_performed": False,
            "plaintext_uploaded": False,
            "raw_rows_emitted": False,
            "raw_rows_retained": False,
            "expected_rows": 8999865,
            "rows_read": 8999865,
            "rows_by_type": {"OPTION": 8490723, "SPOT": 509142},
            "timestamp_min_local": "2021-10-11T09:16:00+05:30",
            "timestamp_max_local": "2026-10-09T15:39:00+05:30",
            "canonical_uncompressed_csv_sha256": "same",
            "expected_canonical_csv_sha256": "same",
            "label_sample_support": support_fixture(wrong),
        }
        with self.assertRaisesRegex(audit.GateError, "DATA_PREFLIGHT_SCOPED_BLOCKS_CHANGED"):
            audit.validate_preflight(preflight)

    def test_duplicate_label_fold_cell_fails_closed(self):
        preflight = {
            "status": "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS",
            "canonical_hash_matches": True,
            "holdout_accessed": False,
            "model_fitting_performed": False,
            "plaintext_uploaded": False,
            "raw_rows_emitted": False,
            "raw_rows_retained": False,
            "expected_rows": 8999865,
            "rows_read": 8999865,
            "rows_by_type": {"OPTION": 8490723, "SPOT": 509142},
            "timestamp_min_local": "2021-10-11T09:16:00+05:30",
            "timestamp_max_local": "2026-10-09T15:39:00+05:30",
            "canonical_uncompressed_csv_sha256": "same",
            "expected_canonical_csv_sha256": "same",
            "label_sample_support": support_fixture(audit.EXPECTED_BLOCKED_CELLS),
        }
        preflight["label_sample_support"].append(dict(preflight["label_sample_support"][0]))
        with self.assertRaisesRegex(audit.GateError, "DATA_PREFLIGHT_DUPLICATE_CELL"):
            audit.validate_preflight(preflight)

    def test_model_fitting_flag_must_remain_false_during_prerequisite_audit(self):
        preflight = {
            "status": "PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS",
            "canonical_hash_matches": True,
            "holdout_accessed": False,
            "model_fitting_performed": True,
            "plaintext_uploaded": False,
            "raw_rows_emitted": False,
            "raw_rows_retained": False,
            "expected_rows": 8999865,
            "rows_read": 8999865,
            "rows_by_type": {"OPTION": 8490723, "SPOT": 509142},
            "timestamp_min_local": "2021-10-11T09:16:00+05:30",
            "timestamp_max_local": "2026-10-09T15:39:00+05:30",
            "canonical_uncompressed_csv_sha256": "same",
            "expected_canonical_csv_sha256": "same",
            "label_sample_support": support_fixture(audit.EXPECTED_BLOCKED_CELLS),
        }
        with self.assertRaisesRegex(audit.GateError, "SAFETY_FLAG_NOT_FALSE:model_fitting_performed"):
            audit.validate_preflight(preflight)

    def test_label_registry_is_fixed_at_ten_horizons(self):
        self.assertEqual(len(audit.ALL_LABELS), 10)
        self.assertEqual(len(set(audit.ALL_LABELS)), 10)
        self.assertEqual(len(audit.EXPECTED_BLOCKED_CELLS), 5)

    def test_scope_blocks_are_fold_scoped_not_horizon_wide(self):
        supported = [f for f in audit.FOLD_IDS if f != "F01"]
        self.assertEqual(len(supported), 7)
        self.assertEqual(Counter(audit.EXPECTED_BLOCKED_CELLS), Counter({
            ("POS_1D_UP_DOWN", "F01"): 1,
            ("POS_2D_UP_DOWN", "F01"): 1,
            ("POS_3D_UP_DOWN", "F01"): 1,
            ("POS_5D_UP_DOWN", "F01"): 1,
            ("POS_10D_UP_DOWN", "F01"): 1,
        }))


if __name__ == "__main__":
    unittest.main()
