#!/usr/bin/env python3
"""Offline/mock-only tests for the one-shot Dhan daily sample runner."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("run_dhan_daily_sample", SCRIPTS / "run_dhan_daily_sample.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

STAMP = 1704167100  # 2024-01-02 09:15:00 Asia/Kolkata
VALID_PAYLOAD = {
    "timestamp": [STAMP],
    "open": [21600.0], "high": [21650.0], "low": [21590.0],
    "close": [21630.0], "volume": [0],
}


class ReadTrackedBody(io.BytesIO):
    def __init__(self, initial_bytes: bytes):
        super().__init__(initial_bytes)
        self.read_count = 0

    def read(self, size: int = -1) -> bytes:
        self.read_count += 1
        return super().read(size)


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/json"):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
        self.read_calls = 0
        self.closed = False

    def read(self, size: int) -> bytes:
        self.read_calls += 1
        return self.body[:size]

    def close(self) -> None:
        self.closed = True


class FakeOpener:
    def __init__(self, response_or_exception):
        self.response_or_exception = response_or_exception
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        assert request.full_url == mod.DAILY_URL
        assert request.get_method() == "POST"
        assert timeout == 20
        return self._response(request)

    def _response(self, request):
        if isinstance(self.response_or_exception, Exception):
            raise self.response_or_exception
        return self.response_or_exception


def fixture_files(folder: pathlib.Path, *, approval_status: str = "SPENT"):
    manifest_path = folder / "request.json"
    approval_path = folder / "approval.json"
    authorization = {
        "scope_id": mod.SCOPE_ID,
        "authorized_scope": "one tiny daily NIFTY 50 index-history request only",
        "source_url": mod.DAILY_URL,
        "method": "POST",
        "request_body": json.loads(json.dumps(mod.REQUEST_BODY)),
        "requests_max": 1,
        "response_bytes_max": 2 * 1024 * 1024,
        "timeout_seconds": 20,
        "credential_host": "api.dhan.co",
        "credential_header": "access-token",
        "redirect_follow_allowed": False,
        "retry_allowed": False,
        "full_history_authorized": False,
        "intraday_authorized": False,
        "rolling_options_authorized": False,
        "feature_engineering_authorized": False,
        "model_fitting_authorized": False,
        "strategy_testing_authorized": False,
        "holdout_access_authorized": False,
        "protected_files": {},
    }
    auth_raw = json.dumps(authorization, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    manifest = {
        "schema_version": 1,
        "status": "PROPOSED",
        "decision": "AWAITING_INDEPENDENT_MANIFEST_REVIEW",
        "authorization": authorization,
        "authorization_sha256": hashlib.sha256(auth_raw).hexdigest(),
    }
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    manifest_path.write_bytes(raw)
    approval = {
        "status": approval_status,
        "decision": "SPENT_BEFORE_SOURCE_REQUEST",
        "approved_authorization_sha256": manifest["authorization_sha256"],
        "request_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "request_manifest_git_blob": "a" * 40,
        "authorized_scope_id": mod.SCOPE_ID,
        "spent_from_commit": "b" * 40,
    }
    approval_path.write_text(json.dumps(approval), encoding="utf-8")
    return manifest_path, approval_path


def run(folder: pathlib.Path, *, env: dict[str, str], opener_factory, response_path: pathlib.Path | None = None):
    manifest_path, approval_path = fixture_files(folder)
    cache = folder / "cache"
    report = response_path or folder / "reports" / "status.json"
    result = mod.run_sample(
        env=env,
        opener_factory=opener_factory,
        manifest_path=manifest_path,
        approval_path=approval_path,
        cache_root=cache,
        report_path=report,
        fetched_at_utc="2026-10-10T00:00:00Z",
    )
    return result, report, cache


def test_import_does_not_request_network() -> None:
    assert mod.DAILY_URL == "https://api.dhan.co/v2/charts/historical"
    assert mod.REQUEST_BODY["toDate"] == "2024-01-03"
    assert mod.REQUEST_BODY["fromDate"] == "2024-01-02"


def test_missing_workflow_flag_fails_before_opener() -> None:
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        calls = []
        code, report, cache = run(folder, env={"DHAN_ACCESS_TOKEN": "dummy"},
                                  opener_factory=lambda: calls.append("called"))
        result = json.loads(report.read_text())
        assert code == 1 and result["failure_code"] == "live_request_not_authorized"
        assert calls == [] and not cache.exists()


def test_missing_token_fails_before_opener() -> None:
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        calls = []
        code, report, cache = run(folder, env={"DHAN_DAILY_SAMPLE_AUTHORIZED": "1"},
                                  opener_factory=lambda: calls.append("called"))
        result = json.loads(report.read_text())
        assert code == 1 and result["failure_code"] == "missing_dhan_access_token"
        assert calls == [] and not cache.exists()


def test_unspent_or_tampered_manifest_fails_before_opener() -> None:
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        manifest, approval = fixture_files(folder, approval_status="READY")
        calls = []
        report = folder / "reports" / "status.json"
        code = mod.run_sample(
            env={"DHAN_DAILY_SAMPLE_AUTHORIZED": "1", "DHAN_ACCESS_TOKEN": "TEST_TOKEN"},
            opener_factory=lambda: calls.append("opened"),
            manifest_path=manifest, approval_path=approval, cache_root=folder / "cache",
            report_path=report,
        )
        result = json.loads(report.read_text())
        assert code == 1 and result["failure_code"] == "sample_approval_not_spent"
        assert calls == [] and not (folder / "cache").exists()

        approval_obj = json.loads(approval.read_text())
        approval_obj["status"] = "SPENT"
        approval_obj["request_manifest_sha256"] = "0" * 64
        approval.write_text(json.dumps(approval_obj), encoding="utf-8")
        code = mod.run_sample(
            env={"DHAN_DAILY_SAMPLE_AUTHORIZED": "1", "DHAN_ACCESS_TOKEN": "TEST_TOKEN"},
            opener_factory=lambda: calls.append("opened"),
            manifest_path=manifest, approval_path=approval, cache_root=folder / "cache",
            report_path=report,
        )
        result = json.loads(report.read_text())
        assert code == 1 and result["failure_code"] == "sample_manifest_hash_mismatch"
        assert calls == [] and not (folder / "cache").exists()

        # Even a matching raw manifest hash is not enough if the approval does
        # not endorse the manifest's frozen authorization digest.
        approval_obj["request_manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
        approval_obj["approved_authorization_sha256"] = "0" * 64
        approval.write_text(json.dumps(approval_obj), encoding="utf-8")
        code = mod.run_sample(
            env={"DHAN_DAILY_SAMPLE_AUTHORIZED": "1", "DHAN_ACCESS_TOKEN": "TEST_TOKEN"},
            opener_factory=lambda: calls.append("opened"),
            manifest_path=manifest, approval_path=approval, cache_root=folder / "cache",
            report_path=report,
        )
        result = json.loads(report.read_text())
        assert code == 1 and result["failure_code"] == "sample_authorization_digest_mismatch"
        assert calls == [] and not (folder / "cache").exists()


def test_one_valid_response_is_cached_once_without_secret_leak() -> None:
    raw = json.dumps(VALID_PAYLOAD, separators=(",", ":")).encode()
    response = FakeResponse(raw)
    opener = FakeOpener(response)
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        code, report, cache = run(
            folder,
            env={
                "DHAN_DAILY_SAMPLE_AUTHORIZED": "1",
                "DHAN_ACCESS_TOKEN": "TEST_ACCESS_TOKEN_DO_NOT_LEAK",
                "GITHUB_RUN_ID": "12345",
                "GITHUB_SHA": "c" * 40,
            },
            opener_factory=lambda: opener,
        )
        result = json.loads(report.read_text())
        assert code == 0 and result["status"] == "SOURCE_SAMPLE_VALIDATED"
        assert result["request_count"] == 1 and result["retry_count"] == 0
        assert result["validation"]["row_count"] == 1
        assert result["cache_created"] is True
        assert len(opener.calls) == 1 and response.read_calls == 1 and response.closed
        assert list(cache.rglob("response.json"))
        serialized = json.dumps(result)
        assert "TEST_ACCESS_TOKEN_DO_NOT_LEAK" not in serialized
        assert "Authorization" not in serialized and "Set-Cookie" not in serialized


def test_bad_json_or_bad_schema_fails_without_cache() -> None:
    for raw in (b"{not-json", b'{"status":"error"}'):
        with tempfile.TemporaryDirectory() as temp:
            folder = pathlib.Path(temp)
            response = FakeResponse(raw)
            opener = FakeOpener(response)
            code, report, cache = run(
                folder,
                env={"DHAN_DAILY_SAMPLE_AUTHORIZED": "1", "DHAN_ACCESS_TOKEN": "TEST_TOKEN"},
                opener_factory=lambda: opener,
            )
            result = json.loads(report.read_text())
            assert code == 1 and result["status"] == "SOURCE_SAMPLE_FAILED_CLOSED"
            assert result["request_count"] == 1 and not result["cache_created"]
            assert not cache.exists()
            assert "TEST_TOKEN" not in json.dumps(result)


def test_http_error_does_not_persist_provider_error_body() -> None:
    body = ReadTrackedBody(b"SECRET_PROVIDER_ERROR_BODY")
    error = urllib.error.HTTPError(
        mod.DAILY_URL, 403, "Forbidden",
        {"Content-Type": "application/json", "Authorization": "PRIVATE"},
        body,
    )
    with tempfile.TemporaryDirectory() as temp:
        folder = pathlib.Path(temp)
        code, report, cache = run(
            folder,
            env={"DHAN_DAILY_SAMPLE_AUTHORIZED": "1", "DHAN_ACCESS_TOKEN": "TEST_TOKEN"},
            opener_factory=lambda: FakeOpener(error),
        )
        result = json.loads(report.read_text())
        assert code == 1 and result["failure_code"] == "dhan_http_status_403"
        assert "SECRET_PROVIDER_ERROR_BODY" not in json.dumps(result)
        assert "PRIVATE" not in json.dumps(result)
        assert "TEST_TOKEN" not in json.dumps(result)
        assert body.read_count == 0 and not cache.exists()


TESTS = [value for name, value in globals().copy().items()
         if name.startswith("test_") and callable(value)]
for test in TESTS:
    test()
print(f"PASS {len(TESTS)} Dhan daily sample runner offline/mock tests")
