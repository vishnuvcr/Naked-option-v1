#!/usr/bin/env python3
"""No-network regression tests for one-request Dhan spot diagnostics."""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_nifty_1m_spot_diagnostic as diagnostic
from test_nifty_1m_composite_dataset import epoch_ist, spot_request


class TestSpotDiagnostic(unittest.TestCase):
    def _payload(self):
        ts = epoch_ist("2026-10-01", "09:15:00")
        return {"timestamp": [ts], "open": [24700], "high": [24702],
                "low": [24698], "close": [24701], "volume": [1000]}

    def test_diagnostic_result_has_metadata_only_no_market_values(self):
        req = spot_request()
        result = diagnostic.summarize_response(
            json.dumps(self._payload()).encode(), req, 200, "application/json", "a" * 40
        )
        self.assertEqual(result["parser_status"], "PARSED_OK")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["array_lengths"], {
            "timestamp": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1
        })
        serialized = json.dumps(result)
        for market_value in ("24700", "24702", "24698", "24701", "1000"):
            self.assertNotIn(market_value, serialized)
        self.assertFalse(result["raw_response_persisted"])
        self.assertFalse(result["cache_written"])
        self.assertFalse(result["market_values_logged"])
        self.assertEqual(result["wire_requests"], 1)
        self.assertEqual(result["retries"], 0)

    def test_missing_volume_is_flagged_without_values(self):
        req = spot_request()
        payload = self._payload()
        payload.pop("volume")
        result = diagnostic.summarize_response(json.dumps(payload).encode(), req, 200, "application/json", "a" * 40)
        self.assertEqual(result["parser_status"], "PARSED_WITH_VOLUME_GAP")
        self.assertEqual(result["row_count"], 1)
        self.assertIn("SPOT_VOLUME_MISSING_OR_MISALIGNED", result["quality_flag_counts"])
        self.assertNotIn("24700", json.dumps(result))

    def test_misaligned_ohlc_is_rejected_with_sanitized_reason(self):
        req = spot_request()
        payload = self._payload()
        payload["high"] = []
        result = diagnostic.summarize_response(json.dumps(payload).encode(), req, 200, "application/json", "a" * 40)
        self.assertEqual(result["parser_status"], "PARSER_REJECTED")
        self.assertEqual(result["parser_reason"], "response_field_array_length_mismatch")
        self.assertNotIn("24700", json.dumps(result))

    def test_provider_error_exposes_only_sanitized_numeric_code(self):
        req = spot_request()
        result = diagnostic.summarize_response(
            b'{"errorCode":806,"errorMessage":"never log this","status":"failure"}',
            req, 200, "application/json", "a" * 40
        )
        self.assertEqual(result["parser_status"], "DHAN_API_ERROR")
        self.assertEqual(result["api_error_code"], "806")
        self.assertNotIn("never log this", json.dumps(result))
        self.assertNotIn("errorMessage", json.dumps(result))

    def test_non_200_does_not_parse_or_log_response_body(self):
        req = spot_request()
        result = diagnostic.summarize_response(b"secret body must not appear", req, 403, "", "a" * 40)
        self.assertEqual(result["parser_status"], "HTTP_ERROR")
        self.assertNotIn("secret body", json.dumps(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
