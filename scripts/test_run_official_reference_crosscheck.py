#!/usr/bin/env python3
"""Offline/mocked tests for the one-use official-reference cross-check runner."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("run_official_reference_crosscheck", SCRIPTS / "run_official_reference_crosscheck.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

CSV_HEADER = (
    "SEM_SMST_SECURITY_ID,SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_INSTRUMENT_NAME,"
    "SEM_TRADING_SYMBOL,SM_SYMBOL_NAME,SEM_CUSTOM_SYMBOL,SEM_EXCH_INSTRUMENT_TYPE\n"
)
CSV = (CSV_HEADER + "13,NSE,E,INDEX,NIFTY,NIFTY 50,NIFTY 50,IDX\n").encode()
NIFTY_ROW = {
    "INDEX_NAME": "NIFTY 50",
    "HistoricalDate": "02 Jan 2024",
    "OPEN": "21751.35",
    "HIGH": "21755.60",
    "LOW": "21555.65",
    "CLOSE": "21665.80",
}
NIFTY_RAW = json.dumps({"d": json.dumps([NIFTY_ROW])}).encode()


class FakeResponse:
    def __init__(self, body: bytes, *, content_type: str):
        self.body = body
        self.status = 200
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
        self.read_calls = 0
        self.closed = False

    def read(self, size: int) -> bytes:
        self.read_calls += 1
        return self.body[:size]

    def close(self):
        self.closed = True


class SequentialOpener:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        assert self.results, "unexpected extra source request"
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def source_specs():
    return [
        {
            "source": "nifty_indices",
            "url": mod.adapter.NIFTY_INDICES_URL,
            "method": "POST",
            "request_count_max": 1,
            "response_bytes_max": mod.adapter.NIFTY_MAX_RESPONSE_BYTES,
            "timeout_seconds": mod.adapter.NIFTY_TIMEOUT_SECONDS,
            "redirect_follow_allowed": False,
            "retry_allowed": False,
            "credential_allowed": False,
        },
        {
            "source": "dhan_instrument_master",
            "url": mod.adapter.DHAN_COMPACT_MASTER_URL,
            "method": "GET",
            "request_count_max": 1,
            "response_bytes_max": mod.adapter.MAX_CSV_BYTES,
            "timeout_seconds": mod.adapter.DHAN_MASTER_TIMEOUT_SECONDS,
            "redirect_follow_allowed": False,
            "retry_allowed": False,
            "credential_allowed": False,
        },
    ]


def canonical(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def fixtures(folder: pathlib.Path, *, approval_status: str = "SPENT", override: dict | None = None):
    manifest_path = folder / "request.json"
    approval_path = folder / "approval.json"
    auth = {
        "scope_id": mod.SCOPE_ID,
        "source_specs": source_specs(),
        "expected_date": mod.adapter.EXPECTED_DATE,
        "expected_dhan_row": mod.adapter.EXPECTED_DHAN_ROW,
        "expected_mapping": mod.adapter.EXPECTED_MAPPING,
    }
    manifest = {
        "schema_version": 1,
        "status": "PROPOSED",
        "decision": "AWAITING_INDEPENDENT_MANIFEST_REVIEW",
        "authorization": auth,
        "authorization_sha256": canonical(auth),
    }
    if override:
        manifest.update(override)
    raw = (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    manifest_path.write_bytes(raw)
    approval = {
        "status": approval_status,
        "decision": "SPENT_BEFORE_SOURCE_REQUEST" if approval_status == "SPENT" else "APPROVED_ONE_RUN",
        "scope_id": mod.SCOPE_ID,
        "authorized_scope_id": mod.SCOPE_ID,
        "request_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "approved_authorization_sha256": manifest["authorization_sha256"],
        "spent_from_commit": "a" * 40,
    }
    approval_path.write_text(json.dumps(approval), encoding="utf-8")
    return manifest_path, approval_path


def call(folder: pathlib.Path, *, env: dict, opener: SequentialOpener, nifty_raw=NIFTY_RAW, csv_raw=CSV):
    manifest, approval = fixtures(folder)
    responses = [
        FakeResponse(nifty_raw, content_type="application/json"),
        FakeResponse(csv_raw, content_type="text/csv"),
    ]
    opener.results = responses if opener is None else opener.results
    cache = folder / "cache"
    report = folder / "reports" / "status.json"
    code = mod.run_crosscheck(
        env=env, opener_factory=lambda: opener,
        manifest_path=manifest, approval_path=approval,
        cache_root=cache, report_path=report,
        fetched_at_utc="2026-10-10T00:00:00Z",
    )
    return code, report, cache, manifest, approval, responses


def test_live_cli_requires_explicit_flag_and_workflow_authorization() -> None:
    import os
    from unittest.mock import patch
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OFFICIAL_CROSSCHECK_AUTHORIZED", None)
        assert mod.main(["--live"]) == 1
        assert mod.main(["--unexpected"]) == 2


def test_import_and_cli_are_offline_only() -> None:
    assert mod.SCOPE_ID == "dhan-sample-official-crosscheck-2024-01-02-two-hosts"
    assert mod.main() == 0


def test_missing_workflow_flag_and_unspent_approval_fail_before_network() -> None:
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        opener = SequentialOpener([])
        code, report, cache, *_ = call(folder, env={}, opener=opener)
        out = json.loads(report.read_text())
        assert code == 1 and out["failure_code"] == "crosscheck_live_request_not_authorized"
        assert not opener.calls and not cache.exists()
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        manifest, approval = fixtures(folder, approval_status="READY")
        opener = SequentialOpener([])
        report = folder / "status.json"
        code = mod.run_crosscheck(
            env={"OFFICIAL_CROSSCHECK_AUTHORIZED": "1"}, opener_factory=lambda: opener,
            manifest_path=manifest, approval_path=approval, cache_root=folder / "cache", report_path=report
        )
        out = json.loads(report.read_text())
        assert code == 1 and out["failure_code"] == "crosscheck_approval_not_spent"
        assert not opener.calls and not (folder / "cache").exists()


def test_wrong_manifest_digest_scope_or_source_spec_fails_before_network() -> None:
    cases = [
        ({"authorization_sha256": "0" * 64}, "crosscheck_authorization_digest_mismatch"),
        ({"authorization": {"scope_id": "wrong"}}, "crosscheck_scope_mismatch"),
        ({"authorization": {"expected_date": "2024-01-03"}}, "crosscheck_expected_date_mismatch"),
        ({"authorization": {"source_specs": []}}, "crosscheck_source_scope_mismatch"),
    ]
    for change, expected in cases:
        with tempfile.TemporaryDirectory() as temp:
            folder = pathlib.Path(temp)
            manifest, approval = fixtures(folder)
            m = json.loads(manifest.read_text())
            if "authorization" in change:
                m["authorization"].update(change["authorization"])
                m["authorization_sha256"] = canonical(m["authorization"])
            else:
                m.update(change)
            manifest.write_text(json.dumps(m, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
            # Re-pin approval raw-manifest hash, so the target validation path is reached.
            a = json.loads(approval.read_text())
            a["request_manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
            a["approved_authorization_sha256"] = m["authorization_sha256"]
            approval.write_text(json.dumps(a), encoding="utf-8")
            opener = SequentialOpener([])
            report = folder / "status.json"
            code = mod.run_crosscheck(env={"OFFICIAL_CROSSCHECK_AUTHORIZED": "1"}, opener_factory=lambda: opener,
                manifest_path=manifest, approval_path=approval, cache_root=folder / "cache", report_path=report)
            out = json.loads(report.read_text())
            assert code == 1 and out["failure_code"] == expected, (expected, out)
            assert not opener.calls and not (folder / "cache").exists()


def test_success_fetches_each_host_once_and_caches_only_after_match() -> None:
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        opener = SequentialOpener([
            FakeResponse(NIFTY_RAW, content_type="application/json"),
            FakeResponse(CSV, content_type="text/csv"),
        ])
        code, report, cache, manifest, approval, _ = call(
            folder, env={"OFFICIAL_CROSSCHECK_AUTHORIZED": "1", "GITHUB_RUN_ID": "run-safe"},
            opener=opener
        )
        out = json.loads(report.read_text())
        assert code == 0 and out["status"] == "OFFICIAL_CROSSCHECK_MATCHED"
        assert out["request_count"] == 2 and out["retry_count"] == 0
        assert out["credentials_sent"] is False and out["data_accepted_for_prediction"] is False
        assert out["ohlc_comparison"]["status"] == "MATCH"
        assert out["cache_created"] is True and len(list(cache.glob("*"))) == 1
        assert len(opener.calls) == 2 and not opener.results
        first, second = opener.calls
        assert first[0].full_url == mod.adapter.NIFTY_INDICES_URL and first[0].get_method() == "POST"
        assert second[0].full_url == mod.adapter.DHAN_COMPACT_MASTER_URL and second[0].get_method() == "GET"
        for req, _ in opener.calls:
            headers = {key.lower() for key, _ in req.header_items()}
            assert not headers.intersection({"authorization", "access-token", "cookie", "dhanclientid"})
        assert "NIFTY" in json.dumps(out) and "raw_provider_error" not in json.dumps(out)
        bundle = next(cache.iterdir())
        saved = json.loads((bundle / "manifest.json").read_text())
        assert saved["data_accepted_for_prediction"] is False
        assert hashlib.sha256((bundle / "nifty_indices_response.json").read_bytes()).hexdigest() == saved["raw_sources"]["nifty_indices_response"]["sha256"]
        assert hashlib.sha256((bundle / "dhan_instrument_master.csv").read_bytes()).hexdigest() == saved["raw_sources"]["dhan_instrument_master"]["sha256"]


def test_ohlc_mismatch_and_mapping_mismatch_never_create_cache() -> None:
    wrong_nifty_row = {**NIFTY_ROW, "CLOSE": "21665.81"}
    wrong_nifty = json.dumps({"d": json.dumps([wrong_nifty_row])}).encode()
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        opener = SequentialOpener([
            FakeResponse(wrong_nifty, content_type="application/json"),
            FakeResponse(CSV, content_type="text/csv"),
        ])
        code, report, cache, *_ = call(folder, env={"OFFICIAL_CROSSCHECK_AUTHORIZED": "1"}, opener=opener, nifty_raw=wrong_nifty)
        out = json.loads(report.read_text())
        assert code == 1 and out["failure_code"] == "official_nifty_ohlc_mismatch"
        assert not cache.exists() or not list(cache.iterdir())
    bad_csv = (CSV_HEADER + "13,BSE,E,INDEX,NIFTY,NIFTY 50,NIFTY 50,IDX\n").encode()
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        opener = SequentialOpener([
            FakeResponse(NIFTY_RAW, content_type="application/json"),
            FakeResponse(bad_csv, content_type="text/csv"),
        ])
        code, report, cache, *_ = call(folder, env={"OFFICIAL_CROSSCHECK_AUTHORIZED": "1"}, opener=opener, csv_raw=bad_csv)
        out = json.loads(report.read_text())
        assert code == 1 and out["failure_code"] == "dhan_mapping_exchange_mismatch"
        assert not cache.exists() or not list(cache.iterdir())


def test_second_source_failure_preserves_no_partial_cache_and_safe_report() -> None:
    import urllib.error
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        err = urllib.error.HTTPError(mod.adapter.DHAN_COMPACT_MASTER_URL, 403, "Forbidden", {"Content-Type":"text/plain"}, io.BytesIO(b"PRIVATE_ERROR"))
        opener = SequentialOpener([FakeResponse(NIFTY_RAW, content_type="application/json"), err])
        code, report, cache, *_ = call(folder, env={"OFFICIAL_CROSSCHECK_AUTHORIZED":"1"}, opener=opener)
        out = json.loads(report.read_text())
        assert code == 1 and out["failure_code"] == "dhan_instrument_master_http_status_403"
        assert len(opener.calls) == 2 and not cache.exists()
        assert "PRIVATE_ERROR" not in json.dumps(out) and out["credentials_sent"] is False


TESTS = [v for k, v in globals().copy().items() if k.startswith("test_") and callable(v)]
for test in TESTS:
    test()
print(f"PASS {len(TESTS)} official reference cross-check runner offline/mock tests")
