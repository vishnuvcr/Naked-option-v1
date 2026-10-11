import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.modeling_readiness_feasibility_run import (
    EXPECTED_DATASET_SHA256, EXPECTED_DATASET_ID, EXPECTED_ROWS, EXPECTED_COLUMNS,
    git_blob_sha1, validate_execution_authorization, validate_input_manifests,
    build_blocked_report, sanitize_report, _report_schema_subset_validate, _scan_prefix,
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
            "timestamp_semantics": "BAR_END", "official_close_linkage_proven": True,
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

    def test_real_schema_validates_blocked_report_and_nested_targets(self):
        schema_path = Path("research/gates/MODELING_READINESS_FEASIBILITY_REPORT_SCHEMA_R5_2026-10-11.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        report = build_blocked_report({"dataset_sha256": EXPECTED_DATASET_SHA256}, "BLOCKED_HOLDOUT_PROOF")
        self.assertEqual(sanitize_report(report, schema)["gate_status"], "BLOCKED")
        bad = json.loads(json.dumps(report))
        bad["target_horizons"]["1"]["price"] = 22000
        with self.assertRaisesRegex(ValueError, "REPORT_SCHEMA_EXTRA_PROPERTY"):
            sanitize_report(bad, schema)

    def test_prefix_scan_stops_at_exact_holdout_byte_boundary(self):
        header = ["type","ts","date","o","h","l","c","v","q","j"] + [f"x{i}" for i in range(37)]
        rows = []
        observations = [
            ("OPTION", 1000, "2026-01-01", "", "", "", "", "", "", "MATCHED"),
            ("SPOT",   1000, "2026-01-01", "100","101","99","100","10","","MATCHED"),
            ("OPTION", 2000, "2026-01-02", "", "", "", "", "", "", "MATCHED"),
            ("SPOT",   2000, "2026-01-02", "100","103","99","102","10","","MATCHED"),
            ("OPTION", 3000, "2026-01-05", "", "", "", "", "", "", "UNMATCHED"),
            ("SPOT",   3000, "2026-01-05", "99","100","98","99","10","","MATCHED"),
        ]
        for record in observations:
            rows.append(list(record) + [""] * 37)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic.csv"
            from io import StringIO
            buffer = StringIO()
            writer = csv.writer(buffer, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
            prefix_bytes = buffer.getvalue().encode("utf-8")
            # Deliberately malformed row after the boundary must never be parsed.
            path.write_bytes(prefix_bytes + b'"bad"unexpected,holdout,row\n')
            input_manifest = {
                "column_map": {"row_type":"type","timestamp_epoch":"ts","session_date":"date","open":"o",
                               "high":"h","low":"l","close":"c","volume":"v","quality_flags":"q","join_status":"j"},
                "row_type_values": {"option":"OPTION","spot":"SPOT"}
            }
            source_manifest = {"feature_families":[
                {"family":"SPOT_OHLCV","row_type":"SPOT","columns":["c"],"pit_proven":True,"join_validity_proven":True}
            ]}
            calendar_manifest = {"valid_sessions":["2026-01-01","2026-01-02","2026-01-05","2026-01-06"]}
            split_manifest = {"train_end_session":"2026-01-01","validation_end_session":"2026-01-02",
                              "holdout_start_session":"2026-01-06","pre_holdout_prefix_rows":6}
            report = _scan_prefix(path, len(prefix_bytes), split_manifest, input_manifest, source_manifest, calendar_manifest)
            self.assertEqual(report["prefix_rows_scanned"], 6)
            self.assertEqual(report["option_rows_scanned"], 3)
            self.assertEqual(report["spot_rows_scanned"], 3)
            self.assertEqual(report["unmatched_option_rows"], 1)
            self.assertEqual(report["feature_families"]["SPOT_OHLCV"]["coverage_rate"], 1.0)
            schema = json.loads(Path("research/gates/MODELING_READINESS_FEASIBILITY_REPORT_SCHEMA_R5_2026-10-11.json").read_text(encoding="utf-8"))
            report.update({"source_manifest_sha256":"a"*64,"calendar_manifest_sha256":"b"*64,"split_manifest_sha256":"c"*64})
            self.assertEqual(sanitize_report(report, schema)["gate_status"], "PASS_WITH_RESTRICTIONS")


    def test_close_linkage_and_timestamp_semantics_fail_closed(self):
        input_manifest = {
            "dataset_sha256": EXPECTED_DATASET_SHA256, "expected_rows": EXPECTED_ROWS,
            "expected_columns": EXPECTED_COLUMNS,
            "column_map": {"row_type":"a","timestamp_epoch":"b","session_date":"c","open":"d","high":"e",
                           "low":"f","close":"g","volume":"h","quality_flags":"i","join_status":"j"},
            "row_type_values": {"option":"OPTION","spot":"SPOT"},
        }
        sources = {"dataset_sha256": EXPECTED_DATASET_SHA256, "cache_only":True,
                   "source_vintages":[{"family":"SPOT_OHLCV","pit_proven":True}]}
        calendar = {"dataset_sha256":EXPECTED_DATASET_SHA256,"exchange":"NSE","calendar_source":"fixture",
                    "valid_sessions":["2026-01-01","2026-01-02"]}
        split = {"dataset_sha256":EXPECTED_DATASET_SHA256,"holdout_boundary_found":False}
        self.assertEqual(validate_input_manifests(input_manifest,sources,calendar,split),(False,"CANDLE_SEMANTICS_UNPROVEN"))
        input_manifest["timestamp_semantics"] = "BAR_END"
        self.assertEqual(validate_input_manifests(input_manifest,sources,calendar,split),(False,"CLOSE_LINKAGE_UNPROVEN"))
        input_manifest["official_close_linkage_proven"] = True
        self.assertEqual(validate_input_manifests(input_manifest,sources,calendar,split),(False,"BLOCKED_HOLDOUT_PROOF"))

    def test_split_requires_endpoint_purge_and_minimum_origins(self):
        input_manifest = {
            "dataset_sha256": EXPECTED_DATASET_SHA256, "expected_rows": EXPECTED_ROWS,
            "expected_columns": EXPECTED_COLUMNS,
            "column_map": {"row_type":"a","timestamp_epoch":"b","session_date":"c","open":"d","high":"e",
                           "low":"f","close":"g","volume":"h","quality_flags":"i","join_status":"j"},
            "row_type_values": {"option":"OPTION","spot":"SPOT"},
            "timestamp_semantics":"BAR_END","official_close_linkage_proven":True,
        }
        sources = {"dataset_sha256":EXPECTED_DATASET_SHA256,"cache_only":True,
                   "source_vintages":[{"family":"SPOT_OHLCV","pit_proven":True}]}
        calendar = {"dataset_sha256":EXPECTED_DATASET_SHA256,"exchange":"NSE","calendar_source":"fixture",
                    "valid_sessions":["2026-01-01","2026-01-02","2026-01-05"]}
        split = {
            "dataset_sha256":EXPECTED_DATASET_SHA256,"holdout_boundary_found":True,
            "record_boundary_verified":True,"chronological_order_verified":True,
            "holdout_values_accessed":False,"holdout_labels_accessed":False,
            "holdout_excluded_from_feature_fit":True,"holdout_excluded_from_label_selection":True,
            "train_label_endpoint_purge_verified":False,"validation_label_endpoint_purge_verified":True,
            "train_eligible_origins":300,"train_eligible_origins_verified":300,
            "validation_eligible_origins":270,"validation_eligible_origins_verified":270,
            "common_validation_origins":270,"train_end_byte_offset":100,
            "validation_end_byte_offset":200,"holdout_start_byte_offset":300,
            "train_end_session":"2026-01-01","validation_end_session":"2026-01-02",
            "holdout_start_session":"2026-01-05"
        }
        self.assertEqual(validate_input_manifests(input_manifest,sources,calendar,split),(False,"BLOCKED_LEAKAGE"))
        split["train_label_endpoint_purge_verified"] = True
        split["train_eligible_origins"] = 251
        split["train_eligible_origins_verified"] = 251
        self.assertEqual(validate_input_manifests(input_manifest,sources,calendar,split),(False,"INCOMPLETE_NOT_PROMOTABLE"))

    def test_authorization_is_bound_to_single_actions_attempt(self):
        auth = {"gate_id":"MODELING_READINESS_FEASIBILITY_RUN_R5",
                "verdict":"PASS_WITH_SCOPED_RESTRICTIONS",
                "allowed_scope":"one bounded metadata-only MR-0 to MR-5 feasibility audit",
                "one_use":True,"authorized_workflow_run_id":"12345",
                "permissions":{"model_fitting":False,"model_tuning":False,"prediction_scoring":False,
                               "holdout_observation_access":False,"new_source_requests":False,"strategy_pnl":False,"trading":False},
                "reviewed_blobs":{},"decoded_dataset_sha256":EXPECTED_DATASET_SHA256,
                "max_dataset_rows":EXPECTED_ROWS,"max_dataset_columns":EXPECTED_COLUMNS,"input_sha256":{}}
        with tempfile.TemporaryDirectory() as temp:
            paths={}
            for name in ("scripts/modeling_readiness_feasibility_run.py","tests/test_modeling_readiness_feasibility_run.py",
                         "research/gates/MODELING_READINESS_FEASIBILITY_REPORT_SCHEMA_R5_2026-10-11.json",
                         ".github/workflows/phase-07-modeling-readiness-feasibility-synthetic.yml"):
                p=Path(temp)/name
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text("synthetic")
                paths[name]=p
                auth["reviewed_blobs"][name]=git_blob_sha1(p)
            auth["input_sha256"]={key:"a"*64 for key in ("dataset","input_manifest","source_manifest","calendar_manifest","split_manifest")}
            auth["input_sha256"]["dataset"]=EXPECTED_DATASET_SHA256
            import os
            old_run,old_attempt=os.environ.get("GITHUB_RUN_ID"),os.environ.get("GITHUB_RUN_ATTEMPT")
            try:
                os.environ["GITHUB_RUN_ID"]="12345"; os.environ["GITHUB_RUN_ATTEMPT"]="1"
                validate_execution_authorization(auth,paths)
                os.environ["GITHUB_RUN_ATTEMPT"]="2"
                with self.assertRaisesRegex(ValueError,"AUTH_WORKFLOW_RUN_OR_ATTEMPT_MISMATCH"):
                    validate_execution_authorization(auth,paths)
                os.environ["GITHUB_RUN_ID"]="99999"; os.environ["GITHUB_RUN_ATTEMPT"]="1"
                with self.assertRaisesRegex(ValueError,"AUTH_WORKFLOW_RUN_OR_ATTEMPT_MISMATCH"):
                    validate_execution_authorization(auth,paths)
            finally:
                if old_run is None: os.environ.pop("GITHUB_RUN_ID",None)
                else: os.environ["GITHUB_RUN_ID"]=old_run
                if old_attempt is None: os.environ.pop("GITHUB_RUN_ATTEMPT",None)
                else: os.environ["GITHUB_RUN_ATTEMPT"]=old_attempt

    def test_blocked_report_does_not_claim_cleanup_ran(self):
        report = build_blocked_report({"dataset_sha256":EXPECTED_DATASET_SHA256},"BLOCKED_HOLDOUT_PROOF")
        self.assertEqual(report["cleanup_status"],"NOT_RUN")

    def test_report_blocked_output_has_no_price_fields(self):
        report = build_blocked_report({"dataset_sha256":EXPECTED_DATASET_SHA256}, "BLOCKED_HOLDOUT_PROOF")
        self.assertNotIn("price", report)
        self.assertEqual(report["target_horizons"]["1"]["eligible_origins"], 0)
        self.assertEqual(report["gate_status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
