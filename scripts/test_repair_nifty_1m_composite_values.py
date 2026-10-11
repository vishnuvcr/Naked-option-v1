from __future__ import annotations

import csv
import gzip
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import repair_nifty_1m_composite_values as repair
import validate_repaired_nifty_1m_composite as repaired_validator
from decrypt_nifty_1m_composite import decrypt_bytes, derive_key
from test_audit_nifty_1m_composite_values import COLUMNS, base_row, write_fixture

SECRET = "synthetic-test-secret-value-only"


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class DerivedDatasetRepairTests(unittest.TestCase):
    def test_exact_epoch_reconciles_join_and_masks_negative_option_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "input"
            option = base_row("OPTION", "private-option-request")
            option["nifty_open"] = "20990"
            option["nifty_high"] = "20991"
            option["nifty_low"] = "20980"
            option["nifty_close"] = "20985"
            option["nifty_volume"] = "-5"
            option["option_volume"] = "-4"
            spot = base_row("SPOT", "private-spot-request")
            write_fixture(root, [option], [spot])
            out = pathlib.Path(tmp) / "derived-encrypted"
            report_path = pathlib.Path(tmp) / "repair-report.json"
            report = repair.repair_dataset(root, out, report_path, SECRET)
            self.assertEqual(report["status"], "DERIVED_REPAIR_COMPLETE")
            self.assertEqual(report["row_counts"]["rows_deleted"], 0)
            self.assertGreater(report["repair_counts"].get("joined_nifty_fields_reconciled", 0), 0)
            self.assertEqual(report["repair_counts"].get("option_rows_with_invalid_volume_masked"), 1)
            manifest = json.loads((out / "dataset_manifest.json").read_text(encoding="utf-8"))
            part = manifest["parts"][0]
            encrypted_path = out / part["file"]
            self.assertTrue(encrypted_path.is_file())
            self.assertFalse((out / part["file"].removesuffix(".enc")).exists())
            self.assertEqual(repair.sha256_bytes(encrypted_path.read_bytes()), part["encrypted_sha256"])
            plaintext_gzip = decrypt_bytes(encrypted_path.read_bytes(), derive_key(SECRET))
            temp_plain = pathlib.Path(tmp) / "decrypted.csv.gz"
            temp_plain.write_bytes(plaintext_gzip)
            rows = read_rows(temp_plain)
            option_out = next(row for row in rows if row["row_type"] == "OPTION")
            spot_out = next(row for row in rows if row["row_type"] == "SPOT")
            for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"):
                self.assertEqual(option_out[field], spot_out[field])
            self.assertEqual(option_out["option_volume"], "")
            self.assertIn("REPAIR_JOINED_NIFTY_FROM_EXACT_SPOT", option_out["data_quality_flags"])
            self.assertNotIn("20990", report_path.read_text(encoding="utf-8"))
            self.assertNotIn("private-option-request", report_path.read_text(encoding="utf-8"))

    def test_invalid_spot_bar_masks_joined_ohlc_and_volume_without_fabrication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "input"
            option = base_row("OPTION", "request-opt")
            option["nifty_high"] = "1"
            option["nifty_volume"] = "-1"
            spot = base_row("SPOT", "request-spot")
            spot["nifty_high"] = "1"
            spot["nifty_volume"] = "-1"
            write_fixture(root, [option], [spot])
            out = pathlib.Path(tmp) / "derived"
            report = repair.repair_dataset(root, out, pathlib.Path(tmp) / "report.json", SECRET)
            self.assertEqual(report["repair_counts"].get("spot_rows_with_invalid_ohlc_masked"), 1)
            self.assertEqual(report["repair_counts"].get("spot_rows_with_invalid_volume_masked"), 1)
            manifest = json.loads((out / "dataset_manifest.json").read_text(encoding="utf-8"))
            plain = repair.decrypt_bytes if hasattr(repair, "decrypt_bytes") else decrypt_bytes
            payload = plain((out / manifest["parts"][0]["file"]).read_bytes(), derive_key(SECRET))
            tmp_gz = pathlib.Path(tmp) / "check.csv.gz"
            tmp_gz.write_bytes(payload)
            rows = read_rows(tmp_gz)
            spot_out = next(row for row in rows if row["row_type"] == "SPOT")
            option_out = next(row for row in rows if row["row_type"] == "OPTION")
            for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"):
                self.assertEqual(spot_out[field], "")
                self.assertEqual(option_out[field], "")

    def test_unmatched_option_remains_unmatched_and_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "input"
            option = base_row("OPTION", "request-opt")
            option["session_date"] = "2024-01-06"
            option["spot_join_status"] = "NO_EXACT_TIMESTAMP_SPOT_MATCH"
            for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"):
                option[field] = ""
            write_fixture(root, [option], [])
            manifest_path = root / "dataset_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["dataset_summary"]["spot_join_matched"] = 0
            manifest["dataset_summary"]["spot_join_missing"] = 1
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            out = pathlib.Path(tmp) / "derived"
            report = repair.repair_dataset(root, out, pathlib.Path(tmp) / "report.json", SECRET)
            self.assertEqual(report["repair_counts"].get("unmatched_option_rows_preserved"), 1)
            self.assertEqual(report["repair_counts"].get("weekend_session_rows_flagged"), 1)
            manifest = json.loads((out / "dataset_manifest.json").read_text(encoding="utf-8"))
            payload = decrypt_bytes((out / manifest["parts"][0]["file"]).read_bytes(), derive_key(SECRET))
            gz_path = pathlib.Path(tmp) / "check.csv.gz"
            gz_path.write_bytes(payload)
            row = read_rows(gz_path)[0]
            self.assertEqual(row["spot_join_status"], "NO_EXACT_TIMESTAMP_SPOT_MATCH")
            self.assertTrue(all(row[field] == "" for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume")))

    def test_workflows_install_crypto_and_find_nested_manifest(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        repair_workflow = (root / ".github" / "workflows" / "phase-07-derived-dataset-repair.yml").read_text(encoding="utf-8")
        self.assertIn('root.rglob("dataset_manifest.json")', repair_workflow)
        self.assertIn("source_manifest_count_invalid", repair_workflow)
        self.assertIn("pip install -r requirements-composite.txt", repair_workflow)

    def test_source_and_output_directories_must_be_disjoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            with self.assertRaises(ValueError):
                repair.repair_dataset(root, root, root / "report.json", SECRET)



    def test_independent_post_repair_validator_checks_exact_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "input"
            option = base_row("OPTION", "request-opt")
            spot = base_row("SPOT", "request-spot")
            write_fixture(root, [option], [spot])
            manifest_path = root / "dataset_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["dataset_id"] = "synthetic_DERIVED_REPAIR_V1"
            manifest["derived_from"] = {"parent_dataset_id": "synthetic-parent"}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report_path = pathlib.Path(tmp) / "safe-report.json"
            result = repaired_validator.audit(root, report_path, pathlib.Path(tmp) / "audit.sqlite")
            self.assertEqual(result["status"], "PASS_WITH_COVERAGE_RESTRICTIONS")
            self.assertEqual(result["row_counts"]["total"], 2)
            self.assertEqual(result["join_counts"]["exact_join_field_mismatches"], 0)
            self.assertNotIn("21000", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
