import csv, gzip, hashlib, json, tempfile, unittest
from pathlib import Path
from offline_dataset_preflight import run

class PreflightTests(unittest.TestCase):
    def make_file(self, root, rows, header=None):
        header = header or [f"c{i}" for i in range(47)]
        path = Path(root) / "tiny.csv.gz"
        with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)
        return path

    def test_passes_exact_fixture_and_reports_metadata_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); header=["timestamp_epoch","instrument_type","symbol","expiry","strike","option_type"]+[f"c{i}" for i in range(41)]
            rows=[["1","spot","NIFTY","","",""]+[""]*41,["2","spot","NIFTY","","",""]+[""]*41]
            path=self.make_file(td,rows,header)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            out=root/"report.json"
            report=run(path,out,digest,2,47)
            self.assertEqual(report["data_rows"],2)
            self.assertEqual(report["gzip_integrity"],"PASS")
            self.assertNotIn("NIFTY",out.read_text())

    def test_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=self.make_file(td,[["x"]*47])
            with self.assertRaisesRegex(ValueError,"INPUT_SHA256_MISMATCH"):
                run(path,Path(td)/"r.json","0"*64,1,47)

    def test_row_count_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=self.make_file(td,[["x"]*47])
            with self.assertRaisesRegex(ValueError,"ROW_COUNT_MISMATCH"):
                run(path,Path(td)/"r.json",hashlib.sha256(path.read_bytes()).hexdigest(),2,47)

    def test_duplicate_header_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            header=["same","same"]+[f"c{i}" for i in range(45)]
            path=self.make_file(td,[["x"]*47],header)
            with self.assertRaisesRegex(ValueError,"DUPLICATE_COLUMN_NAMES"):
                run(path,Path(td)/"r.json",hashlib.sha256(path.read_bytes()).hexdigest(),1,47)

    def test_bad_column_count_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=self.make_file(td,[["x"]*46], [f"c{i}" for i in range(46)])
            with self.assertRaisesRegex(ValueError,"COLUMN_COUNT_MISMATCH"):
                run(path,Path(td)/"r.json",hashlib.sha256(path.read_bytes()).hexdigest(),1,47)

if __name__ == "__main__":
    unittest.main()
