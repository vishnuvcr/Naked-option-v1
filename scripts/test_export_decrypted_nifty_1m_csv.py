from __future__ import annotations

import csv
import gzip
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import export_decrypted_nifty_1m_csv as exporter


class DecryptedCsvExportTests(unittest.TestCase):
    def write_gzip(self, path: pathlib.Path, rows: list[list[str]]) -> None:
        with gzip.open(path, "wt", encoding="utf-8", newline="") as out:
            writer = csv.writer(out, lineterminator="\n")
            writer.writerows(rows)

    def test_merge_parts_streams_rows_and_writes_one_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            a = root / "a.csv.gz"
            b = root / "b.csv.gz"
            self.write_gzip(a, [["row_type", "value"], ["SPOT", "1"], ["OPTION", "2"]])
            self.write_gzip(b, [["row_type", "value"], ["SPOT", "3"]])
            out = root / "joined.csv"
            rows = exporter.merge_parts_to_csv([b, a], {"a.csv.gz": 2, "b.csv.gz": 1}, out, 3)
            self.assertEqual(rows, 3)
            with out.open(encoding="utf-8", newline="") as handle:
                parsed = list(csv.reader(handle))
            self.assertEqual(parsed, [
                ["row_type", "value"],
                ["SPOT", "1"], ["OPTION", "2"], ["SPOT", "3"]
            ])

    def test_rejects_mismatched_monthly_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            a = root / "a.csv.gz"
            b = root / "b.csv.gz"
            self.write_gzip(a, [["row_type", "value"], ["SPOT", "1"]])
            self.write_gzip(b, [["row_type", "different"], ["SPOT", "2"]])
            with self.assertRaisesRegex(ValueError, "monthly_csv_schema_mismatch"):
                exporter.merge_parts_to_csv([a, b], {"a.csv.gz": 1, "b.csv.gz": 1}, root / "bad.csv", 2)

    def test_rejects_monthly_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            a = root / "a.csv.gz"
            self.write_gzip(a, [["row_type", "value"], ["SPOT", "1"]])
            with self.assertRaisesRegex(ValueError, "monthly_csv_row_count_mismatch"):
                exporter.merge_parts_to_csv([a], {"a.csv.gz": 2}, root / "bad.csv", 1)

    def test_rejects_total_count_mismatch_and_removes_partial_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            a = root / "a.csv.gz"
            self.write_gzip(a, [["row_type", "value"], ["SPOT", "1"]])
            out = root / "bad.csv"
            with self.assertRaisesRegex(ValueError, "merged_csv_total_row_count_mismatch"):
                exporter.merge_parts_to_csv([a], {"a.csv.gz": 1}, out, 2)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
