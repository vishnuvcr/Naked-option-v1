#!/usr/bin/env python3
"""Offline regression tests for artifact-preserving Dhan spot gap fill."""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_nifty_1m_composite_dataset as collector
import run_nifty_1m_spot_gapfill as gapfill


def sample_row(row_type: str, epoch: int, request_id: str) -> dict[str, str]:
    ist = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc).astimezone(gapfill.IST)
    row = {column: "" for column in gapfill.COLUMNS}
    row.update({
        "timestamp_epoch": str(epoch),
        "row_type": row_type,
        "timestamp_utc": dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "timestamp_ist": ist.isoformat(),
        "session_date": ist.date().isoformat(),
        "underlying": "NIFTY",
        "source_provider": "DhanHQ",
        "source_request_id": request_id,
        "request_scope_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "cache_status": "FETCHED",
        "greek_model": "Black-Scholes-European-v1",
        "greek_status": "NOT_APPLICABLE_SPOT_ROW" if row_type == "SPOT" else "",
    })
    return row


def write_gz_csv(path: pathlib.Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=gapfill.COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


class TestSpotGapfillManifest(unittest.TestCase):
    def test_manifest_has_full_disjoint_39_day_spot_only_coverage(self):
        root = collector.load_json(collector.ROOT_MANIFEST)
        requests = gapfill.validate_gapfill_manifest(root)
        self.assertEqual(len(requests), 47)
        self.assertEqual(requests[0]["window_start_inclusive"], "2021-10-11")
        self.assertEqual(requests[-1]["window_end_exclusive"], "2026-10-11")
        self.assertTrue(all(r["source_family"] == "NIFTY_SPOT_1M" for r in requests))
        self.assertTrue(all((dt.date.fromisoformat(r["window_end_exclusive"]) -
                             dt.date.fromisoformat(r["window_start_inclusive"])).days <= 39 for r in requests))
        self.assertFalse(gapfill.load_json(gapfill.GAPFILL_MANIFEST)["live_option_requests_allowed"])
        self.assertEqual(gapfill.BASELINE_WIRE_ATTEMPTS + gapfill.DIAGNOSTIC_WIRE_ATTEMPTS +
                         47 + 47, 8701)


class TestSpotGapfillMerge(unittest.TestCase):
    def test_option_rows_are_preserved_and_exact_spot_values_fill_join_columns(self):
        epoch = int(dt.datetime.fromisoformat("2026-10-01T09:15:00+05:30").timestamp())
        base = sample_row("OPTION", epoch, "OPT-HIST")
        base.update({
            "option_open": "99", "option_high": "101", "option_low": "98",
            "option_close": "100", "spot_join_status": "NO_EXACT_TIMESTAMP_SPOT_MATCH",
            "data_quality_flags": "",
        })
        spot1 = sample_row("SPOT", epoch, "GAPSPOT1M")
        spot1.update({"nifty_open": "24700", "nifty_high": "24702", "nifty_low": "24698",
                      "nifty_close": "24701", "nifty_volume": "12345", "spot_join_status": "SPOT_SOURCE_ROW",
                      "data_quality_flags": ""})
        spot2 = sample_row("SPOT", epoch + 60, "GAPSPOT1M")
        spot2.update({"nifty_open": "24701", "nifty_high": "24703", "nifty_low": "24699",
                      "nifty_close": "24702", "nifty_volume": "23456", "spot_join_status": "SPOT_SOURCE_ROW"})
        spot_map = {
            epoch: {k: spot1.get(k, "") for k in ("nifty_open", "nifty_high", "nifty_low",
                                                     "nifty_close", "nifty_volume", "data_quality_flags")},
        }
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            base_path = root / "base" / "nifty_1m_composite_2026-10.csv.gz"
            spot_dir = root / "spots"
            output_dir = root / "output"
            write_gz_csv(base_path, [base])
            write_gz_csv(spot_dir / "spot_rows_2026-10.csv.gz", [spot1, spot2])
            old_plain = gapfill.PLAIN_ROOT
            gapfill.PLAIN_ROOT = output_dir
            try:
                rows_by_month, counters = gapfill.merge_into_existing_dataset([base_path], spot_dir, spot_map)
            finally:
                gapfill.PLAIN_ROOT = old_plain
            with gzip.open(output_dir / "nifty_1m_composite_2026-10.csv.gz", "rt", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        option_rows = [row for row in rows if row["row_type"] == "OPTION"]
        spot_rows = [row for row in rows if row["row_type"] == "SPOT"]
        self.assertEqual(len(option_rows), 1)
        self.assertEqual(len(spot_rows), 2)
        self.assertEqual(option_rows[0]["option_close"], "100")
        self.assertEqual(option_rows[0]["nifty_open"], "24700")
        self.assertEqual(option_rows[0]["nifty_close"], "24701")
        self.assertEqual(option_rows[0]["nifty_volume"], "12345")
        self.assertEqual(option_rows[0]["spot_join_status"], "EXACT_TIMESTAMP_MATCH")
        self.assertEqual(counters["rows_options_out"], 1)
        self.assertEqual(counters["rows_spot_out"], 2)
        self.assertEqual(counters["spot_join_matched"], 1)
        self.assertEqual(counters["spot_join_missing"], 0)
        self.assertEqual(rows_by_month["2026-10"], 3)

    def test_unmatched_option_keeps_spot_blank_and_is_flagged(self):
        epoch = int(dt.datetime.fromisoformat("2026-10-01T09:15:00+05:30").timestamp())
        row = sample_row("OPTION", epoch, "OPT-HIST")
        counters = Counter()
        enriched = list(gapfill._enriched_option_rows(
            pathlib.Path("unused"), {}, counters
        )) if False else None
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "options.csv.gz"
            write_gz_csv(path, [row])
            output = list(gapfill._enriched_option_rows(path, {}, counters))
        self.assertEqual(output[0]["nifty_open"], "")
        self.assertEqual(output[0]["spot_join_status"], "NO_EXACT_TIMESTAMP_SPOT_MATCH")
        self.assertIn("SPOT_JOIN_MISSING", output[0]["data_quality_flags"])
        self.assertEqual(counters["spot_join_missing"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
