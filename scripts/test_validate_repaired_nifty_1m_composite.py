from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import validate_repaired_nifty_1m_composite as validator
from test_audit_nifty_1m_composite_values import base_row, write_fixture


def write_derived_fixture(root: pathlib.Path, option_rows: list[dict[str, str]],
                          spot_rows: list[dict[str, str]]) -> None:
    write_fixture(root, option_rows, spot_rows)
    manifest_path = root / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dataset_id"] = "synthetic_DERIVED_REPAIR_V1"
    manifest["derived_from"] = {
        "parent_dataset_id": "synthetic-parent",
        "repair_policy": "EXACT_SPOT_EPOCH_RECONCILIATION_AND_INVALID_VALUE_MASKING_V1",
    }
    manifest["dataset_summary"]["spot_join_matched"] = sum(
        row.get("spot_join_status") == "EXACT_TIMESTAMP_MATCH" for row in option_rows
    )
    manifest["dataset_summary"]["spot_join_missing"] = sum(
        row.get("spot_join_status") == "NO_EXACT_TIMESTAMP_SPOT_MATCH" for row in option_rows
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


class RepairedDatasetValidationTests(unittest.TestCase):
    def run_audit(self, root: pathlib.Path) -> dict:
        output = root / "safe-report.json"
        db = root / "temp.sqlite"
        result = validator.audit(root, output, db)
        self.assertFalse(db.exists())
        return result

    def test_valid_exact_join_passes_and_reports_all_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_derived_fixture(root, [base_row("OPTION", "request-opt")],
                                  [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "PASS_WITH_COVERAGE_RESTRICTIONS")
            self.assertEqual(report["row_counts"]["total"], 2)
            self.assertEqual(report["row_counts"]["option"], 1)
            self.assertEqual(report["row_counts"]["spot"], 1)
            self.assertEqual(report["join_counts"]["exact_join_field_mismatches"], 0)
            self.assertFalse(report["sensitive_values_emitted"])
            encoded = json.dumps(report)
            self.assertNotIn("21000", encoded)
            self.assertNotIn("request-opt", encoded)

    def test_unmatched_rows_are_retained_blank_and_not_interpolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["spot_join_status"] = "NO_EXACT_TIMESTAMP_SPOT_MATCH"
            for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"):
                option[field] = ""
            write_derived_fixture(root, [option], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "PASS_WITH_COVERAGE_RESTRICTIONS")
            self.assertEqual(report["join_counts"]["unmatched_option_rows"], 1)
            self.assertEqual(report["join_counts"]["unmatched_rows_with_underlying_values"], 0)

    def test_invalid_nonblank_ohlc_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["option_high"] = "98"
            write_derived_fixture(root, [option], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertGreater(report["quality_counts"]["nonblank_invalid_ohlc_rows"], 0)

    def test_negative_nonblank_volume_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["option_volume"] = "-4"
            write_derived_fixture(root, [option], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["quality_counts"]["negative_nonblank_volumes"], 1)

    def test_exact_join_value_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["nifty_close"] = "20900"
            write_derived_fixture(root, [option], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["join_counts"]["exact_join_field_mismatches"], 1)

    def test_partial_ohlc_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["option_high"] = ""
            write_derived_fixture(root, [option], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["quality_counts"]["partial_ohlc_missing_rows"], 1)


if __name__ == "__main__":
    unittest.main()
