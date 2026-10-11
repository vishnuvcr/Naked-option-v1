from __future__ import annotations

import gzip
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import diagnose_nifty_1m_value_anomalies as diagnostic
from test_audit_nifty_1m_composite_values import COLUMNS, base_row


def write_rows(root: pathlib.Path, option_rows: list[dict[str, str]],
               spot_rows: list[dict[str, str]]) -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "nifty_1m_composite_2024-01.csv.gz"
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        import csv
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(option_rows + spot_rows)
    return path


class ValueAnomalyDiagnosticTests(unittest.TestCase):
    def test_finds_ohlc_and_negative_volume_without_emitting_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "private-option-request")
            option["option_high"] = "98"
            option["option_volume"] = "-4"
            option["nifty_high"] = "21000"
            option["nifty_close"] = "21002"
            option["nifty_volume"] = "-7"
            spot = base_row("SPOT", "private-spot-request")
            spot["nifty_high"] = "21000"
            spot["nifty_close"] = "21002"
            spot["nifty_volume"] = "-7"
            write_rows(root, [option], [spot])
            report = diagnostic.analyze(root)
            self.assertEqual(report["status"], "DIAGNOSTIC_COMPLETE")
            self.assertGreater(report["issue_occurrence_counts"].get("OPTION_OHLC:HIGH_BELOW_CLOSE", 0), 0)
            self.assertEqual(report["issue_occurrence_counts"].get("OPTION_VOLUME:NEGATIVE_VOLUME"), 1)
            self.assertEqual(report["issue_occurrence_counts"].get("MATCHED_NIFTY_VOLUME:NEGATIVE_VOLUME"), 1)
            self.assertEqual(report["issue_occurrence_counts"].get("SPOT_VOLUME:NEGATIVE_VOLUME"), 1)
            self.assertEqual(report["distinct_timestamp_diagnostics"]["matched_option_epochs_with_invalid_joined_nifty_ohlc"], 1)
            encoded = json.dumps(report)
            for value in ("21000", "21002", "-7", "-4", "private-option-request", "private-spot-request"):
                self.assertNotIn(value, encoded)
            self.assertTrue(report["flagged_row_fingerprints"])
            self.assertFalse(report["permissions"]["source_rows_modified"])

    def test_unmatched_option_missing_underlying_is_not_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["spot_join_status"] = "NO_EXACT_TIMESTAMP_SPOT_MATCH"
            for name in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"):
                option[name] = ""
            write_rows(root, [option], [])
            report = diagnostic.analyze(root)
            self.assertEqual(report["row_counts"]["unmatched_option_rows"], 1)
            self.assertNotIn("MATCHED_NIFTY_OHLC:OHLC_MISSING_OR_NONFINITE", report["issue_occurrence_counts"])

    def test_missing_decrypted_parts_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                diagnostic.analyze(pathlib.Path(tmp))


if __name__ == "__main__":
    unittest.main()
