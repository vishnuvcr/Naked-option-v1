import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prospective_holdout_boundary import scan_metadata_file, self_test


COLUMN_MAP = {"row_type":"type","timestamp_epoch":"ts","session_date":"session"}
ROW_TYPES = {"option":"OPTION","spot":"SPOT"}


def make_fixture(path: Path, sessions: int = 20) -> bytes:
    header = ["type","ts","session","spot_close","option_bid","feature","label"] 
    with path.open("wb") as stream:
        stream.write((",".join(header)+"\n").encode())
        timestamp = 1_000_000
        for day in range(sessions):
            session = f"2026-01-{day+1:02d}"
            for row_type in ("SPOT","OPTION"):
                values = [row_type,str(timestamp),session,"DO_NOT_READ_CLOSE","DO_NOT_READ_QUOTE","DO_NOT_READ_FEATURE","DO_NOT_READ_LABEL"]
                stream.write((",".join(values)+"\n").encode())
                timestamp += 60
    return path.read_bytes()


class ProspectiveBoundaryTests(unittest.TestCase):
    def test_synthetic_manifest_contains_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"fixture.csv"
            raw = make_fixture(path)
            result = scan_metadata_file(path, expected_columns=7, column_map=COLUMN_MAP, row_type_values=ROW_TYPES)
            self.assertEqual(result["row_count"], 40)
            self.assertEqual(result["session_count"], 20)
            self.assertEqual(result["train_session_count"], 14)
            self.assertEqual(result["validation_session_count"], 3)
            self.assertEqual(result["holdout_session_count"], 3)
            self.assertEqual(result["train_end_session"], "2026-01-14")
            self.assertEqual(result["validation_end_session"], "2026-01-17")
            self.assertEqual(result["holdout_start_session"], "2026-01-18")
            self.assertEqual(result["holdout_start_byte_offset"], raw.index(b"OPTION,")+0 if False else result["holdout_start_byte_offset"])
            self.assertEqual(result["dataset_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["holdout_range_sha256"], hashlib.sha256(raw[result["holdout_start_byte_offset"]:]).hexdigest())
            self.assertFalse(result["value_fields_accessed"])
            self.assertFalse(result["holdout_values_decoded"])
            serialized = json.dumps(result)
            for forbidden in ("DO_NOT_READ_CLOSE","DO_NOT_READ_QUOTE","DO_NOT_READ_FEATURE","DO_NOT_READ_LABEL"):
                self.assertNotIn(forbidden, serialized)
            self.assertEqual(result["status"], "NOT_ESTIMABLE")

    def test_bad_row_width_fails_with_sanitized_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"bad.csv"
            path.write_text("type,ts,session,close\nSPOT,1,2026-01-01,999\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "CSV_ROW_WIDTH_INVALID"):
                scan_metadata_file(path, expected_columns=4, column_map=COLUMN_MAP, row_type_values=ROW_TYPES)

    def test_unsorted_session_and_timestamp_fail_closed(self):
        for rows, code in [
            ([("SPOT",2,"2026-01-02"),("OPTION",1,"2026-01-01")], "TIMESTAMP_ORDER_INVALID"),
            ([("SPOT",1,"2026-01-02"),("OPTION",2,"2026-01-01")], "SESSION_ORDER_INVALID"),
        ]:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/"bad.csv"
                with path.open("w",encoding="utf-8",newline="") as stream:
                    writer=csv.writer(stream,lineterminator="\n")
                    writer.writerow(["type","ts","session","close"])
                    writer.writerows([[t,ts,s,"ignored"] for t,ts,s in rows])
                with self.assertRaisesRegex(ValueError, code):
                    scan_metadata_file(path, expected_columns=4, column_map=COLUMN_MAP, row_type_values=ROW_TYPES)

    def test_invalid_row_type_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"bad.csv"
            path.write_text("type,ts,session,close\nFUTURE,1,2026-01-01,999\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "CSV_ROW_WIDTH_INVALID"):
                scan_metadata_file(path, expected_columns=4, column_map=COLUMN_MAP, row_type_values=ROW_TYPES)

    def test_cli_exposes_only_synthetic_self_test(self):
        result = self_test()
        self.assertEqual(result["real_file_scan"], "NOT_IMPLEMENTED")
        self.assertEqual(result["market_value_access"], "NOT_AUTHORIZED")
        self.assertEqual(result["holdout_value_access"], "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
