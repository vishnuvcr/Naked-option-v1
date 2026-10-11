#!/usr/bin/env python3
"""Offline regression tests for artifact-preserving Dhan spot gap fill."""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import pathlib
import sys
import tempfile
import unittest
import os
import hashlib
import argparse
from collections import Counter
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_nifty_1m_composite_dataset as collector
import run_nifty_1m_spot_gapfill as gapfill
import validate_nifty_1m_spot_gapfill_split_proposal as split_validator


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
        self.assertEqual(proposal["base_partial_artifact"]["artifact_id"], "11693866249")
        self.assertEqual(proposal["base_partial_artifact"]["existing_option_rows"], 8_490_723)
        self.assertEqual(proposal["base_partial_artifact"]["existing_spot_rows"], 403_664)
        self.assertTrue(proposal["preserve_existing_spot_rows"])
        self.assertEqual(proposal["expected_existing_spot_rows"], 403_664)
        self.assertFalse(proposal["refetch_successful_windows"])
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


class TestSplitProposalAuthorization(unittest.TestCase):
    def setUp(self):
        self.proposal = split_validator.load_json(split_validator.DEFAULT_PROPOSAL)

    def test_proposal_validator_passes_without_authorizing_requests(self):
        self.assertEqual(split_validator.validate_proposal(self.proposal), [])
        self.assertFalse(self.proposal["live_requests_authorized"])

    def test_missing_or_stale_tester_authorization_fails_closed(self):
        decision = {
            "decision": "PASS_WITH_SCOPED_RESTRICTIONS",
            "decision_scope": "OFFLINE_SPLIT_MANIFEST_DESIGN_ONLY",
            "reviewed_developer_commit": "b" * 40,
            "proposal_blob_sha": "a" * 40,
            "split_recovery_authorized": False,
            "live_requests_authorized": False,
            "split_recovery_request_limit": 34,
            "split_recovery_retry_limit": 0,
            "live_option_requests_allowed": False,
            "model_fitting_authorized": False,
            "holdout_access_authorized": False,
            "strategy_testing_authorized": False,
        }
        errors = split_validator.validate_exact_authorization(
            self.proposal, "a" * 40, "b" * 40, decision
        )
        self.assertIn("tester_scope_not_split_recovery_execution", errors)
        self.assertIn("split_recovery_not_authorized", errors)
        self.assertIn("live_requests_not_authorized", errors)

    def test_exact_authorization_requires_both_exact_shas_and_all_scope_guards(self):
        decision = {
            "decision": "PASS_WITH_SCOPED_RESTRICTIONS",
            "decision_scope": "SPLIT_RECOVERY_EXECUTION",
            "reviewed_developer_commit": "b" * 40,
            "proposal_blob_sha": "a" * 40,
            "split_recovery_authorized": True,
            "live_requests_authorized": True,
            "split_recovery_request_limit": 34,
            "split_recovery_retry_limit": 0,
            "live_option_requests_allowed": False,
            "model_fitting_authorized": False,
            "holdout_access_authorized": False,
            "strategy_testing_authorized": False,
        }
        errors = split_validator.validate_exact_authorization(
            self.proposal, "a" * 40, "b" * 40, decision
        )
        self.assertEqual(errors, [])
        stale = split_validator.validate_exact_authorization(
            self.proposal, "c" * 40, "b" * 40, decision
        )
        self.assertIn("tester_proposal_blob_sha_mismatch", stale)


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

    def test_split_execution_fails_closed_without_spent_exact_sha_marker(self):
        proposal_path = split_validator.DEFAULT_PROPOSAL
        raw = proposal_path.read_bytes()
        blob_sha = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        args = argparse.Namespace(
            split_proposal=proposal_path,
            proposal_blob_sha=blob_sha,
            reviewed_sha="b" * 40,
            source_dir=pathlib.Path("/tmp/not-a-real-artifact"),
            plain_dir=pathlib.Path("/tmp/not-a-real-plain-dir"),
            split_ledger=pathlib.Path("/tmp/not-a-real-ledger.json"),
        )
        missing_marker = pathlib.Path("/tmp/no-such-spot-split-marker-for-test.json")
        with mock.patch.dict(os.environ, {"DHAN_ACCESS_TOKEN": "test-token", "HF_TOKEN": "test-token"}), \
             mock.patch.object(gapfill, "SPLIT_EXECUTION_MARKER", missing_marker), \
             mock.patch.object(gapfill.urllib.request, "build_opener") as network:
            with self.assertRaises(FileNotFoundError):
                gapfill.execute_split(args)
        network.assert_not_called()


    def test_partial_base_preserves_existing_spot_rows_and_fills_only_new_matches(self):
        epoch = int(dt.datetime.fromisoformat("2026-10-01T09:15:00+05:30").timestamp())
        old_option = sample_row("OPTION", epoch, "OPT-HIST")
        old_option.update({
            "option_close": "100", "nifty_open": "24700", "nifty_high": "24702",
            "nifty_low": "24698", "nifty_close": "24701", "nifty_volume": "12345",
            "spot_join_status": "EXACT_TIMESTAMP_MATCH", "data_quality_flags": "",
        })
        old_spot = sample_row("SPOT", epoch, "GAPSPOT1M-OLD")
        old_spot.update({
            "nifty_open": "24700", "nifty_high": "24702", "nifty_low": "24698",
            "nifty_close": "24701", "nifty_volume": "12345", "spot_join_status": "SPOT_SOURCE_ROW",
            "data_quality_flags": "",
        })
        new_epoch = epoch + 60
        missing_option = sample_row("OPTION", new_epoch, "OPT-HIST")
        missing_option.update({
            "option_close": "101", "nifty_open": "", "nifty_high": "", "nifty_low": "",
            "nifty_close": "", "nifty_volume": "", "spot_join_status": "NO_EXACT_TIMESTAMP_SPOT_MATCH",
            "data_quality_flags": "SPOT_JOIN_MISSING",
        })
        new_spot = sample_row("SPOT", new_epoch, "GAPSPOT1M-R1")
        new_spot.update({
            "nifty_open": "24701", "nifty_high": "24703", "nifty_low": "24699",
            "nifty_close": "24702", "nifty_volume": "23456", "spot_join_status": "SPOT_SOURCE_ROW",
            "data_quality_flags": "",
        })
        spot_map = {
            new_epoch: {k: new_spot.get(k, "") for k in (
                "nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume", "data_quality_flags"
            )}
        }
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            base_path = root / "base" / "nifty_1m_composite_2026-10.csv.gz"
            spot_dir = root / "spots"
            output_dir = root / "output"
            write_gz_csv(base_path, [old_option, old_spot, missing_option])
            write_gz_csv(spot_dir / "spot_rows_2026-10.csv.gz", [new_spot])
            old_plain = gapfill.PLAIN_ROOT
            gapfill.PLAIN_ROOT = output_dir
            try:
                rows_by_month, counters = gapfill.merge_into_existing_dataset(
                    [base_path], spot_dir, spot_map, preserve_existing_spot_rows=True
                )
            finally:
                gapfill.PLAIN_ROOT = old_plain
            with gzip.open(output_dir / "nifty_1m_composite_2026-10.csv.gz", "rt", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        options = [row for row in rows if row["row_type"] == "OPTION"]
        spots = [row for row in rows if row["row_type"] == "SPOT"]
        self.assertEqual(len(options), 2)
        self.assertEqual(len(spots), 2)
        self.assertEqual(options[0]["nifty_close"], "24701")
        self.assertEqual(options[1]["nifty_close"], "24702")
        self.assertNotIn("SPOT_JOIN_MISSING", options[1]["data_quality_flags"])
        self.assertEqual(counters["rows_options_out"], 2)
        self.assertEqual(counters["rows_spot_out"], 2)
        self.assertEqual(counters["spot_join_matched"], 2)
        self.assertEqual(counters["spot_join_missing"], 0)
        self.assertEqual(rows_by_month["2026-10"], 4)

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





class TestSpotGapfillRowCapMetadata(unittest.TestCase):
    def test_row_cap_failure_records_observed_count_and_response_hash(self):
        request = {
            "request_id": "TEST-SPOT-ROW-CAP",
            "source_family": "NIFTY_SPOT_1M",
            "endpoint": "https://example.invalid/spot",
            "method": "POST",
            "window_start_inclusive": "2021-11-08",
            "window_end_exclusive": "2021-11-09",
            "max_rows": 1,
            "max_response_bytes": 1024 * 1024,
            "max_attempts": 1,
            "body": {
                "securityId": "13", "exchangeSegment": "IDX_I", "instrument": "INDEX",
                "interval": "1", "oi": False,
                "fromDate": "2021-11-08 09:15:00", "toDate": "2021-11-08 15:30:00",
            },
        }
        raw = json.dumps({
            "timestamp": [1636334100, 1636334160],
            "open": [1, 1], "high": [1, 1], "low": [1, 1], "close": [1, 1], "volume": [10, 10],
        }).encode("utf-8")
        response = mock.Mock()
        response.status = 200
        response.headers = {"Content-Type": "application/json"}
        response.read.return_value = raw
        response.close.return_value = None
        opener = mock.Mock()
        opener.open.return_value = response
        collector_obj = gapfill.SpotGapFillCollector(
            token="test-token", key=b"x" * 32,
            requests=[request],
            ledger={"wire_attempts_new": 0, "retry_attempts_new": 0, "attempts_by_request_id": {}},
        )
        collector_obj.pacer.wait = mock.Mock()
        collector_obj._record_attempt = mock.Mock()
        with mock.patch.object(gapfill.urllib.request, "build_opener", return_value=opener), \
             mock.patch.object(gapfill, "get_cached_payload", return_value=None):
            payload, status, digest, http_status, size = collector_obj._get_payload(request)
        self.assertIsNone(payload)
        self.assertEqual(status, "FAILED_VALIDATION")
        self.assertEqual(http_status, 200)
        self.assertEqual(size, len(raw))
        self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
        self.assertEqual(collector_obj.errors[0]["reason"], "response_row_cap_exceeded_n2_cap1")
        self.assertEqual(collector_obj.errors[0]["observed_rows"], 2)
        self.assertEqual(collector_obj.errors[0]["max_rows"], 1)
        self.assertEqual(collector_obj.errors[0]["response_bytes"], len(raw))
        self.assertEqual(collector_obj.errors[0]["response_sha256"], hashlib.sha256(raw).hexdigest())


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
