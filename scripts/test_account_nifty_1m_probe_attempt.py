#!/usr/bin/env python3
"""Offline, no-network tests for accounting the authorized diagnostic wire request."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import account_nifty_1m_probe_attempt as account


class TestDiagnosticAttemptAccounting(unittest.TestCase):
    def _fixtures(self, root: pathlib.Path):
        plan = {
            "request_id": "SPOT1M-20260915-20261011",
            "max_wire_requests": 1,
            "max_retries": 0,
        }
        marker = {
            "status": "SPENT_BEFORE_SOURCE_REQUEST",
            "scope": "ONE_NONPERSISTING_SPOT_SCHEMA_DIAGNOSTIC",
            "max_wire_requests": 1,
            "max_retries": 0,
            "request_id": plan["request_id"],
            "reviewed_developer_commit": "a" * 40,
            "github_run_id": "test-run-123",
        }
        result = {
            "request_id": plan["request_id"],
            "developer_reviewed_sha": "a" * 40,
            "wire_requests": 1,
            "retries": 0,
            "executed_at_utc": "2026-10-11T00:00:00Z",
            "request_scope_sha256": "b" * 64,
            "raw_response_persisted": False,
            "cache_written": False,
        }
        plan_path = root / "plan.json"
        marker_path = root / "marker.json"
        result_path = root / "result.json"
        ledger_path = root / "request_attempt_ledger.jsonl"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        marker_path.write_text(json.dumps(marker), encoding="utf-8")
        result_path.write_text(json.dumps(result), encoding="utf-8")
        return plan_path, marker_path, result_path, ledger_path

    def test_accounts_exactly_one_wire_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            plan_path, marker_path, result_path, ledger_path = self._fixtures(root)
            old_plan_path = account.PLAN_PATH
            account.PLAN_PATH = plan_path
            try:
                first = account.account_probe_attempt(marker_path, result_path, ledger_path, "b" * 64)
                second = account.account_probe_attempt(marker_path, result_path, ledger_path, "b" * 64)
                events = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            finally:
                account.PLAN_PATH = old_plan_path
            self.assertEqual(first["status"], "ACCOUNTED")
            self.assertEqual(first["wire_delta"], 1)
            self.assertEqual(second["status"], "ALREADY_ACCOUNTED")
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["wire_delta"], 1)
            self.assertEqual(events[0]["retry_delta"], 0)
            self.assertEqual(events[0]["request_updates"], {})
            self.assertFalse(events[0]["raw_response_persisted"])

    def test_scope_hash_mismatch_fails_without_ledger_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            plan_path, marker_path, result_path, ledger_path = self._fixtures(root)
            old_plan_path = account.PLAN_PATH
            account.PLAN_PATH = plan_path
            try:
                with self.assertRaisesRegex(ValueError, "diagnostic_request_scope_hash_mismatch"):
                    account.account_probe_attempt(marker_path, result_path, ledger_path, "c" * 64)
                self.assertFalse(ledger_path.exists())
            finally:
                account.PLAN_PATH = old_plan_path

    def test_corrupt_ledger_fails_closed_without_appending(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            plan_path, marker_path, result_path, ledger_path = self._fixtures(root)
            ledger_path.write_text("{corrupt}\n", encoding="utf-8")
            old_plan_path = account.PLAN_PATH
            account.PLAN_PATH = plan_path
            try:
                with self.assertRaisesRegex(ValueError, "attempt_ledger_corrupt_fail_closed"):
                    account.account_probe_attempt(marker_path, result_path, ledger_path, "b" * 64)
                self.assertEqual(ledger_path.read_text(), "{corrupt}\n")
            finally:
                account.PLAN_PATH = old_plan_path


if __name__ == "__main__":
    unittest.main(verbosity=2)
