#!/usr/bin/env python3
"""One-use, point-in-time safe Dhan daily NIFTY sample runner.

No request is made on import. This script is only invokable inside the reviewed
workflow after the approval gate is marked SPENT. It performs one daily-candle
POST, validates the raw response, writes a hashed cache bundle on success, and
always emits a redacted status report.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import tempfile
from typing import Any, Callable

import dhan_history_pipeline as pipeline

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/gates/DHAN_DAILY_SAMPLE_REQUEST.json"
APPROVAL_PATH = ROOT / "research/gates/DHAN_DAILY_SAMPLE_APPROVAL.json"
DEFAULT_CACHE_ROOT = ROOT / "data/cache/dhan_daily_sample"
DEFAULT_REPORT_PATH = ROOT / "data/reports/dhan_daily_sample_status.json"

DAILY_URL = "https://api.dhan.co/v2/charts/historical"
REQUEST_BODY = {
    "securityId": "13",
    "exchangeSegment": "IDX_I",
    "instrument": "INDEX",
    "fromDate": "2024-01-02",
    "toDate": "2024-01-03",
    "oi": False,
}
SCOPE_ID = "dhan-nifty50-daily-2024-01-02-one-request"
SAFE_CODE = re.compile(r"[a-zA-Z0-9_:-]{1,100}\Z")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json_atomic(path: pathlib.Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _load_json(path: pathlib.Path, error_code: str) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(error_code) from None
    if not isinstance(obj, dict):
        raise ValueError(error_code)
    return obj


def _safe_failure_code(exc: Exception) -> str:
    if isinstance(exc, (ValueError, RuntimeError)):
        value = str(exc)
        if SAFE_CODE.fullmatch(value):
            return value
    return f"runner_error_{type(exc).__name__}"


def _validate_local_spent_gate(manifest_path: pathlib.Path, approval_path: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest_raw = manifest_path.read_bytes()
    manifest = _load_json(manifest_path, "sample_manifest_unreadable")
    approval = _load_json(approval_path, "sample_approval_unreadable")
    manifest_sha = _sha256(manifest_raw)

    if manifest.get("status") != "PROPOSED" or manifest.get("decision") != "AWAITING_INDEPENDENT_MANIFEST_REVIEW":
        raise ValueError("sample_manifest_state_invalid")
    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict):
        raise ValueError("sample_authorization_missing")
    if authorization.get("scope_id") != SCOPE_ID:
        raise ValueError("sample_scope_mismatch")
    if authorization.get("source_url") != DAILY_URL or authorization.get("method") != "POST":
        raise ValueError("sample_endpoint_mismatch")
    if authorization.get("request_body") != REQUEST_BODY:
        raise ValueError("sample_request_body_mismatch")
    if (authorization.get("requests_max") != 1
            or authorization.get("response_bytes_max") != pipeline.MAX_RESPONSE_BYTES):
        raise ValueError("sample_budget_mismatch")
    if (authorization.get("redirect_follow_allowed") is not False
            or authorization.get("retry_allowed") is not False
            or authorization.get("full_history_authorized") is not False
            or authorization.get("feature_engineering_authorized") is not False
            or authorization.get("model_fitting_authorized") is not False
            or authorization.get("strategy_testing_authorized") is not False
            or authorization.get("holdout_access_authorized") is not False):
        raise ValueError("sample_forbidden_scope_flag")

    if approval.get("status") != "SPENT" or approval.get("decision") != "SPENT_BEFORE_SOURCE_REQUEST":
        raise ValueError("sample_approval_not_spent")
    if approval.get("request_manifest_sha256") != manifest_sha:
        raise ValueError("sample_manifest_hash_mismatch")
    if approval.get("request_manifest_git_blob") is None:
        raise ValueError("sample_manifest_blob_missing")
    if approval.get("approved_authorization_sha256") != manifest.get("authorization_sha256"):
        raise ValueError("sample_authorization_digest_mismatch")
    if approval.get("authorized_scope_id") != SCOPE_ID:
        raise ValueError("sample_approval_scope_mismatch")
    spent_from = approval.get("spent_from_commit")
    if not isinstance(spent_from, str) or not re.fullmatch(r"[0-9a-f]{40}", spent_from):
        raise ValueError("sample_spend_from_commit_missing")
    return manifest, approval, manifest_sha


def run_sample(
    *,
    env: dict[str, str] | None = None,
    opener_factory: Callable[[], Any] = pipeline._no_redirect_opener,
    manifest_path: pathlib.Path = MANIFEST_PATH,
    approval_path: pathlib.Path = APPROVAL_PATH,
    cache_root: pathlib.Path = DEFAULT_CACHE_ROOT,
    report_path: pathlib.Path = DEFAULT_REPORT_PATH,
    fetched_at_utc: str | None = None,
) -> int:
    """Execute one request only after workflow authorization and a spent manifest."""
    environment = dict(os.environ if env is None else env)
    budget = pipeline.RequestBudget(request_limit=1, byte_limit=pipeline.MAX_RESPONSE_BYTES)
    report: dict[str, Any] = {
        "schema_version": 1,
        "scope_id": SCOPE_ID,
        "status": "BLOCKED_BEFORE_REQUEST",
        "source_url": DAILY_URL,
        "request_parameters": REQUEST_BODY,
        "request_count": 0,
        "response_bytes": 0,
        "retry_count": 0,
        "redirect_followed": False,
        "raw_provider_error_saved": False,
        "cache_created": False,
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
        "github_run_id": environment.get("GITHUB_RUN_ID", ""),
        "github_sha": environment.get("GITHUB_SHA", ""),
    }
    try:
        if environment.get("DHAN_DAILY_SAMPLE_AUTHORIZED") != "1":
            raise ValueError("live_request_not_authorized")
        token = environment.get("DHAN_ACCESS_TOKEN", "")
        if not token:
            raise ValueError("missing_dhan_access_token")
        manifest, approval, manifest_sha = _validate_local_spent_gate(manifest_path, approval_path)
        report["request_manifest_sha256"] = manifest_sha
        report["approval_spent_from_commit"] = approval["spent_from_commit"]

        payload, metadata, raw_bytes = pipeline.request_json(
            DAILY_URL,
            REQUEST_BODY,
            token=token,
            budget=budget,
            opener_factory=opener_factory,
            live_authorized=True,
        )
        report["request_count"] = metadata["request_count"]
        report["response_bytes"] = metadata["response_bytes"]
        validation = pipeline.validate_candle_payload(payload)
        fetched_at = fetched_at_utc or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        cache_result = pipeline.atomic_cache_bundle(
            raw_bytes,
            validation,
            cache_root=cache_root,
            source_url=DAILY_URL,
            request_metadata=metadata,
            request_parameters=REQUEST_BODY,
            fetched_at_utc=fetched_at,
        )
        report.update({
            "status": "SOURCE_SAMPLE_VALIDATED",
            "http_status": metadata["http_status"],
            "content_type": metadata["content_type"],
            "response_sha256": metadata["response_sha256"],
            "validation": validation,
            "cache_created": cache_result["status"] == "CACHE_CREATED",
            "cache_status": cache_result["status"],
            "cache_bundle_name": pathlib.Path(cache_result["path"]).name,
            "fetched_at_utc": fetched_at,
            "retry_count": 0,
            "redirect_followed": False,
        })
        _write_json_atomic(report_path, report)
        print(json.dumps(report, sort_keys=True))
        return 0
    except Exception as exc:
        # Only fixed/internal failure codes are written. Never serialize exception
        # objects, headers, token values or raw provider error bodies.
        report.update({
            "status": "SOURCE_SAMPLE_FAILED_CLOSED",
            "failure_code": _safe_failure_code(exc),
            "request_count": budget.requests,
            "response_bytes": budget.bytes_read,
            "retry_count": 0,
            "redirect_followed": False,
            "raw_provider_error_saved": False,
            "cache_created": False,
        })
        _write_json_atomic(report_path, report)
        print(json.dumps(report, sort_keys=True))
        return 1


def main() -> int:
    return run_sample()


if __name__ == "__main__":
    raise SystemExit(main())
