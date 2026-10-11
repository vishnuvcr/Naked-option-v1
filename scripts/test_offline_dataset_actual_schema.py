import csv
import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path

from offline_dataset_preflight import run


ACTUAL_HEADER = [
    "timestamp_epoch", "row_type", "underlying", "source_request_id",
    "expiry_flag", "expiry_code", "requested_relative_strike",
    "returned_strike", "option_type",
] + [f"c{i}" for i in range(38)]


def spot_row(epoch="1700000000"):
    return [epoch, "SPOT", "NIFTY", "", "", "", "", "", ""] + [""] * 38


def option_row(epoch="1700000000", request_id="req-A", relative_strike="ATM",
               returned_strike="25000", option_type="CE", row_type="OPTION"):
    return [
        epoch, row_type, "NIFTY", request_id, "WEEK", "2026-10-29",
        relative_strike, returned_strike, option_type,
    ] + [""] * 38


def write_gzip(path, header, rows):
    with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ActualCompositeSchemaTests(unittest.TestCase):
    def test_actual_schema_uses_canonical_option_identity_and_separate_spot_epoch_key(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "actual.csv.gz"
            # OPTION A is repeated with harmless textual timestamp/case/returned-strike
            # variations. OPTION B shares the returned strike and timestamp, but it was
            # a distinct request/relative-strike selector and must not be a false duplicate.
            rows = [
                spot_row(),
                spot_row("1700000000.0"),
                option_row(),
                option_row("1700000000.0", "req-A", "ATM", "25000.0", "ce", "option"),
                option_row("1700000000", "req-B", "ATM+1", "25000", "CE"),
            ]
            digest = write_gzip(path, ACTUAL_HEADER, rows)
            report = run(path, Path(td) / "report.json", digest, len(rows), 47)

            # One repeated SPOT timestamp and one repeated canonical OPTION identity.
            # req-B/ATM+1 is not collapsed into req-A/ATM merely because returned strike
            # and timestamp are the same.
            self.assertEqual(report["duplicate_key_count"], 2)
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")
            self.assertEqual(report["incomplete_composite_key_rows"], 0)
            self.assertEqual(report["key_group_row_counts"]["0"]["fields"], [
                "timestamp_epoch", "row_type", "source_request_id", "expiry_flag",
                "expiry_code", "requested_relative_strike", "option_type",
            ])
            self.assertEqual(report["key_group_row_counts"]["0"]["rows_assigned"], 3)
            self.assertEqual(report["key_group_row_counts"]["1"]["fields"], ["timestamp_epoch"])
            self.assertEqual(report["key_group_row_counts"]["1"]["rows_assigned"], 2)

    def test_actual_schema_flags_incomplete_option_identity_without_spot_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "actual.csv.gz"
            incomplete = option_row(request_id="")
            digest = write_gzip(path, ACTUAL_HEADER, [incomplete, spot_row()])
            report = run(path, Path(td) / "report.json", digest, 2, 47)

            self.assertEqual(report["incomplete_composite_key_rows"], 1)
            self.assertEqual(report["key_group_row_counts"]["1"]["rows_assigned"], 1)
            self.assertEqual(report["duplicate_key_count"], 0)
            self.assertEqual(report["status"], "PREFLIGHT_REVIEW_INCOMPLETE_COMPOSITE_KEYS")

    def test_canonical_option_duplicate_ignores_returned_strike_but_not_request_identity(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "canonical-key.csv.gz"
            rows = [
                option_row("1700000000", "req-A", "ATM", "25000", "CE"),
                option_row("1700000000.0", "req-A", "ATM", "25000.0", "ce", "option"),
                option_row("1700000000", "req-B", "ATM+1", "25000", "CE"),
            ]
            digest = write_gzip(path, ACTUAL_HEADER, rows)
            report = run(path, Path(td) / "report.json", digest, len(rows), 47)

            self.assertEqual(report["duplicate_key_count"], 1)
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")
            self.assertEqual(report["incomplete_composite_key_rows"], 0)

    def test_duplicate_detection_across_10000_row_batch_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            rows = [
                spot_row(str(1700000000 + 60 * i))
                for i in range(10_000)
            ]
            rows.append(spot_row())
            path = Path(td) / "batch-boundary.csv.gz"
            digest = write_gzip(path, ACTUAL_HEADER, rows)
            report = run(path, Path(td) / "report.json", digest, len(rows), 47)

            self.assertEqual(report["duplicate_key_count"], 1)
            self.assertEqual(report["status"], "PREFLIGHT_FAIL_DUPLICATE_KEYS")
            self.assertEqual(report["incomplete_composite_key_rows"], 0)


if __name__ == "__main__":
    unittest.main()
