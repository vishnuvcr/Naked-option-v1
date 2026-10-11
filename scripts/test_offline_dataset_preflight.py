import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from offline_dataset_preflight import run


KEY_HEADER = ["timestamp_epoch", "instrument_type", "symbol", "expiry", "strike", "option_type"] + [f"c{i}" for i in range(41)]
GENERIC_HEADER = [f"c{i}" for i in range(47)]


class PreflightTests(unittest.TestCase):
    def make_file(self, root, rows, header=None):
        header = header or GENERIC_HEADER
        path = Path(root) / "tiny.csv.gz"
        with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(rows)
        return path

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_passes_fixture_reports_metadata_only_and_creates_nested_report_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            header = ["timestamp_epoch", "instrument_type", "symbol", "expiry", "strike", "option_type", "close"] + [f"c{i}" for i in range(40)]
            rows = [
                ["1700000000", "spot", "NIFTY", "NA", "0", "SPOT", "12345.67"] + [""] * 40,
                ["1700000060", "spot", "NIFTY", "NA", "0", "SPOT", "12345.67"] + [""] * 40,
            ]
            path = self.make_file(td, rows, header)
            out = root / "nested" / "reports" / "report.json"
            report = run(path, out, self.digest(path), 2, 47)
            self.assertEqual(report["data_rows"], 2)
            self.assertEqual(report["gzip_integrity"], "PASS")
            self.assertEqual(report["timestamp_epoch_min"], 1700000000)
            self.assertEqual(report["timestamp_epoch_max"], 1700000060)
            self.assertEqual(report["duplicate_key_count"], 0)
            # No row values, symbols, or source records are included in the report.
            self.assertNotIn("NIFTY", out.read_text(encoding="utf-8"))
            self.assertNotIn("12345.67", out.read_text(encoding="utf-8"))
            self.assertFalse(Path(str(out) + ".sqlite.tmp").exists())

    def test_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_file(td, [["x"] * 47])
            with self.assertRaisesRegex(ValueError, "INPUT_SHA256_MISMATCH"):
                run(path, Path(td) / "r.json", "0" * 64, 1, 47)

    def test_row_count_mismatch_fails_closed_and_cleans_sqlite(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_file(td, [["1", "spot", "NIFTY", "NA", "0", "SPOT"] + [""] * 41], KEY_HEADER)
            report = Path(td) / "r.json"
            with self.assertRaisesRegex(ValueError, "ROW_COUNT_MISMATCH"):
                run(path, report, self.digest(path), 2, 47)
            self.assertFalse(Path(str(report) + ".sqlite.tmp").exists())

    def test_duplicate_header_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            header = ["same", "same"] + [f"c{i}" for i in range(45)]
            path = self.make_file(td, [["x"] * 47], header)
            with self.assertRaisesRegex(ValueError, "DUPLICATE_COLUMN_NAMES"):
                run(path, Path(td) / "r.json", self.digest(path), 1, 47)

    def test_bad_column_count_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_file(td, [["x"] * 46], [f"c{i}" for i in range(46)])
            with self.assertRaisesRegex(ValueError, "COLUMN_COUNT_MISMATCH"):
                run(path, Path(td) / "r.json", self.digest(path), 1, 47)

    def test_malformed_row_width_fails_closed_and_cleans_sqlite(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_file(td, [["1", "spot", "NIFTY", "NA", "0", "SPOT"] + [""] * 40], KEY_HEADER)
            report = Path(td) / "r.json"
            with self.assertRaisesRegex(ValueError, "ROW_WIDTH_MISMATCH"):
                run(path, report, self.digest(path), 1, 47)
            self.assertFalse(Path(str(report) + ".sqlite.tmp").exists())

    def test_duplicate_composite_key_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            row = ["1700000000", "option", "NIFTY", "2026-10-29", "25000", "CE"] + ["x"] * 41
            path = self.make_file(td, [row, row], KEY_HEADER)
            report = run(path, Path(td) / "r.json", self.digest(path), 2, 47)
            self.assertEqual(report["duplicate_key_check"], "FAIL_DUPLICATE_KEYS_FOUND")
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")
            self.assertEqual(report["duplicate_key_count"], 1)

    def test_equivalent_epoch_encodings_are_canonicalized_for_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as td:
            row_a = ["1700000000", "option", "NIFTY", "2026-10-29", "25000", "CE"] + ["x"] * 41
            row_b = ["1700000000.0", "option", "NIFTY", "2026-10-29", "25000", "CE"] + ["x"] * 41
            path = self.make_file(td, [row_a, row_b], KEY_HEADER)
            report = run(path, Path(td) / "r.json", self.digest(path), 2, 47)
            self.assertEqual(report["duplicate_key_count"], 1)
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")

    def test_spot_rows_fall_back_to_security_id_key_when_option_fields_are_blank(self):
        with tempfile.TemporaryDirectory() as td:
            header = ["timestamp_epoch", "instrument_type", "symbol", "expiry", "strike", "option_type", "security_id"] + [f"c{i}" for i in range(40)]
            row = ["1700000000", "spot", "NIFTY", "", "", "", "13"] + [""] * 40
            path = self.make_file(td, [row, row], header)
            report = run(path, Path(td) / "r.json", self.digest(path), 2, 47)
            self.assertEqual(report["duplicate_key_count"], 1)
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")
            self.assertEqual(report["incomplete_composite_key_rows"], 0)

    def test_missing_recognized_key_fields_is_not_estimable_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_file(td, [["x"] * 47], GENERIC_HEADER)
            report = run(path, Path(td) / "r.json", self.digest(path), 1, 47)
            self.assertEqual(report["duplicate_key_check"], "NOT_ESTIMABLE_NO_RECOGNIZED_COMPOSITE_KEY")
            self.assertEqual(report["status"], "PREFLIGHT_REVIEW_DUPLICATE_CHECK_NOT_ESTIMABLE")
            self.assertIsNone(report["duplicate_key_count"])

    def test_incomplete_key_rows_are_not_counted_as_unique_or_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            row = ["1700000000", "option", "", "2026-10-29", "25000", "CE"] + ["x"] * 41
            path = self.make_file(td, [row, row], KEY_HEADER)
            report = run(path, Path(td) / "r.json", self.digest(path), 2, 47)
            self.assertEqual(report["duplicate_key_count"], 0)
            self.assertEqual(report["incomplete_composite_key_rows"], 2)
            self.assertEqual(report["duplicate_key_check"], "PARTIAL_INCOMPLETE_COMPOSITE_KEYS")
            self.assertEqual(report["status"], "PREFLIGHT_REVIEW_INCOMPLETE_COMPOSITE_KEYS")

    def test_corrupt_gzip_trailer_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_file(td, [["x"] * 47])
            data = bytearray(path.read_bytes())
            data[-5] ^= 0xFF
            path.write_bytes(data)
            with self.assertRaises((OSError, EOFError, gzip.BadGzipFile)):
                run(path, Path(td) / "r.json", self.digest(path), 1, 47)

    def test_truncated_gzip_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_file(td, [["x"] * 47])
            path.write_bytes(path.read_bytes()[:-8])
            with self.assertRaises((OSError, EOFError, gzip.BadGzipFile)):
                run(path, Path(td) / "r.json", self.digest(path), 1, 47)

    def test_timestamp_parse_errors_are_reported(self):
        with tempfile.TemporaryDirectory() as td:
            rows = [
                ["bad-time", "spot", "NIFTY", "NA", "0", "SPOT"] + [""] * 41,
                ["1700000000", "spot", "NIFTY", "NA", "0", "SPOT"] + [""] * 41,
            ]
            path = self.make_file(td, rows, KEY_HEADER)
            report = run(path, Path(td) / "r.json", self.digest(path), 2, 47)
            self.assertEqual(report["timestamp_parse_errors"], 1)
            self.assertEqual(report["status"], "PREFLIGHT_REVIEW_TIMESTAMP_PARSE_ERRORS")


if __name__ == "__main__":
    unittest.main()
