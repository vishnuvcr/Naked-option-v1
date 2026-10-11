import json
import tempfile
import unittest
from pathlib import Path

from publish_preflight_receipt import ALLOWED_REPORT_KEYS, build_receipt


class PublishReceiptTests(unittest.TestCase):
    def metadata(self):
        return {
            "id": 123, "name": "Phase 07 Exact-File Offline Preflight Audit",
            "head_sha": "a" * 40, "head_branch": "phase-07-developer",
            "conclusion": "success", "status": "completed", "created_at": "2026-10-11T12:00:00Z",
        }

    def report(self, **updates):
        value = {
            "status": "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS",
            "file_name": "nifty_repaired_composite_2021-10_to_2026-10.csv.gz", "file_size_bytes": 123,
            "sha256": "b" * 64, "gzip_integrity": "PASS",
            "data_rows": 8999865, "columns": 47, "column_names": ["timestamp_epoch"],
            "recognized_timestamp_column": "timestamp_epoch",
            "timestamp_epoch_min": 1, "timestamp_epoch_max": 2,
            "timestamp_parse_errors": 0, "recognized_row_type_counts": {},
            "null_or_blank_counts_by_column": {}, "row_width_errors": 0,
            "duplicate_key_check": "PASS", "duplicate_key_fields": [],
            "duplicate_key_count": 0, "incomplete_composite_key_rows": 0,
            "key_group_row_counts": {}, "limitations": ["metadata only"],
        }
        value.update(updates)
        return value

    def test_no_report_creates_explicit_receipt_not_success(self):
        receipt = build_receipt(self.metadata(), None)
        self.assertEqual(receipt["receipt_status"], "NO_SANITIZED_REPORT")
        self.assertFalse(receipt["report_available"])
        self.assertIsNone(receipt["report"])

    def test_expected_metadata_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "report.json"
            path.write_text(json.dumps(self.report()), encoding="utf-8")
            receipt = build_receipt(self.metadata(), path)
            self.assertEqual(receipt["receipt_status"], "REPORT_PRESENT_PASS")
            self.assertTrue(receipt["report_available"])
            self.assertEqual(receipt["report"]["sha256"], "b" * 64)

    def test_unexpected_raw_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "report.json"
            path.write_text(json.dumps(self.report(raw_rows=[["raw", "price"]])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REPORT_CONTAINS_UNAPPROVED_FIELDS"):
                build_receipt(self.metadata(), path)

    def test_wrong_row_or_column_count_is_never_labeled_clean(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "report.json"
            path.write_text(json.dumps(self.report(data_rows=10)), encoding="utf-8")
            receipt = build_receipt(self.metadata(), path)
            self.assertEqual(receipt["receipt_status"], "REPORT_PRESENT_WITH_EXPECTATION_MISMATCH")

    def test_raw_value_hidden_in_allowed_text_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "report.json"
            value = self.report(limitations=["raw option price: 123.45"])
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REPORT_LIMITATIONS_INVALID"):
                build_receipt(self.metadata(), path)

    def test_invalid_hash_or_count_types_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "report.json"
            path.write_text(json.dumps(self.report(sha256="not-a-hash")), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REPORT_SHA256_INVALID"):
                build_receipt(self.metadata(), path)

    def test_report_without_required_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "report.json"
            path.write_text(json.dumps({"status": "PASS", "data_rows": 8999865, "columns": 47}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REPORT_REQUIRED_METADATA_MISSING"):
                build_receipt(self.metadata(), path)


if __name__ == "__main__":
    unittest.main()
