from __future__ import annotations

import csv
import gzip
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import diagnose_nifty_1m_unmatched_spot_targets as diagnostic


COLUMNS = ["timestamp_epoch","row_type","session_date","spot_join_status","source_request_id"]
BASE_EPOCH = 1636452900


def write_part(path: pathlib.Path, rows: list[dict[str,str]]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(path,"wt",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


class TestUnmatchedSpotDiagnostic(unittest.TestCase):
    def test_date_distribution_exact_overlap_and_nearest_offsets(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            write_part(root/"nifty_1m_composite_2021-11.csv.gz",[
                {"timestamp_epoch":str(BASE_EPOCH),"row_type":"SPOT","session_date":"2021-11-09","spot_join_status":"","source_request_id":"OLD-SPOT"},
                {"timestamp_epoch":str(BASE_EPOCH+120),"row_type":"SPOT","session_date":"2021-11-09","spot_join_status":"","source_request_id":"GAPSPOT1M-PATCH-R2-20211109"},
                {"timestamp_epoch":str(BASE_EPOCH),"row_type":"OPTION","session_date":"2021-11-09","spot_join_status":"NO_EXACT_TIMESTAMP_SPOT_MATCH","source_request_id":"OPT-SRC"},
                {"timestamp_epoch":str(BASE_EPOCH+60),"row_type":"OPTION","session_date":"2021-11-09","spot_join_status":"NO_EXACT_TIMESTAMP_SPOT_MATCH","source_request_id":"OPT-SRC"},
                {"timestamp_epoch":str(BASE_EPOCH+120),"row_type":"OPTION","session_date":"2021-11-09","spot_join_status":"NO_EXACT_TIMESTAMP_SPOT_MATCH","source_request_id":"OPT-SRC"},
                {"timestamp_epoch":str(BASE_EPOCH+3600),"row_type":"OPTION","session_date":"2021-11-10","spot_join_status":"NO_EXACT_TIMESTAMP_SPOT_MATCH","source_request_id":"OPT-SRC"},
            ])
            report=diagnostic.analyze(root)
        self.assertEqual(report["row_counts"]["option_rows"],4)
        self.assertEqual(report["row_counts"]["spot_rows"],2)
        self.assertEqual(report["unmatched_option_rows"]["row_count"],4)
        self.assertEqual(report["unmatched_option_rows"]["distinct_option_timestamps"],4)
        self.assertEqual(report["unmatched_option_rows"]["timestamps_marked_missing_but_present_in_existing_spot_rows"]["distinct_timestamps"],2)
        self.assertEqual(report["unmatched_option_rows"]["new_r2_patch_exact_timestamp_overlap"]["distinct_unmatched_option_timestamps"],1)
        self.assertEqual(report["unmatched_option_rows"]["unmatched_rows_by_session_date"]["2021-11-09"],3)
        self.assertEqual(report["spot_coverage"]["patch_r2_rows_by_weekday"]["Tuesday"],1)
        self.assertEqual(report["nearest_timestamp_diagnostic_seconds"]["same_day_signed_offset_histogram_seconds"]["-60"],1)
        self.assertFalse(report["quality_and_permission_flags"]["source_requests_made"])
        self.assertFalse(report["quality_and_permission_flags"]["prices_emitted"])

    def test_requires_matching_manifest_counts_when_manifest_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            write_part(root/"nifty_1m_composite_2021-11.csv.gz",[
                {"timestamp_epoch":str(BASE_EPOCH),"row_type":"SPOT","session_date":"2021-11-09","spot_join_status":"","source_request_id":"OLD-SPOT"}
            ])
            (root/"dataset_manifest.json").write_text(json.dumps({
                "source_row_count_options":0,"source_row_count_spot":0
            }),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"manifest_spot_row_count_mismatch"):
                diagnostic.analyze(root)


if __name__=="__main__":
    unittest.main(verbosity=2)
