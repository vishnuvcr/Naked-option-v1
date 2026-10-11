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


class TestSpotGapfillSplitProposal(unittest.TestCase):
    def test_split_proposal_is_complete_disjoint_bounded_and_not_authorized(self):
        proposal_path = gapfill.ROOT / "research/gates/NIFTY_1M_SPOT_GAPFILL_SPLIT_PROPOSAL.json"
        proposal = collector.load_json(proposal_path)
        requests = proposal["requests"]
        self.assertEqual(proposal["status"], "DRAFT_OFFLINE_ONLY_NOT_EXECUTABLE")
        self.assertFalse(proposal["live_requests_authorized"])
        self.assertFalse(proposal["live_option_requests_allowed"])
        self.assertFalse(proposal["model_fitting_authorized"])
        self.assertFalse(proposal["holdout_access_authorized"])
        self.assertFalse(proposal["strategy_testing_authorized"])
        self.assertEqual(proposal["requests_planned"], 34)
        self.assertEqual(proposal["max_wire_requests"], 34)
        self.assertEqual(proposal["max_retry_requests"], 0)
        self.assertEqual(proposal["max_attempts_per_request"], 1)
        self.assertEqual(len(requests), 34)
        self.assertEqual(len({r["request_id"] for r in requests}), 34)
        self.assertEqual(requests[0]["window_start_inclusive"], "2021-10-11")
        self.assertEqual(requests[-1]["window_end_exclusive"], "2022-06-02")
        for i, request in enumerate(requests):
            start = dt.date.fromisoformat(request["window_start_inclusive"])
            end = dt.date.fromisoformat(request["window_end_exclusive"])
            self.assertGreater((end - start).days, 0)
            self.assertLessEqual((end - start).days, 7)
            self.assertEqual(request["max_rows"], 4000)
            self.assertEqual(request["max_response_bytes"], 8_388_608)
            self.assertEqual(request["max_attempts"], 1)
            self.assertEqual(request["source_family"], "NIFTY_SPOT_1M")
            self.assertEqual(request["body"]["fromDate"], f"{start.isoformat()} 09:15:00")
            expected_last_day = (end - dt.timedelta(days=1)).isoformat()
            self.assertEqual(request["body"]["toDate"], f"{expected_last_day} 15:30:00")
            if i:
                self.assertEqual(requests[i-1]["window_end_exclusive"], request["window_start_inclusive"])
        self.assertEqual(
            sum((dt.date.fromisoformat(r["window_end_exclusive"]) -
                 dt.date.fromisoformat(r["window_start_inclusive"])).days for r in requests),
            234,
        )


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




class TestSpotGapfillByteBudget(unittest.TestCase):
    def setUp(self):
        self.raw = b"{malformed-json"
        self.request = {
            "request_id": "TEST-SPOT-BYTES",
            "endpoint": "https://example.invalid/spot",
            "method": "POST",
            "body": {"symbol": "NIFTY"},
            "max_response_bytes": 1024,
            "window_start_inclusive": "2026-01-01",
            "window_end_exclusive": "2026-01-02",
        }
        self.response = mock.Mock()
        self.response.status = 200
        self.response.headers = {"Content-Type": "application/json"}
        self.response.read.return_value = self.raw
        self.response.close.return_value = None
        self.opener = mock.Mock()
        self.opener.open.return_value = self.response
        self.collector = gapfill.SpotGapFillCollector(
            token="test-token",
            key=b"x" * 32,
            requests=[self.request],
            ledger={"wire_attempts_new": 0, "retry_attempts_new": 0, "attempts_by_request_id": {}},
        )
        self.collector.pacer.wait = mock.Mock()
        self.collector._record_attempt = mock.Mock()

    def test_malformed_response_bytes_are_charged_before_json_validation(self):
        with mock.patch.object(gapfill.urllib.request, "build_opener", return_value=self.opener), \
             mock.patch.object(gapfill, "get_cached_payload", return_value=None), \
             mock.patch.object(gapfill, "parse_json_numbers", side_effect=ValueError("bad_json")):
            payload, status, digest, http_status, size = self.collector._get_payload(self.request)
        self.assertIsNone(payload)
        self.assertEqual(status, "FAILED_VALIDATION")
        self.assertEqual(self.collector.downloaded_bytes, len(self.raw))
        self.assertEqual(size, len(self.raw))

    def test_aggregate_budget_exceeded_fails_before_payload_validation(self):
        cap = 268_435_456
        self.collector.downloaded_bytes = cap - len(self.raw) + 1
        with mock.patch.object(gapfill.urllib.request, "build_opener", return_value=self.opener):
            with self.assertRaisesRegex(ValueError, "spot_aggregate_byte_budget_exceeded"):
                self.collector._http_fetch(self.request)
        self.assertEqual(self.collector.downloaded_bytes, cap - len(self.raw) + 1)


    def test_max_attempts_one_disables_retry(self):
        self.request["max_attempts"] = 1
        failure = collector.SourceRequestError("http_status_500", 500)
        with mock.patch.object(gapfill, "get_cached_payload", return_value=None), \
             mock.patch.object(self.collector, "_http_fetch", side_effect=failure) as fetch:
            payload, status, digest, http_status, size = self.collector._get_payload(self.request)
        self.assertIsNone(payload)
        self.assertEqual(status, "FAILED_REQUEST")
        self.assertEqual(fetch.call_count, 1)

    def test_max_attempts_two_allows_one_retry(self):
        self.request["max_attempts"] = 2
        failures = [
            collector.SourceRequestError("http_status_500", 500),
            collector.SourceRequestError("http_status_500", 500),
        ]
        with mock.patch.object(gapfill, "get_cached_payload", return_value=None), \
             mock.patch.object(self.collector, "_http_fetch", side_effect=failures) as fetch:
            payload, status, digest, http_status, size = self.collector._get_payload(self.request)
        self.assertIsNone(payload)
        self.assertEqual(status, "FAILED_REQUEST")
        self.assertEqual(fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
