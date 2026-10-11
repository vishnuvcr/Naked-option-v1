import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.modeling_readiness_feasibility_run import (
    EXPECTED_DATASET_SHA256, EXPECTED_DATASET_ID, EXPECTED_ROWS, EXPECTED_COLUMNS,
    git_blob_sha1, validate_execution_authorization, validate_input_manifests,
    build_blocked_report, sanitize_report, _report_schema_subset_validate,
)


class FeasibilityRunTests(unittest.TestCase):
    def test_absent_holdout_boundary_blocks_before_csv_open(self):
        base = {
            "dataset_sha256": EXPECTED_DATASET_SHA256, "dataset_id": EXPECTED_DATASET_ID,
            "expected_rows": EXPECTED_ROWS, "expected_columns": EXPECTED_COLUMNS,
            "column_map": {"row_type": "type", "timestamp_epoch": "ts", "session_date": "date",
                           "open": "o", "high": "h", "low": "l", "close": "c", "volume": "v",
                           "quality_flags": "q", "join_status": "j"},
            "row_type_values": {"option": "OPTION", "spot": "SPOT"},
        }
        sources = {"dataset_sha256": EXPECTED_DATASET_SHA256, "cache_only": True,
                   "source_vintages": [{"family": "SPOT_OHLCV", "pit_proven": True}]}
        calendar = {"dataset_sha256": EXPECTED_DATASET_SHA256, "exchange": "NSE",
                    "calendar_source": "synthetic official calendar fixture",
                    "valid_sessions": ["2026-01-01", "2026-01-02", "2026-01-05"]}
        split = {"dataset_sha256": EXPECTED_DATASET_SHA256, "holdout_boundary_found": False}
        ready, status = validate_input_manifests(base, sources, calendar, split)
        self.assertFalse(ready)
        self.assertEqual(status, "BLOCKED_HOLDOUT_PROOF")
        blocked = build_blocked_report(base, status)
        self.assertEqual(blocked["prefix_rows_scanned"], 0)
        self.assertEqual(blocked["gate_status"], "BLOCKED")

    def test_dataset_identity_mismatch_rejected(self):
        input_manifest = {"dataset_sha256": "0" * 64}
        empty = {"dataset_sha256": EXPECTED_DATASET_SHA256}
        with self.assertRaisesRegex(ValueError, "MANIFEST_DATASET_HASH_MISMATCH"):
            validate_input_manifests(input_manifest, empty, empty, empty)

    def test_source_manifest_requires_cached_provenance(self):
        m = {"dataset_sha256": EXPECTED_DATASET_SHA256, "cache_only": False,
             "source_vintages": [{"family": "SPOT", "pit_proven": True}]}
        with self.assertRaisesRegex(ValueError, "SOURCE_MANIFEST_NOT_CACHE_ONLY"):
            validate_input_manifests(
                {"dataset_sha256": EXPECTED_DATASET_SHA256, "expected_rows": EXPECTED_ROWS,
                 "expected_columns": EXPECTED_COLUMNS, "column_map": {
                     "row_type": "a", "timestamp_epoch": "b", "session_date": "c", "open": "d",
                     "high": "e", "low": "f", "close": "g", "volume": "h", "quality_flags": "i",
                     "join_status": "j"}, "row_type_values": {"option": "OPTION", "spot": "SPOT"}},
                m, {"dataset_sha256": EXPECTED_DATASET_SHA256, "exchange": "NSE",
                    "calendar_source": "fixture", "valid_sessions": ["2026-01-01"]},
                {"dataset_sha256": EXPECTED_DATASET_SHA256, "holdout_boundary_found": False})

    def test_unsorted_or_duplicate_calendar_rejected(self):
        common = {"dataset_sha256": EXPECTED_DATASET_SHA256}
        im = {"dataset_sha256": EXPECTED_DATASET_SHA256, "expected_rows": EXPECTED_ROWS,
              "expected_columns": EXPECTED_COLUMNS,
              "column_map": {"row_type": "a", "timestamp_epoch": "b", "session_date": "c", "open": "d",
                             "high": "e", "low": "f", "close": "g", "volume": "h", "quality_flags": "i",
                             "join_status": "j"},
              "row_type_values": {"option": "OPTION", "spot": "SPOT"}}
        sm = {"dataset_sha256": EXPECTED_DATASET_SHA256, "cache_only": True, "source_vintages": [{"family":"SPOT","pit_proven":True}]}
        for sessions in (["2026-01-02", "2026-01-01"], ["2026-01-01", "2026-01-01"]):
            cm = {"dataset_sha256": EXPECTED_DATASET_SHA256, "exchange": "NSE", "calendar_source": "fixture", "valid_sessions": sessions}
            with self.assertRaisesRegex(ValueError, "NSE_CALENDAR_NOT_UNIQUE_SORTED"):
                validate_input_manifests(im, sm, cm, {"dataset_sha256": EXPECTED_DATASET_SHA256, "holdout_boundary_found": False})

    def test_authorization_rejects_any_downstream_permission(self):
        paths = {}
        auth = {"gate_id":"MODELING_READINESS_FEASIBILITY_RUN_R5", "verdict":"PASS_WITH_SCOPED_RESTRICTIONS",
                "allowed_scope":"one bounded metadata-only MR-0 to MR-5 feasibility audit", "one_use":True,
                "permissions": {"model_fitting":False, "model_tuning":False, "prediction_scoring":False,
                               "holdout_observation_access":True, "new_source_requests":False,
                               "strategy_pnl":False, "trading":False},
                "reviewed_blobs": {}, "decoded_dataset_sha256": EXPECTED_DATASET_SHA256,
                "max_dataset_rows": EXPECTED_ROWS, "max_dataset_columns": EXPECTED_COLUMNS, "input_sha256": {}}
        with self.assertRaisesRegex(ValueError, "AUTH_DOWNSTREAM_PERMISSION_NOT_CLOSED"):
            validate_execution_authorization(auth, paths)

    def test_report_schema_subset_rejects_unknown_properties_and_bad_hash(self):
        schema = {"type":"object", "additionalProperties":False, "required":["dataset_sha256","count"],
                  "properties":{"dataset_sha256":{"type":"string","pattern":"^[a-f0-9]{64}$"},
                               "count":{"type":"integer","minimum":0}}}
        valid = {"dataset_sha256":EXPECTED_DATASET_SHA256,"count":0}
        _report_schema_subset_validate(valid, schema)
        with self.assertRaisesRegex(ValueError, "REPORT_SCHEMA_EXTRA_PROPERTY"):
            _report_schema_subset_validate({**valid,"price":22000}, schema)
        with self.assertRaisesRegex(ValueError, "REPORT_SCHEMA_PATTERN"):
            _report_schema_subset_validate({**valid,"dataset_sha256":"not-a-hash"}, schema)
        with self.assertRaisesRegex(ValueError, "REPORT_SCHEMA_MINIMUM"):
            _report_schema_subset_validate({**valid,"count":-1}, schema)

    def test_report_blocked_output_has_no_price_fields(self):
        report = build_blocked_report({"dataset_sha256":EXPECTED_DATASET_SHA256}, "BLOCKED_HOLDOUT_PROOF")
        self.assertNotIn("price", report)
        self.assertEqual(report["target_horizons"]["1"]["eligible_origins"], 0)
        self.assertEqual(report["gate_status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
