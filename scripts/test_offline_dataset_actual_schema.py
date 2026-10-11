import csv
import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path

from offline_dataset_preflight import run


class ActualCompositeSchemaTests(unittest.TestCase):
    def test_actual_schema_detects_duplicate_spot_and_option_keys(self):
        with tempfile.TemporaryDirectory() as td:
            header = ["timestamp_epoch", "row_type", "underlying", "expiry_code", "returned_strike", "option_type"] + [f"c{i}" for i in range(41)]
            spot = ["1700000000", "SPOT", "NIFTY", "", "", ""] + [""] * 41
            option = ["1700000000", "OPTION", "NIFTY", "2026-10-29", "25000", "CE"] + [""] * 41
            path = Path(td) / "actual.csv.gz"
            with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerows([spot, spot, option, option])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            report = run(path, Path(td) / "report.json", digest, 4, 47)
            self.assertEqual(report["duplicate_key_count"], 2)
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")
            self.assertEqual(report["incomplete_composite_key_rows"], 0)
            self.assertEqual(report["key_group_row_counts"]["0"]["fields"], ["timestamp_epoch", "row_type", "underlying", "expiry_code", "returned_strike", "option_type"])
            self.assertEqual(report["key_group_row_counts"]["1"]["fields"], ["timestamp_epoch", "row_type", "underlying"])

    def test_actual_schema_reports_incomplete_option_key(self):
        with tempfile.TemporaryDirectory() as td:
            header = ["timestamp_epoch", "row_type", "underlying", "expiry_code", "returned_strike", "option_type"] + [f"c{i}" for i in range(41)]
            row = ["1700000000", "OPTION", "NIFTY", "", "25000", "CE"] + [""] * 41
            path = Path(td) / "actual.csv.gz"
            with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerow(row)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            report = run(path, Path(td) / "report.json", digest, 1, 47)
            self.assertEqual(report["duplicate_key_check"], "PARTIAL_INCOMPLETE_COMPOSITE_KEYS")
            self.assertEqual(report["incomplete_composite_key_rows"], 1)


    def test_duplicate_detection_across_10000_row_batch_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            header = ["timestamp_epoch", "row_type", "underlying", "expiry_code", "returned_strike", "option_type"] + [f"c{i}" for i in range(41)]
            rows = []
            first = ["1700000000", "SPOT", "NIFTY", "", "", ""] + [""] * 41
            for i in range(10000):
                rows.append([str(1700000000 + 60 * i), "SPOT", "NIFTY", "", "", ""] + [""] * 41)
            rows.append(first)
            path = Path(td) / "batch-boundary.csv.gz"
            with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerows(rows)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            report = run(path, Path(td) / "report.json", digest, len(rows), 47)
            self.assertEqual(report["duplicate_key_count"], 1)
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")
            self.assertEqual(report["incomplete_composite_key_rows"], 0)


if __name__ == "__main__":
    unittest.main()
