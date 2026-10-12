"""Frozen preregistration integrity tests; never opens market data."""
from __future__ import annotations

import json
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "research" / "registry"
PREREG = REG / "PREDICTION_PREREGISTRATION_V2_R2.json"
LABEL = REG / "PREDICTION_LABEL_MANIFEST_V2_R2.json"
CONFIG = REG / "PREDICTION_CONFIG_MANIFEST_V2_R2.json"
INDEX = REG / "PREDICTION_REGISTRY_SHARD_INDEX_V2_R2.json"
MATRIX = REG / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"
DATA_MANIFEST = ROOT / "research" / "data" / "DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prediction_registry_synthetic_dryrun import git_blob_sha1, canonical_json, sha256_bytes


class PredictionPreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads(PREREG.read_text(encoding="utf-8"))
        cls.l = json.loads(LABEL.read_text(encoding="utf-8"))
        cls.c = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.i = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.m = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.d = json.loads(DATA_MANIFEST.read_text(encoding="utf-8"))

    def test_all_source_git_blob_hashes_are_pinned(self):
        pins = self.p["scope"]
        paths = {
            "data_manifest_sha256_git_blob": DATA_MANIFEST,
            "label_manifest_sha256_git_blob": LABEL,
            "config_manifest_sha256_git_blob": CONFIG,
            "registry_index_sha256_git_blob": INDEX,
            "compatibility_matrix_sha256_git_blob": MATRIX,
        }
        for key, path in paths.items():
            with self.subTest(source=key):
                self.assertEqual(pins[key], git_blob_sha1(path.read_bytes()))

    def test_registry_and_matrix_counts_and_semantic_uniqueness(self):
        self.assertEqual(self.i["method_record_count"], 1000)
        self.assertEqual(self.i["configuration_record_count"], 8000)
        self.assertEqual(len(self.i["method_shards"]), 40)
        self.assertEqual(len(self.i["config_shards"]), 80)
        self.assertEqual(self.m["method_count"], 1000)
        self.assertEqual(self.m["compatibility_allow_in_principle_count"], 426)
        self.assertEqual(self.m["compatibility_block_count"], 574)
        self.assertEqual(self.m["empirically_eligible_count"], 0)
        self.assertEqual(self.m["semantic_fingerprint_unique_count"], 1000)
        self.assertEqual(self.m["duplicate_semantic_fingerprints"], [])
        body = dict(self.m)
        expected = body.pop("matrix_sha256")
        self.assertEqual(expected, sha256_bytes(canonical_json(body)))

    def test_dataset_source_is_metadata_pinned_but_still_encrypted(self):
        self.assertTrue(self.d["encrypted_only"])
        self.assertEqual(self.d["rows_preserved"], 8999865)
        self.assertTrue(self.p["scope"]["source_dataset_is_encrypted_only"])
        self.assertIn("No untouched holdout access", self.p["output_and_failure_rules"]["holdout_protection"])

    def test_all_eight_outer_calendar_windows_are_fixed_and_contiguous(self):
        folds = self.p["chronological_validation"]["fold_calendar_windows"]
        self.assertEqual(len(folds), 8)
        self.assertEqual(folds[0]["start"], "2023-01-01")
        self.assertEqual(folds[-1]["end_inclusive"], "2026-10-10")
        from datetime import date, timedelta
        for a, b in zip(folds, folds[1:]):
            self.assertEqual(date.fromisoformat(a["end_inclusive"]) + timedelta(days=1), date.fromisoformat(b["start"]))
        self.assertEqual(self.p["chronological_validation"]["overlap_purge_sessions"], 1)
        self.assertEqual(self.p["chronological_validation"]["embargo_sessions"], 1)
        self.assertFalse(self.p["chronological_validation"]["final_untouched_holdout"].startswith("INCLUDED"))

    def test_label_flat_tolerance_and_sample_rules_match(self):
        self.assertEqual(self.l["return_convention"]["flat_tolerance_abs_simple_return"], 1e-8)
        self.assertEqual(self.p["labels"]["INTRA_30M_UP_DOWN"]["flat_tolerance_abs_simple_return"], 1e-8)
        self.assertEqual(self.p["labels"]["POS_1D_UP_DOWN"]["flat_tolerance_abs_simple_return"], 1e-8)
        self.assertEqual(self.p["sample_eligibility"]["target_pair_missing_fraction_max"], 0.01)
        self.assertEqual(self.p["sample_eligibility"]["feature_column_missing_fraction_max"], 0.2)

    def test_multiple_testing_and_bootstrap_are_explicit(self):
        mult = self.p["metrics_and_inference"]["multiplicity"]
        boot = self.p["metrics_and_inference"]["bootstrap"]
        self.assertEqual(mult["procedure"], "Benjamini-Yekutieli false discovery rate")
        self.assertEqual(mult["q"], 0.05)
        self.assertEqual(boot["replicates"], 10000)
        self.assertEqual(boot["block_length_exchange_sessions"], 5)
        self.assertEqual(self.p["chronological_validation"]["inner_validation"]["fold_count"], 3)
        self.assertFalse(mult["no_repeated_holdout_tuning"] is False)


if __name__ == "__main__":
    unittest.main()
