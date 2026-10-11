from __future__ import annotations

import csv
import gzip
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_nifty_1m_composite_values as auditor

COLUMNS = [
    "timestamp_epoch", "row_type", "timestamp_utc", "timestamp_ist", "session_date",
    "underlying", "expiry_flag", "expiry_code", "requested_relative_strike",
    "returned_strike", "option_type", "option_open", "option_high", "option_low",
    "option_close", "option_volume", "open_interest", "implied_volatility",
    "rolling_spot", "nifty_open", "nifty_high", "nifty_low", "nifty_close",
    "nifty_volume", "spot_join_status", "source_provider", "source_endpoint",
    "source_request_id", "request_scope_sha256", "response_sha256", "cache_status",
    "expiry_date", "expiry_mapping_source", "time_to_expiry_years",
    "risk_free_rate_decimal", "risk_free_rate_source", "dividend_yield_decimal",
    "dividend_yield_source", "greek_assumption", "delta", "gamma", "theta_per_day",
    "vega_per_1pct_iv", "rho_per_1pct_rate", "greek_model", "greek_status",
    "data_quality_flags",
]
IST = ZoneInfo("Asia/Kolkata")
EPOCH = 1704168000  # 2024-01-02 09:30:00 IST


def base_row(row_type: str, request_id: str) -> dict[str, str]:
    utc = datetime.fromtimestamp(EPOCH, tz=timezone.utc)
    ist = utc.astimezone(IST)
    row = {col: "" for col in COLUMNS}
    row.update({
        "timestamp_epoch": str(EPOCH),
        "row_type": row_type,
        "timestamp_utc": utc.isoformat().replace("+00:00", "Z"),
        "timestamp_ist": ist.isoformat(),
        "session_date": ist.date().isoformat(),
        "underlying": "NIFTY",
        "source_request_id": request_id,
        "source_provider": "test",
        "source_endpoint": "test",
    })
    if row_type == "OPTION":
        row.update({
            "expiry_flag": "0", "expiry_code": "0", "requested_relative_strike": "ATM",
            "returned_strike": "21000", "option_type": "CALL",
            "option_open": "100", "option_high": "102", "option_low": "99", "option_close": "101",
            "option_volume": "500", "open_interest": "1000", "implied_volatility": "0.2",
            "rolling_spot": "21000", "nifty_open": "20999", "nifty_high": "21005",
            "nifty_low": "20995", "nifty_close": "21002", "nifty_volume": "12345",
            "spot_join_status": "EXACT_TIMESTAMP_MATCH",
            "expiry_date": "2024-01-04", "time_to_expiry_years": "0.005",
        })
    else:
        row.update({
            "nifty_open": "20999", "nifty_high": "21005", "nifty_low": "20995",
            "nifty_close": "21002", "nifty_volume": "12345",
        })
    return row


def write_fixture(root: pathlib.Path, option_rows: list[dict[str, str]], spot_rows: list[dict[str, str]],
                  *, tamper_row_count: bool = False, bad_header: bool = False) -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    filename = "nifty_1m_composite_2024-01.csv.gz"
    output = root / filename
    rows = option_rows + spot_rows
    with gzip.open(output, "wt", encoding="utf-8", newline="") as handle:
        fields = COLUMNS[:-1] if bad_header else COLUMNS
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: v for k, v in row.items() if k in fields})
    n = len(rows) + (1 if tamper_row_count else 0)
    manifest = {
        "schema_version": 1,
        "dataset_id": "synthetic-test-only",
        "download_bundle_contains_encrypted_data_only": True,
        "columns": COLUMNS,
        "parts": [{"file": filename + ".enc", "row_count": n}],
        "row_count_by_month": {"2024-01": n},
        "dataset_summary": {
            "rows_options": len(option_rows),
            "original_rows_options": len(option_rows),
            "rows_spot": len(spot_rows),
            "spot_join_matched": len(option_rows),
            "spot_join_missing": 0,
            "observed_trading_session_count": 1,
            "historical_option_request_grid_status": "PARTIAL_GRID",
            "spot_recovery_status": "SPOT_GAPFILL_PARTIAL",
            "gapfill_request_count_failed": 6,
            "gapfill_request_count_planned": 47,
        },
    }
    (root / "dataset_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return output


class DatasetValueAuditTests(unittest.TestCase):
    def run_audit(self, root: pathlib.Path) -> dict:
        output = root / "safe-report.json"
        db = root / "temp.sqlite"
        auditor.audit_dataset(root, output, db)
        self.assertFalse(db.exists(), "temporary duplicate database should be deleted")
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_dataset_passes_with_coverage_restriction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, [base_row("OPTION", "request-opt")], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "PASS_WITH_COVERAGE_RESTRICTIONS")
            self.assertEqual(report["rows"], {"total": 2, "option": 1, "spot": 1})
            self.assertEqual(report["row_integrity"]["semantic_error_count"], 0)
            self.assertNotIn("21000", (root / "safe-report.json").read_text(encoding="utf-8"))

    def test_invalid_option_ohlc_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["option_high"] = "98"
            write_fixture(root, [option], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertGreater(report["row_integrity"]["critical_findings"].get("option_ohlc_invalid", 0), 0)

    def test_timestamp_session_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            option["session_date"] = "2024-01-03"
            write_fixture(root, [option], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertGreater(report["row_integrity"]["critical_findings"].get("session_date_mismatch", 0), 0)

    def test_duplicate_collector_composite_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            option = base_row("OPTION", "request-opt")
            write_fixture(root, [option, dict(option)], [base_row("SPOT", "request-spot")])
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["duplicates"]["collector_composite_key_duplicates"], 1)

    def test_manifest_row_count_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, [base_row("OPTION", "request-opt")], [base_row("SPOT", "request-spot")],
                          tamper_row_count=True)
            report = self.run_audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertGreater(report["row_integrity"]["critical_findings"].get("monthly_row_count_mismatch", 0), 0)

    def test_schema_mismatch_emits_no_market_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_fixture(root, [base_row("OPTION", "request-opt")], [base_row("SPOT", "request-spot")],
                          bad_header=True)
            output = root / "safe-report.json"
            with self.assertRaises(ValueError):
                auditor.audit_dataset(root, output, root / "temp.sqlite")
            self.assertFalse(output.exists())


    def test_workflow_is_pinned_offline_only_and_cleans_plaintext(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "dataset-value-audit.yml").read_text(encoding="utf-8")
        self.assertIn("run-id: 38116772719", workflow)
        self.assertIn("nifty-1m-composite-spot-recovery-38116772719", workflow)
        self.assertIn("HF_TOKEN:", workflow)
        self.assertIn("rm -rf", workflow)
        self.assertIn("research/data/DATASET_VALUE_AUDIT_RESULT.json", workflow)
        self.assertIn("PASS_WITH_COVERAGE_RESTRICTIONS", workflow)
        self.assertNotIn("api.dhan.co", workflow)
        self.assertNotIn("rollingoption", workflow)
        self.assertNotIn("model fitting or scoring performed", workflow.lower())

if __name__ == "__main__":
    unittest.main()
