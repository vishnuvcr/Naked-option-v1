#!/usr/bin/env python3
"""Offline tests for encrypted CSV decryption and row construction."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
from decimal import Decimal
import tempfile
import unittest
from zoneinfo import ZoneInfo

import run_nifty_1m_composite_dataset as collector
import decrypt_nifty_1m_composite as decryptor

IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc


def epoch_ist(date_text: str, time_text: str) -> int:
    value = dt.datetime.fromisoformat(date_text + "T" + time_text).replace(tzinfo=IST)
    return int(value.astimezone(UTC).timestamp())


def spot_request() -> dict:
    return {
        "request_id": "SPOT1M-20261001-20261031",
        "source_family": "NIFTY_SPOT_1M",
        "endpoint": "https://api.dhan.co/v2/charts/intraday",
        "method": "POST",
        "window_start_inclusive": "2026-10-01",
        "window_end_exclusive": "2026-10-31",
        "max_response_bytes": 8388608,
        "max_rows": 12000,
        "body": {
            "securityId": "13", "exchangeSegment": "IDX_I", "instrument": "INDEX",
            "interval": "1", "oi": False,
            "fromDate": "2026-10-01 09:15:00", "toDate": "2026-10-30 15:30:00"
        },
    }


def option_request() -> dict:
    return {
        "request_id": "OPT1M-20261001-WEEK-E0-ATM-CALL",
        "source_family": "NIFTY_ROLLING_OPTION_1M",
        "endpoint": "https://api.dhan.co/v2/charts/rollingoption",
        "method": "POST",
        "window_start_inclusive": "2026-10-01",
        "window_end_exclusive": "2026-10-31",
        "max_response_bytes": 2097152,
        "max_rows": 10000,
        "body": {
            "exchangeSegment": "NSE_FNO", "interval": "1", "securityId": 13,
            "instrument": "OPTIDX", "expiryFlag": "WEEK", "expiryCode": 0,
            "strike": "ATM", "drvOptionType": "CALL",
            "requiredData": ["open", "high", "low", "close", "iv", "volume", "strike", "oi", "spot"],
            "fromDate": "2026-10-01", "toDate": "2026-10-31",
        }
    }


class TestEncryptedComposite(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip_and_wrong_key(self):
        key = collector.derive_key("hf_token_for_test_only_0123456789")
        plain = b"small test payload, no real market data"
        cipher = collector.encrypt_bytes(plain, key, nonce=b"0123456789ab")
        self.assertTrue(cipher.startswith(b"N1C1"))
        self.assertEqual(collector.decrypt_bytes(cipher, key), plain)
        other = collector.derive_key("hf_token_other_test_0123456789")
        with self.assertRaises(ValueError):
            collector.decrypt_bytes(cipher, other)

    def test_spot_parser_preserves_values_and_timezone(self):
        request = spot_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        payload = {
            "timestamp": [ts],
            "open": [Decimal("24700.25")],
            "high": [Decimal("24702.50")],
            "low": [Decimal("24699.90")],
            "close": [Decimal("24701.75")],
            "volume": [12345],
        }
        rows, problems = collector.parse_spot_response(payload, request)
        self.assertEqual(problems, [])
        self.assertEqual(rows[0]["session_date"], "2026-10-01")
        self.assertEqual(rows[0]["nifty_close"], "24701.75")
        self.assertTrue(rows[0]["timestamp_utc"].endswith("Z"))

    def test_spot_parser_rejects_misaligned_arrays(self):
        request = spot_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        payload = {"timestamp": [ts], "open": [1], "high": [1], "low": [], "close": [1], "volume": [1]}
        with self.assertRaisesRegex(ValueError, "array_length_mismatch"):
            collector.parse_spot_response(payload, request)

    def test_option_parser_keeps_dhan_spot_separate_from_joined_spot_and_computes_greeks_with_inputs(self):
        request = option_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        spotmap = {ts: {"nifty_open": "24700", "nifty_high": "24710", "nifty_low": "24690",
                        "nifty_close": "24705", "nifty_volume": "4000"}}
        payload = {"data": {"ce": {
            "timestamp": [ts], "open": [Decimal("120.1")], "high": [Decimal("122.0")],
            "low": [Decimal("119.0")], "close": [Decimal("121.5")],
            "iv": [Decimal("18.5")], "volume": [100], "strike": [Decimal("24700")],
            "oi": [3210], "spot": [Decimal("24704.5")]
        }, "pe": None}}
        calendar = {("2026-10-01", "WEEK", 0): {"expiry_date": "2026-10-08", "dividend_yield_decimal": "0.01"}}
        rates = [(dt.datetime(2026, 9, 30, tzinfo=UTC), 0.055, "test", "sha")]
        rows, problems = collector.parse_option_response(payload, request, spotmap, "a" * 64, "FETCHED", calendar, rates)
        self.assertEqual(problems, [])
        row = rows[0]
        self.assertEqual(row["rolling_spot"], "24704.5")
        self.assertEqual(row["nifty_close"], "24705")
        self.assertEqual(row["spot_join_status"], "EXACT_TIMESTAMP_MATCH")
        self.assertEqual(row["greek_status"], "CALCULATED_BS_V1_SOURCED_INPUTS")
        self.assertGreater(float(row["gamma"]), 0)
        self.assertGreater(float(row["delta"]), 0)
        self.assertEqual(row["option_type"], "CALL")

    def test_option_greeks_remain_null_without_actual_expiry_calendar(self):
        request = option_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        payload = {"data": {"ce": {
            "timestamp": [ts], "open": [120], "high": [122], "low": [119], "close": [121],
            "iv": [18.5], "volume": [100], "strike": [24700], "oi": [3210], "spot": [24705]
        }, "pe": None}}
        rows, _ = collector.parse_option_response(payload, request, {}, "b" * 64, "FETCHED", {}, [])
        self.assertEqual(rows[0]["greek_status"], "EXPIRY_MAPPING_UNAVAILABLE")
        self.assertEqual(rows[0]["delta"], "")
        self.assertEqual(rows[0]["gamma"], "")

    def test_rule_expiry_map_uses_september_2025_monthly_transition_correctly(self):
        sessions = {
            "2025-09-01", "2025-09-22", "2025-09-23", "2025-09-24",
            "2025-09-25", "2025-09-26", "2025-09-29", "2025-09-30",
            "2025-10-01", "2025-10-27", "2025-10-28", "2025-10-29",
        }
        mapping = collector.build_rule_expiry_map(sessions, {}, True)
        self.assertEqual(mapping[("2025-09-22", "MONTH", 0)]["expiry_date"], "2025-09-25")
        self.assertEqual(mapping[("2025-09-26", "MONTH", 0)]["expiry_date"], "2025-10-28")
        self.assertEqual(mapping[("2025-09-01", "WEEK", 0)]["expiry_date"], "2025-09-02")

    def test_black_scholes_signs(self):
        call = collector.black_scholes_greeks(100, 100, 0.25, 0.2, 0.04, 0.01, "CALL")
        put = collector.black_scholes_greeks(100, 100, 0.25, 0.2, 0.04, 0.01, "PUT")
        self.assertIsNotNone(call)
        self.assertIsNotNone(put)
        self.assertGreater(call["delta"], 0)
        self.assertLess(put["delta"], 0)
        self.assertGreater(call["gamma"], 0)
        self.assertGreater(call["vega_per_1pct_iv"], 0)
        self.assertGreater(call["rho_per_1pct_rate"], 0)
        self.assertLess(put["rho_per_1pct_rate"], 0)

    def test_decryptor_manifest_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = pathlib.Path(tmp) / "bundle"
            out = pathlib.Path(tmp) / "plain"
            inp.mkdir()
            key = collector.derive_key("hf_token_for_test_only_0123456789")
            gz = b"not an actual gzip stream; only tests cryptographic checks"
            cipher = collector.encrypt_bytes(gz, key, nonce=b"abcdefgh1234")
            (inp / "test.csv.gz.enc").write_bytes(cipher)
            (inp / "dataset_manifest.json").write_text(json.dumps({
                "download_bundle_contains_encrypted_data_only": True,
                "parts": [{"file": "test.csv.gz.enc", "encrypted_sha256": hashlib.sha256(cipher).hexdigest(),
                           "plain_gzip_sha256": hashlib.sha256(gz).hexdigest()}]
            }))
            parts = decryptor.decrypt_dataset(inp, out, key)
            self.assertEqual(parts[0].read_bytes(), gz)



    def test_cumulative_request_attempt_ledger_survives_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_path = collector.ATTEMPT_LEDGER_PATH
            collector.ATTEMPT_LEDGER_PATH = pathlib.Path(tmp) / "request_attempt_ledger.jsonl"
            try:
                ledger = collector.load_attempt_ledger()
                ledger["request_attempts_by_id"]["request-a"] = 1
                ledger["total_wire_attempts"] += 1
                collector.save_attempt_ledger(ledger)

                resumed = collector.load_attempt_ledger()
                self.assertEqual(resumed["total_wire_attempts"], 1)
                self.assertEqual(resumed["request_attempts_by_id"]["request-a"], 1)
                self.assertEqual(resumed["total_retry_attempts"], 0)

                resumed["request_attempts_by_id"]["request-a"] = 2
                resumed["total_wire_attempts"] += 1
                resumed["total_retry_attempts"] += 1
                resumed["permanent_failure_requests"]["request-b"] = "http_status_400"
                collector.save_attempt_ledger(resumed)

                again = collector.load_attempt_ledger()
                self.assertEqual(again["total_wire_attempts"], 2)
                self.assertEqual(again["total_retry_attempts"], 1)
                self.assertEqual(again["request_attempts_by_id"]["request-a"], 2)
                self.assertEqual(again["permanent_failure_requests"]["request-b"], "http_status_400")
            finally:
                collector.ATTEMPT_LEDGER_PATH = old_path

    def test_cumulative_attempt_ledger_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_path = collector.ATTEMPT_LEDGER_PATH
            collector.ATTEMPT_LEDGER_PATH = pathlib.Path(tmp) / "request_attempt_ledger.jsonl"
            try:
                collector.ATTEMPT_LEDGER_PATH.write_text("{not-json}\\n")
                ledger = collector.load_attempt_ledger()
                self.assertGreater(ledger["total_wire_attempts"], 8701)
                self.assertIn("__ALL__", ledger["permanent_failure_families"])
            finally:
                collector.ATTEMPT_LEDGER_PATH = old_path

if __name__ == "__main__":
    unittest.main(verbosity=2)
