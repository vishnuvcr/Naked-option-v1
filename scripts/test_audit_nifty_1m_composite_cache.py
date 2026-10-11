#!/usr/bin/env python3
"""Offline tests for cache-preserving recovery preflight; no market values/network."""
from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_nifty_1m_composite_cache as audit


class TestCompositeCacheAudit(unittest.TestCase):
    def setUp(self):
        self.root = {
            "budgets": {
                "max_wire_requests_total": 8701,
                "max_retry_requests_total": 100,
            }
        }
        self.requests = (
            [{"request_id": f"OPT-{i}", "source_family": "NIFTY_ROLLING_OPTION_1M"} for i in range(8540)]
            + [{"request_id": f"SPOT-{i}", "source_family": "NIFTY_SPOT_1M"} for i in range(61)]
        )
        self.ledger = {
            "total_wire_attempts": 8607,
            "total_retry_attempts": 5,
            "request_attempts_by_id": {},
            "permanent_failure_requests": {},
            "permanent_failure_families": {},
        }

    def test_partial_request_cache_passes_only_when_exact_existing_rows_rebuild(self):
        def cached(request, key):
            if request["request_id"] == "OPT-0":
                return (b'{}', {"response_sha256": "a" * 64})
            return None

        with mock.patch.object(audit.collector, "read_requests", return_value=self.requests),              mock.patch.object(audit.collector, "derive_key", return_value=b"test-key"),              mock.patch.object(audit.collector, "get_cached_payload", side_effect=cached),              mock.patch.object(audit.collector, "parse_json_numbers", return_value={}),              mock.patch.object(audit.collector, "_validate_request_payload"),              mock.patch.object(audit.collector, "_payload_row_count", return_value=8_490_723),              mock.patch.object(audit.collector, "load_attempt_ledger", return_value=self.ledger):
            result = audit.audit(self.root, "hf_token_test_value_long_enough")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["option_cache_valid"], 1)
        self.assertEqual(result["option_cache_missing"], 8539)
        self.assertEqual(result["cached_option_rows"], 8_490_723)
        self.assertFalse(result["live_option_requests_permitted"])
        self.assertEqual(result["source_requests_made"], 0)

    def test_wrong_preserved_row_count_blocks_before_source_requests(self):
        with mock.patch.object(audit.collector, "read_requests", return_value=self.requests),              mock.patch.object(audit.collector, "derive_key", return_value=b"test-key"),              mock.patch.object(audit.collector, "get_cached_payload", return_value=(b'{}', {})),              mock.patch.object(audit.collector, "parse_json_numbers", return_value={}),              mock.patch.object(audit.collector, "_validate_request_payload"),              mock.patch.object(audit.collector, "_payload_row_count", return_value=7),              mock.patch.object(audit.collector, "load_attempt_ledger", return_value=self.ledger):
            result = audit.audit(self.root, "hf_token_test_value_long_enough")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotEqual(result["cached_option_rows"], result["expected_preserved_option_rows"])
        self.assertEqual(result["source_requests_made"], 0)

    def test_missing_hf_key_blocks_without_cache_decryption_or_requests(self):
        with mock.patch.object(audit.collector, "derive_key", side_effect=AssertionError("must not derive")):
            result = audit.audit(self.root, "")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "HF_TOKEN_NOT_CONFIGURED")
        self.assertEqual(result["source_requests_made"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
