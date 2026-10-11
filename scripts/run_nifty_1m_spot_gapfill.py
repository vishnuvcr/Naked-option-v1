#!/usr/bin/env python3
"""Recover NIFTY spot candles and merge them into the previously obtained encrypted option dataset.

The base dataset is downloaded from the immutable encrypted artifact created by
the original acquisition. No rolling-option endpoint is called. The script checks
the original 8,490,723 option-row count, retrieves only the new 39-day spot
shards, fills exact-timestamp spot columns, appends SPOT rows, then encrypts all
monthly outputs. Plaintext only exists on the ephemeral Actions runner and is
never uploaded.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import heapq
import json
import os
import pathlib
import shutil
import time
import urllib.error
import urllib.request
from collections import Counter
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from run_nifty_1m_composite_dataset import (
    COLUMNS, CACHE_ROOT, ENCRYPTED_ROOT, EXPORT_ROOT, IST, PLAIN_ROOT, ROOT,
    UTC, NoRedirect, RequestPacer, _row_key, _safe_exception_reason, _value_string,
    atomic_write, canonical_sha256, derive_key, encrypt_outputs, get_cached_payload,
    load_json, parse_json_numbers, parse_spot_response, request_scope_hash,
    remove_invalid_cache, store_cached_payload, utc_now, _validate_request_payload,
)
# Reuse only the existing parser, schema, encryption and request-budget helpers from
# scripts/run_nifty_1m_composite_dataset.py. This runner itself makes intraday
# spot requests only; it never invokes the rolling-option endpoint.
import run_nifty_1m_composite_dataset as collector
import decrypt_nifty_1m_composite as decryptor
import validate_nifty_1m_spot_gapfill_split_proposal as split_proposal_validator

ROOT_MANIFEST = ROOT / "research/gates/NIFTY_1M_COMPOSITE_REQUEST_MANIFEST.json"
GAPFILL_MANIFEST = ROOT / "research/gates/NIFTY_1M_SPOT_GAPFILL_MANIFEST.json"
EXECUTION_MARKER = ROOT / "research/gates/NIFTY_1M_SPOT_RECOVERY_EXECUTION.json"
SPLIT_EXECUTION_MARKER = ROOT / "research/gates/NIFTY_1M_SPOT_SPLIT_RECOVERY_EXECUTION.json"
PREFLIGHT_RESULT = ROOT / "research/gates/NIFTY_1M_SPOT_GAPFILL_PREFLIGHT.json"
RECOVERY_RESULT = ROOT / "research/gates/NIFTY_1M_SPOT_RECOVERY_RESULT.json"
SPLIT_RECOVERY_RESULT = ROOT / "research/gates/NIFTY_1M_SPOT_SPLIT_RECOVERY_RESULT.json"
WORK_ROOT = ROOT / "data/work/nifty_1m_spot_gapfill"
REPORTS_ROOT = ROOT / "data/reports/nifty_1m_spot_gapfill"
ATTEMPT_LEDGER = REPORTS_ROOT / "attempt_ledger.json"
SPLIT_ATTEMPT_LEDGER = REPORTS_ROOT / "attempt_ledger_split.json"
IST = ZoneInfo("Asia/Kolkata")
TIMEOUT_SECONDS = 35
MIN_REQUEST_INTERVAL_SECONDS = 0.5
EXPECTED_OPTION_ROWS = 8_490_723
BASELINE_WIRE_ATTEMPTS = 8_606
DIAGNOSTIC_WIRE_ATTEMPTS = 1
BASELINE_RETRY_ATTEMPTS = 5


def _load_object(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top_level_object_required")
    return value


def _date(text: str) -> dt.date:
    return dt.date.fromisoformat(text)


def validate_gapfill_manifest(root: dict[str, Any]) -> list[dict[str, Any]]:
    plan = load_json(GAPFILL_MANIFEST)
    if plan.get("status") != "DRAFT_FOR_AUTOMATED_TESTER_REVIEW":
        raise ValueError("gapfill_manifest_status_must_remain_draft")
    if plan.get("source_family") != "NIFTY_SPOT_1M" or plan.get("live_option_requests_allowed") is not False:
        raise ValueError("gapfill_manifest_scope_must_be_spot_only")
    scope = plan.get("dataset_scope", {})
    start_expected = _date("2021-10-11")
    end_expected = _date("2026-10-11")
    if (_date(scope.get("history_start_inclusive", "")) != start_expected
            or _date(scope.get("history_end_exclusive", "")) != end_expected
            or scope.get("endpoint") != "https://api.dhan.co/v2/charts/intraday"):
        raise ValueError("gapfill_history_scope_mismatch")
    requests = plan.get("requests")
    if not isinstance(requests, list) or len(requests) != 47 or plan.get("planned_unique_requests") != 47:
        raise ValueError("gapfill_request_count_mismatch")
    if plan.get("chunk_calendar_days") != 39:
        raise ValueError("gapfill_chunk_size_mismatch")
    current = start_expected
    old_root_requests = []
    for entry in root.get("request_manifests", []):
        sub = load_json(ROOT / entry["path"])
        old_root_requests.extend(sub["requests"])
    old_scopes = {
        canonical_sha256({"endpoint": r["endpoint"], "method": r["method"], "body": r["body"]})
        for r in old_root_requests if r.get("source_family") == "NIFTY_SPOT_1M"
    }
    seen_ids = set()
    for request in requests:
        window_start = _date(request.get("window_start_inclusive", ""))
        window_end = _date(request.get("window_end_exclusive", ""))
        body = request.get("body", {})
        if window_start != current or window_end <= window_start:
            raise ValueError("gapfill_windows_have_gap_or_overlap")
        if (window_end - window_start).days > 39:
            raise ValueError("gapfill_window_exceeds_39_calendar_days")
        if (request.get("source_family") != "NIFTY_SPOT_1M"
                or request.get("endpoint") != "https://api.dhan.co/v2/charts/intraday"
                or request.get("method") != "POST"
                or request.get("max_response_bytes") != 8_388_608
                or request.get("max_rows") != 12_000
                or request.get("request_id") in seen_ids):
            raise ValueError("gapfill_request_scope_invalid")
        last_date = (window_end - dt.timedelta(days=1)).isoformat()
        if (body.get("securityId") != "13" or body.get("exchangeSegment") != "IDX_I"
                or body.get("instrument") != "INDEX" or body.get("interval") != "1"
                or body.get("oi") is not False
                or body.get("fromDate") != window_start.isoformat() + " 09:15:00"
                or body.get("toDate") != last_date + " 15:30:00"):
            raise ValueError("gapfill_request_body_invalid")
        scope_sha = canonical_sha256({"endpoint": request["endpoint"], "method": request["method"], "body": body})
        if scope_sha in old_scopes:
            raise ValueError("gapfill_repeats_prior_exact_request_scope")
        seen_ids.add(request["request_id"])
        current = window_end
    if current != end_expected:
        raise ValueError("gapfill_windows_do_not_cover_five_year_history")
    if (plan.get("maximum_wire_requests_this_run") != 94
            or plan.get("expected_wire_requests_cumulative_max") != 8_701
            or plan.get("prior_wire_requests_cumulative") != BASELINE_WIRE_ATTEMPTS
            or plan.get("diagnostic_wire_requests_additional") != DIAGNOSTIC_WIRE_ATTEMPTS
            or plan.get("prior_retry_requests_cumulative") != BASELINE_RETRY_ATTEMPTS
            or plan.get("max_retry_requests_this_run") != 47):
        raise ValueError("gapfill_budget_contract_invalid")
    if BASELINE_WIRE_ATTEMPTS + DIAGNOSTIC_WIRE_ATTEMPTS + 47 + 47 > 8_701:
        raise ValueError("gapfill_global_wire_budget_exceeded")
    if BASELINE_RETRY_ATTEMPTS + 47 > 100:
        raise ValueError("gapfill_global_retry_budget_exceeded")
    return requests


def _count_rows(parts: list[pathlib.Path]) -> tuple[int, int, dict[str, int]]:
    option_rows = 0
    spot_rows = 0
    rows_by_month: Counter[str] = Counter()
    for path in parts:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != COLUMNS:
                raise ValueError("original_dataset_csv_schema_mismatch")
            for row in reader:
                if row.get("row_type") == "OPTION":
                    option_rows += 1
                    rows_by_month[path.name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz")] += 1
                elif row.get("row_type") == "SPOT":
                    spot_rows += 1
                else:
                    raise ValueError("original_dataset_has_unknown_row_type")
    return option_rows, spot_rows, dict(rows_by_month)


def _normalize_artifact_layout(source_dir: pathlib.Path) -> pathlib.Path:
    """Create a metadata + encrypted-part view of the Actions artifact.

    upload-artifact preserves the 'encrypted/' directory while the embedded
    dataset manifest lists encrypted part basenames. The existing decryptor
    expects those basenames at the input root. Use symlinks in scratch space
    rather than rewriting the immutable downloaded artifact or duplicating its
    encrypted bytes.
    """
    if not source_dir.is_dir():
        raise FileNotFoundError("original_encrypted_artifact_directory_missing")
    manifests = [p for p in source_dir.rglob("dataset_manifest.json") if p.is_file()]
    if len(manifests) != 1:
        raise FileNotFoundError("original_dataset_manifest_missing_or_ambiguous")
    manifest_path = manifests[0]
    manifest = _load_object(manifest_path)
    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("original_dataset_manifest_parts_invalid")
    view = WORK_ROOT / "source_artifact_view"
    if view.exists() or view.is_symlink():
        if view.is_dir() and not view.is_symlink():
            shutil.rmtree(view)
        else:
            view.unlink()
    view.mkdir(parents=True, exist_ok=True)

    # Attach safe metadata files by basename.
    for name in ("dataset_manifest.json", "coverage_and_errors.json", "README.md"):
        candidates = [p for p in source_dir.rglob(name) if p.is_file()]
        if name == "dataset_manifest.json":
            source_file = manifest_path
        elif candidates:
            source_file = candidates[0]
        else:
            continue
        target = view / name
        target.symlink_to(source_file.resolve())

    for part in parts:
        name = str(part.get("file", ""))
        if not name.endswith(".csv.gz.enc") or pathlib.Path(name).name != name:
            raise ValueError("unsafe_original_encrypted_part_name")
        matches = [p for p in source_dir.rglob(name) if p.is_file()]
        if len(matches) != 1:
            raise FileNotFoundError("original_encrypted_part_missing_or_ambiguous")
        (view / name).symlink_to(matches[0].resolve())
    return view


def preflight(
    source_dir: pathlib.Path,
    plain_dir: pathlib.Path,
    hf_token: str,
    expected_spot_rows: int = 0,
    expected_artifact_run_id: int = 38082385220,
) -> dict[str, Any]:
    if not hf_token:
        raise ValueError("HF_TOKEN_NOT_CONFIGURED")
    source_dir = _normalize_artifact_layout(source_dir)
    source_manifest = decryptor.read_manifest(source_dir)
    if (source_manifest.get("download_bundle_contains_encrypted_data_only") is not True
            or source_manifest.get("source_row_count_options") != EXPECTED_OPTION_ROWS
            or int(source_manifest.get("source_row_count_spot", -1)) != expected_spot_rows):
        raise ValueError("base_artifact_manifest_scope_or_row_count_mismatch")
    key = derive_key(hf_token)
    parts = decryptor.decrypt_dataset(source_dir, plain_dir, key, overwrite=True)
    actual_options, actual_spot, rows_by_month = _count_rows(parts)
    if actual_options != EXPECTED_OPTION_ROWS:
        raise ValueError("base_artifact_option_row_count_mismatch")
    if actual_spot != expected_spot_rows:
        raise ValueError("base_artifact_spot_row_count_mismatch")
    coverage_path = source_dir / "coverage_and_errors.json"
    source_coverage = _load_object(coverage_path)
    source_summary = source_coverage.get("summary", {})
    if (int(source_summary.get("rows_options", -1)) != EXPECTED_OPTION_ROWS
            or int(source_summary.get("rows_spot", -1)) != expected_spot_rows):
        raise ValueError("base_coverage_summary_mismatch")
    return {
        "schema_version": 1,
        "status": "PASS",
        "base_artifact_run_id": expected_artifact_run_id,
        "encrypted_parts_verified": len(parts),
        "option_rows_verified": actual_options,
        "spot_rows_in_base": actual_spot,
        "monthly_parts_with_options": len(rows_by_month),
        "raw_market_values_logged": False,
        "plaintext_uploaded": False,
    }


def _read_ledger(path: pathlib.Path = ATTEMPT_LEDGER) -> dict[str, Any]:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return {"schema_version": 1, "wire_attempts_new": 0, "retry_attempts_new": 0,
                "attempts_by_request_id": {}, "failures": {}, "updated_at_utc": utc_now()}
    try:
        ledger = _load_object(path)
        if ledger.get("schema_version") != 1:
            raise ValueError
        return ledger
    except Exception:
        raise ValueError("gapfill_attempt_ledger_corrupt_fail_closed") from None


def _save_ledger(ledger: dict[str, Any], path: pathlib.Path = ATTEMPT_LEDGER) -> None:
    ledger["updated_at_utc"] = utc_now()
    atomic_write(path, (json.dumps(ledger, sort_keys=True, indent=2) + "\n").encode("utf-8"))


class SpotGapFillCollector:
    def __init__(
        self,
        token: str,
        key: bytes,
        requests: list[dict[str, Any]],
        ledger: dict[str, Any],
        baseline_wire_attempts: int = BASELINE_WIRE_ATTEMPTS,
        baseline_retry_attempts: int = BASELINE_RETRY_ATTEMPTS,
        ledger_path: pathlib.Path = ATTEMPT_LEDGER,
    ):
        self.token = token
        self.key = key
        self.requests = requests
        self.ledger = ledger
        self.baseline_wire_attempts = baseline_wire_attempts
        self.baseline_retry_attempts = baseline_retry_attempts
        self.ledger_path = ledger_path
        self.pacer = RequestPacer(MIN_REQUEST_INTERVAL_SECONDS)
        self.spot_by_epoch: dict[int, dict[str, str]] = {}
        self.handles: dict[str, tuple[Any, Any]] = {}
        self.request_results: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.rows_spot = 0
        self.cache_hits = 0
        self.fresh_responses = 0
        self.downloaded_bytes = 0
        self.retry_attempts_this_run = 0
        self.auth_failed = False

    def _append_spot_row(self, row: dict[str, Any]) -> None:
        month = row.get("timestamp_ist", "")[:7]
        if len(month) != 7:
            raise ValueError("gapfill_spot_month_missing")
        path = WORK_ROOT / ("spot_rows_" + month + ".csv.gz")
        if month not in self.handles:
            handle = gzip.open(path, "wt", encoding="utf-8", newline="", compresslevel=6)
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            self.handles[month] = (handle, writer)
        handle, writer = self.handles[month]
        writer.writerow(row)

    def _record_attempt(self, request: dict[str, Any], is_retry: bool) -> None:
        wire_now = self.baseline_wire_attempts + DIAGNOSTIC_WIRE_ATTEMPTS + int(self.ledger["wire_attempts_new"])
        retry_now = self.baseline_retry_attempts + int(self.ledger["retry_attempts_new"])
        if wire_now >= 8_701:
            raise ValueError("gapfill_global_wire_budget_exhausted")
        if is_retry and retry_now >= 100:
            raise ValueError("gapfill_global_retry_budget_exhausted")
        attempts = int(self.ledger["attempts_by_request_id"].get(request["request_id"], 0))
        if attempts >= 2:
            raise ValueError("gapfill_request_attempt_budget_exhausted")
        self.ledger["wire_attempts_new"] += 1
        self.ledger["attempts_by_request_id"][request["request_id"]] = attempts + 1
        if is_retry:
            self.ledger["retry_attempts_new"] += 1
            self.retry_attempts_this_run += 1
        _save_ledger(self.ledger, self.ledger_path)

    def _charge_downloaded_bytes(self, size: int) -> None:
        if size < 0:
            raise ValueError("spot_response_byte_count_invalid")
        if self.downloaded_bytes + size > 268_435_456:
            raise ValueError("spot_aggregate_byte_budget_exceeded")
        self.downloaded_bytes += size

    def _http_fetch(self, request: dict[str, Any], is_retry: bool = False) -> tuple[bytes, int, str]:
        self.pacer.wait()
        self._record_attempt(request, is_retry)
        body = json.dumps(request["body"], separators=(",", ":"), sort_keys=True).encode("utf-8")
        req = urllib.request.Request(
            request["endpoint"], data=body, method="POST",
            headers={"Accept": "application/json", "Content-Type": "application/json",
                     "access-token": self.token, "User-Agent": "Naked-option-v1-spot-gapfill/1.0"},
        )
        try:
            response = urllib.request.build_opener(NoRedirect()).open(req, timeout=TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            content_type = str(exc.headers.get("Content-Type", "")) if exc.headers else ""
            try:
                exc.close()
            except OSError:
                pass
            raise collector.SourceRequestError("http_status_" + str(status), status) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise collector.SourceRequestError("transport_error_" + type(exc).__name__) from None
        try:
            status = int(getattr(response, "status", 0))
            content_type = str(getattr(response, "headers", {}).get("Content-Type", ""))
            raw = response.read(int(request["max_response_bytes"]) + 1)
            # Charge every body read before size/content-type/JSON/schema validation.
            # A malformed response must not bypass the aggregate transfer budget.
            self._charge_downloaded_bytes(len(raw))
            if len(raw) > int(request["max_response_bytes"]):
                raise collector.SourceRequestError("response_byte_cap_exceeded", status)
            if not (200 <= status < 300):
                raise collector.SourceRequestError("http_status_" + str(status), status)
            if "json" not in content_type.lower():
                raise collector.SourceRequestError("unexpected_content_type", status)
            return raw, status, content_type
        finally:
            try:
                response.close()
            except Exception:
                pass

    def _get_payload(self, request: dict[str, Any]) -> tuple[dict[str, Any] | None, str, str, int | None, int]:
        if self.auth_failed:
            self.errors.append(self._error_record(request, "skipped_after_dhan_auth_or_entitlement_failure", None))
            return None, "SKIPPED_AUTH_FAILURE", "", None, 0
        cached = get_cached_payload(request, self.key)
        if cached is not None:
            raw, meta = cached
            try:
                payload = parse_json_numbers(raw)
                _validate_request_payload(payload, request)
                return payload, "CACHE_HIT", meta["response_sha256"], int(meta.get("http_status", 200)), len(raw)
            except Exception:
                remove_invalid_cache(request)
        previous_attempts = int(self.ledger["attempts_by_request_id"].get(request["request_id"], 0))
        maximum_attempts = int(request.get("max_attempts", 2))
        if maximum_attempts not in (1, 2):
            raise ValueError("gapfill_max_attempts_invalid")
        retry_allowed = previous_attempts < maximum_attempts
        if not retry_allowed:
            return None, "FAILED_REQUEST", "", None, 0
        try:
            raw, status, content_type = self._http_fetch(request, is_retry=previous_attempts > 0)
        except collector.SourceRequestError as exc:
            status_code = exc.http_status
            if status_code in (401, 403) or exc.reason.startswith("dhan_api_auth_or_entitlement"):
                self.auth_failed = True
                self.errors.append(self._error_record(request, "dhan_auth_or_entitlement_failure", status_code))
                return None, "DHAN_AUTH_FAILURE", "", status_code, 0
            retryable = (status_code == 429 or (status_code is not None and 500 <= status_code <= 599)
                         or exc.reason.startswith("transport_error_"))
            if retryable and previous_attempts + 1 < maximum_attempts:
                try:
                    raw, status, content_type = self._http_fetch(request, is_retry=True)
                except collector.SourceRequestError as retry_exc:
                    if retry_exc.http_status in (401, 403) or retry_exc.reason.startswith("dhan_api_auth_or_entitlement"):
                        self.auth_failed = True
                        reason = "dhan_auth_or_entitlement_failure"
                    else:
                        reason = retry_exc.reason
                    self.errors.append(self._error_record(request, reason, retry_exc.http_status))
                    return None, "DHAN_AUTH_FAILURE" if self.auth_failed else "FAILED_REQUEST", "", retry_exc.http_status, 0
            else:
                self.errors.append(self._error_record(request, exc.reason, status_code))
                return None, "FAILED_REQUEST", "", status_code, 0
        try:
            payload = parse_json_numbers(raw)
            _validate_request_payload(payload, request)
            rows, problems = parse_spot_response(payload, request)
            digest = collector.sha256_bytes(raw)
            cached_meta = store_cached_payload(request, raw, self.key, status, len(rows), content_type)
            return payload, "FETCHED_AFTER_ONE_RETRY" if self.ledger["attempts_by_request_id"].get(request["request_id"], 0) > 1 else "FETCHED", cached_meta["response_sha256"], status, len(raw)
        except Exception as exc:
            if isinstance(exc, collector.SourceRequestError) and exc.reason.startswith("dhan_api_auth_or_entitlement"):
                self.auth_failed = True
                self.errors.append(self._error_record(request, "dhan_auth_or_entitlement_failure", exc.http_status))
                return None, "DHAN_AUTH_FAILURE", "", exc.http_status, len(raw)
            self.errors.append(self._error_record(request, _safe_exception_reason(exc), status))
            return None, "FAILED_VALIDATION", "", status, len(raw)

    @staticmethod
    def _error_record(request: dict[str, Any], reason: str, status: int | None) -> dict[str, Any]:
        return {
            "request_id": request.get("request_id", ""),
            "source_family": "NIFTY_SPOT_1M_GAPFILL",
            "window_start_inclusive": request.get("window_start_inclusive", ""),
            "window_end_exclusive": request.get("window_end_exclusive", ""),
            "status": "ERROR",
            "reason": str(reason)[:120],
            "http_status": status,
            "request_scope_sha256": request_scope_hash(request),
            "endpoint": request["endpoint"],
        }

    def collect(self) -> dict[str, Any]:
        WORK_ROOT.mkdir(parents=True, exist_ok=True)
        for request in self.requests:
            payload, cache_status, digest, status_code, size = self._get_payload(request)
            result = {
                "request_id": request["request_id"],
                "source_family": "NIFTY_SPOT_1M_GAPFILL",
                "window_start_inclusive": request["window_start_inclusive"],
                "window_end_exclusive": request["window_end_exclusive"],
                "status": cache_status,
                "http_status": status_code,
                "response_bytes": size,
                "response_sha256": digest,
                "request_scope_sha256": request_scope_hash(request),
                "cache_status": cache_status,
            }
            self.request_results.append(result)
            if payload is None:
                continue
            try:
                rows, problems = parse_spot_response(payload, request)
                for row in rows:
                    row["response_sha256"] = digest
                    row["cache_status"] = cache_status
                    self._append_spot_row(row)
                    epoch = int(row["timestamp_epoch"])
                    if epoch in self.spot_by_epoch:
                        row["data_quality_flags"] = "|".join(filter(None, [
                            row.get("data_quality_flags", ""),
                            "DUPLICATE_TIMESTAMP_ACROSS_GAPFILL_WINDOWS"
                        ]))
                    self.spot_by_epoch[epoch] = {
                        k: str(row.get(k, "")) for k in (
                            "nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume",
                            "data_quality_flags", "source_request_id", "response_sha256", "cache_status"
                        )
                    }
                self.rows_spot += len(rows)
                self.cache_hits += int(cache_status == "CACHE_HIT")
                self.fresh_responses += int(cache_status.startswith("FETCHED"))
                result["row_count"] = len(rows)
                result["quality_flags"] = sorted(set(
                    flag for row in rows for flag in row.get("data_quality_flags", "").split("|") if flag
                ))
                if problems:
                    self.errors.append(self._error_record(request, "spot_volume_missing_or_misaligned", status_code))
            except Exception as exc:
                result["status"] = "FAILED_VALIDATION"
                self.errors.append(self._error_record(request, _safe_exception_reason(exc), status_code))
        for handle, _writer in self.handles.values():
            try:
                handle.close()
            except Exception:
                pass
        self.handles.clear()
        return {
            "rows_spot": self.rows_spot,
            "spot_by_epoch": self.spot_by_epoch,
            "request_results": self.request_results,
            "errors": self.errors,
            "cache_hits": self.cache_hits,
            "fresh_responses": self.fresh_responses,
            "downloaded_bytes": self.downloaded_bytes,
            "wire_requests_this_run": int(self.ledger["wire_attempts_new"]),
            "retry_requests_this_run": int(self.ledger["retry_attempts_new"]),
            "wire_requests_cumulative": self.baseline_wire_attempts + DIAGNOSTIC_WIRE_ATTEMPTS + int(self.ledger["wire_attempts_new"]),
            "retry_requests_cumulative": self.baseline_retry_attempts + int(self.ledger["retry_attempts_new"]),
            "attempt_ledger": self.ledger,
        }


def _iter_gzip_rows(path: pathlib.Path) -> Iterable[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ValueError("monthly_csv_schema_mismatch")
        yield from reader


def _add_quality_flag(existing: str, flag: str) -> str:
    values = [item for item in str(existing or "").split("|") if item]
    if flag and flag not in values:
        values.append(flag)
    return "|".join(values)


def _remove_quality_flag(existing: str, flag: str) -> str:
    return "|".join(item for item in str(existing or "").split("|") if item and item != flag)


def _enriched_option_rows(
    path: pathlib.Path,
    spot_map: dict[int, dict[str, str]],
    counters: Counter,
    preserve_existing_spot_rows: bool = False,
) -> Iterable[dict[str, str]]:
    for row in _iter_gzip_rows(path):
        if row.get("row_type") == "SPOT":
            if preserve_existing_spot_rows:
                yield row
            continue
        if row.get("row_type") != "OPTION":
            raise ValueError("unknown_original_row_type")
        counters["rows_options"] += 1
        epoch = int(row["timestamp_epoch"])
        spot = spot_map.get(epoch)
        if spot is None and preserve_existing_spot_rows and row.get("spot_join_status") == "EXACT_TIMESTAMP_MATCH":
            if any(row.get(field, "") for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close")):
                counters["spot_join_matched"] += 1
                yield row
                continue
        if spot is None:
            for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"):
                row[field] = ""
            row["spot_join_status"] = "NO_EXACT_TIMESTAMP_SPOT_MATCH"
            row["data_quality_flags"] = _add_quality_flag(row.get("data_quality_flags", ""), "SPOT_JOIN_MISSING")
            counters["spot_join_missing"] += 1
        else:
            for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume"):
                row[field] = spot.get(field, "")
            row["spot_join_status"] = "EXACT_TIMESTAMP_MATCH"
            row["data_quality_flags"] = _remove_quality_flag(row.get("data_quality_flags", ""), "SPOT_JOIN_MISSING")
            counters["spot_join_matched"] += 1
            if "SPOT_VOLUME_MISSING_OR_MISALIGNED" in spot.get("data_quality_flags", ""):
                row["data_quality_flags"] = _add_quality_flag(row.get("data_quality_flags", ""), "SPOT_VOLUME_MISSING_OR_MISALIGNED")
        yield row


def _month_from_filename(path: pathlib.Path) -> str:
    return path.name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz")


def merge_into_existing_dataset(
    base_parts: list[pathlib.Path],
    spot_dir: pathlib.Path,
    spot_map: dict[int, dict[str, str]],
    preserve_existing_spot_rows: bool = False,
) -> tuple[dict[str, int], Counter]:
    if PLAIN_ROOT.exists():
        shutil.rmtree(PLAIN_ROOT)
    PLAIN_ROOT.mkdir(parents=True, exist_ok=True)
    base_by_month = {_month_from_filename(path): path for path in base_parts}
    spot_by_month = {path.name.removeprefix("spot_rows_").removesuffix(".csv.gz"): path
                     for path in spot_dir.glob("spot_rows_*.csv.gz")}
    months = sorted(set(base_by_month) | set(spot_by_month))
    row_count_by_month: Counter[str] = Counter()
    counters: Counter = Counter()
    for month in months:
        option_path = base_by_month.get(month)
        spot_path = spot_by_month.get(month)
        if spot_path is not None:
            spot_rows = _iter_gzip_rows(spot_path)
        else:
            spot_rows = iter(())
        if option_path is not None:
            option_rows = _enriched_option_rows(
                option_path, spot_map, counters,
                preserve_existing_spot_rows=preserve_existing_spot_rows,
            )
        else:
            option_rows = iter(())
        merged = heapq.merge(option_rows, spot_rows, key=_row_key)
        destination = PLAIN_ROOT / ("nifty_1m_composite_" + month + ".csv.gz")
        with gzip.open(destination, "wt", encoding="utf-8", newline="", compresslevel=6) as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for row in merged:
                writer.writerow(row)
                row_count_by_month[month] += 1
                counters["rows_spot_out" if row.get("row_type") == "SPOT" else "rows_options_out"] += 1
    return dict(row_count_by_month), counters


def execute(args: argparse.Namespace) -> int:
    token = os.environ.get("DHAN_ACCESS_TOKEN", "").strip()
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not token or not hf_token:
        raise ValueError("required_secret_not_configured")
    marker = _load_object(EXECUTION_MARKER)
    if (marker.get("status") != "SPENT_BEFORE_SOURCE_REQUEST"
            or marker.get("scope") != "SPOT_ONLY_ARTIFACT_PRESERVING_GAPFILL"
            or marker.get("reviewed_developer_commit") != args.reviewed_sha
            or marker.get("max_spot_requests") != 61
            or marker.get("max_gapfill_requests") != 47
            or marker.get("gapfill_manifest_sha256") != collector.sha256_bytes(GAPFILL_MANIFEST.read_bytes())
            or marker.get("live_option_requests_allowed") is not False
            or marker.get("tester_decision_blob") is None):
        raise ValueError("gapfill_execution_marker_missing_or_scope_mismatch")
    root = load_json(ROOT_MANIFEST)
    requests = validate_gapfill_manifest(root)
    source_dir = args.source_dir.resolve()
    plain_dir = args.plain_dir.resolve()
    preflight_result = preflight(source_dir, plain_dir, hf_token)
    if preflight_result.get("status") != "PASS":
        raise ValueError("encrypted_original_artifact_preflight_failed")
    normalized_source_dir = _normalize_artifact_layout(source_dir)
    old_coverage = _load_object(normalized_source_dir / "coverage_and_errors.json")
    old_manifest = decryptor.read_manifest(normalized_source_dir)
    key = derive_key(hf_token)

    # Clear only temporary new spot rows, never the downloaded source artifact or the original data.
    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    if ENCRYPTED_ROOT.exists():
        shutil.rmtree(ENCRYPTED_ROOT)
    ledger = _read_ledger()
    collector_obj = SpotGapFillCollector(token, key, requests, ledger)
    gap = collector_obj.collect()

    row_counts, join_counts = merge_into_existing_dataset(
        [path for path in plain_dir.glob("nifty_1m_composite_*.csv.gz")],
        WORK_ROOT,
        gap["spot_by_epoch"],
    )
    rows_options = int(join_counts["rows_options_out"])
    rows_spot_out = int(join_counts["rows_spot_out"])
    if rows_options != EXPECTED_OPTION_ROWS:
        raise ValueError("merged_option_row_count_changed")
    old_summary = old_coverage.get("summary", {})
    new_spot_requests_ok = sum(
        result.get("status") in {"CACHE_HIT", "FETCHED", "FETCHED_AFTER_ONE_RETRY"}
        for result in gap["request_results"]
    )
    gapfill_complete = (
        new_spot_requests_ok == len(requests)
        and rows_spot_out == gap["rows_spot"]
        and rows_options == EXPECTED_OPTION_ROWS
        and int(join_counts["spot_join_missing"]) == 0
    )
    spot_status = "SPOT_GAPFILL_COMPLETE" if gapfill_complete else "SPOT_GAPFILL_PARTIAL"
    original_errors = old_coverage.get("errors", [])
    original_results = old_coverage.get("request_results", [])
    errors = list(original_errors) + gap["errors"]
    results = list(original_results) + gap["request_results"]
    session_dates = set()
    for path in PLAIN_ROOT.glob("nifty_1m_composite_*.csv.gz"):
        # The output header is already validated by the writer; inspect SPOT rows only.
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("row_type") == "SPOT":
                    session_dates.add(row.get("session_date", ""))
    summary = {
        **{k: old_summary.get(k) for k in (
            "request_count_planned", "failed_responses", "empty_valid_responses",
            "missing_greek_inputs", "observed_trading_session_count"
        )},
        "request_count_processed": int(old_summary.get("request_count_processed", 0)) + len(requests),
        "gapfill_request_count_planned": len(requests),
        "gapfill_request_count_succeeded": new_spot_requests_ok,
        "gapfill_request_count_failed": len(requests) - new_spot_requests_ok,
        "wire_requests_this_run": gap["wire_requests_this_run"],
        "wire_requests_cumulative": gap["wire_requests_cumulative"],
        "retry_requests_this_run": gap["retry_requests_this_run"],
        "retry_requests_cumulative": gap["retry_requests_cumulative"],
        "rows_options": rows_options,
        "original_rows_options": EXPECTED_OPTION_ROWS,
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "rows_spot": rows_spot_out,
        "spot_rows_downloaded": gap["rows_spot"],
        "spot_join_matched": int(join_counts["spot_join_matched"]),
        "spot_join_missing": int(join_counts["spot_join_missing"]),
        "spot_recovery_status": spot_status,
        "spot_volume_quality_flag_count": sum(
            "SPOT_VOLUME_MISSING_OR_MISALIGNED" in v.get("data_quality_flags", "")
            for v in gap["spot_by_epoch"].values()
        ),
        "observed_trading_session_count": len(session_dates),
        "cache_hits": gap["cache_hits"],
        "fresh_responses": gap["fresh_responses"],
        "downloaded_bytes": gap["downloaded_bytes"],
        "historical_option_request_grid_status": old_coverage.get("status", "PARTIAL_GRID"),
        "source_requests_made_this_run": gap["wire_requests_this_run"],
        "live_option_requests_allowed": False,
        "raw_response_persisted_unencrypted": False,
    }
    original_columns = old_manifest.get("columns", COLUMNS)
    result = {
        "schema_version": 1,
        "dataset_id": "NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_SPOT_GAPFILL",
        "created_at_utc": utc_now(),
        "status": "PARTIAL_GRID",
        "spot_gapfill_status": spot_status,
        "source_provider": "DhanHQ Data API",
        "history_start_inclusive": "2021-10-11",
        "history_end_exclusive": "2026-10-11",
        "interval": "1-minute",
        "user_acceptance": "Preserve previously acquired option rows from immutable encrypted source artifact; fill spot fields using separate Dhan spot-only request shards. No live option requests performed.",
        "schema_columns": list(original_columns),
        "rows_per_month": dict(sorted(row_counts.items())),
        "summary": summary,
        "errors": errors,
        "request_results": results,
        "gapfill_request_results": gap["request_results"],
        "original_request_failures_preserved": len(original_errors),
        "missing_greek_inputs": old_coverage.get("missing_greek_inputs", []),
        "greek_method": old_coverage.get("greek_method", old_manifest.get("greek_method", "")),
        "greek_iv_unit_convention": old_coverage.get("greek_iv_unit_convention", old_manifest.get("greek_iv_unit_convention", "")),
        "spot_join_policy": "Exact timestamp_epoch match from new Dhan spot bars. Rolling option spot remains a separate provider field. Only exact matches populate NIFTY OHLCV; non-matching option rows stay blank and are explicitly flagged.",
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
        "strategy_testing_authorized": False,
        "source_artifact_run_id": 38082385220,
        "source_artifact_encrypted_hashes_verified": True,
        "source_rows_options_verified": EXPECTED_OPTION_ROWS,
        "plain_rows_uploaded": False,
    }
    encrypt_outputs(key, result)
    # Remove artifact plaintext and gapfill scratch material; only encrypted outputs survive.
    shutil.rmtree(plain_dir, ignore_errors=True)
    shutil.rmtree(WORK_ROOT, ignore_errors=True)
    shutil.rmtree(ROOT / "data/recovery/source-artifact", ignore_errors=True)
    result_safe = {
        "schema_version": 1,
        "result_type": "SPOT_ONLY_ARTIFACT_PRESERVING_GAPFILL",
        "status": spot_status,
        "reviewed_developer_commit": args.reviewed_sha,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "summary": summary,
        "source_rows_options_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "source_artifact_hashes_verified": True,
        "live_option_requests_allowed": False,
        "raw_market_values_committed": False,
        "completed_at_utc": utc_now(),
    }
    atomic_write(RECOVERY_RESULT, (json.dumps(result_safe, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({
        "status": spot_status,
        "source_artifact_hashes_verified": True,
        "original_option_rows": EXPECTED_OPTION_ROWS,
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "spot_rows": rows_spot_out,
        "spot_join_matched": int(join_counts["spot_join_matched"]),
        "spot_join_missing": int(join_counts["spot_join_missing"]),
        "gapfill_requests_planned": len(requests),
        "gapfill_requests_succeeded": new_spot_requests_ok,
        "gapfill_requests_failed": len(requests) - new_spot_requests_ok,
        "wire_requests_this_run": gap["wire_requests_this_run"],
        "wire_requests_cumulative": gap["wire_requests_cumulative"],
        "retry_requests_this_run": gap["retry_requests_this_run"],
        "retry_requests_cumulative": gap["retry_requests_cumulative"],
        "live_option_requests_allowed": False,
        "raw_market_values_logged": False,
    }, sort_keys=True))
    return 0 if gapfill_complete else 2


def _git_blob_sha(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def execute_split(args: argparse.Namespace) -> int:
    token = os.environ.get("DHAN_ACCESS_TOKEN", "").strip()
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not token or not hf_token:
        raise ValueError("required_secret_not_configured")
    proposal_path = args.split_proposal.resolve()
    proposal = split_proposal_validator.load_json(proposal_path)
    proposal_errors = split_proposal_validator.validate_proposal(proposal)
    if proposal_errors:
        raise ValueError("split_proposal_invalid:" + ",".join(proposal_errors[:8]))
    if not args.proposal_blob_sha or _git_blob_sha(proposal_path) != args.proposal_blob_sha:
        raise ValueError("split_proposal_blob_sha_mismatch")
    marker = _load_object(SPLIT_EXECUTION_MARKER)
    if (marker.get("status") != "SPENT_BEFORE_SOURCE_REQUEST"
            or marker.get("scope") != "SPLIT_SPOT_ONLY_ARTIFACT_PRESERVING_GAPFILL"
            or marker.get("reviewed_developer_commit") != args.reviewed_sha
            or marker.get("split_proposal_blob_sha") != args.proposal_blob_sha
            or marker.get("max_spot_requests") != 34
            or marker.get("max_gapfill_requests") != 34
            or marker.get("max_retry_requests") != 0
            or marker.get("base_artifact_id") != "11693866249"
            or marker.get("base_artifact_sha256") != "aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216"
            or marker.get("live_option_requests_allowed") is not False
            or marker.get("tester_decision_blob") is None):
        raise ValueError("split_execution_marker_missing_or_scope_mismatch")

    requests = proposal["requests"]
    base = proposal["base_partial_artifact"]
    source_dir = args.source_dir.resolve()
    plain_dir = args.plain_dir.resolve()
    base_spot_rows = int(proposal["expected_existing_spot_rows"])
    preflight_result = preflight(
        source_dir, plain_dir, hf_token,
        expected_spot_rows=base_spot_rows,
        expected_artifact_run_id=int(base["run_id"]),
    )
    if preflight_result.get("status") != "PASS":
        raise ValueError("encrypted_partial_artifact_preflight_failed")
    normalized_source_dir = _normalize_artifact_layout(source_dir)
    old_coverage = _load_object(normalized_source_dir / "coverage_and_errors.json")
    old_manifest = decryptor.read_manifest(normalized_source_dir)
    key = derive_key(hf_token)

    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    if ENCRYPTED_ROOT.exists():
        shutil.rmtree(ENCRYPTED_ROOT)
    ledger_path = args.split_ledger.resolve()
    ledger = _read_ledger(ledger_path)
    collector_obj = SpotGapFillCollector(
        token, key, requests, ledger,
        baseline_wire_attempts=8_653,
        baseline_retry_attempts=5,
        ledger_path=ledger_path,
    )
    gap = collector_obj.collect()

    old_gapfill_results = old_coverage.get("gapfill_request_results", [])
    if not isinstance(old_gapfill_results, list) or len(old_gapfill_results) != 47:
        raise ValueError("partial_base_gapfill_history_missing")
    row_counts, join_counts = merge_into_existing_dataset(
        [path for path in plain_dir.glob("nifty_1m_composite_*.csv.gz")],
        WORK_ROOT,
        gap["spot_by_epoch"],
        preserve_existing_spot_rows=True,
    )
    rows_options = int(join_counts["rows_options_out"])
    rows_spot_out = int(join_counts["rows_spot_out"])
    if rows_options != EXPECTED_OPTION_ROWS:
        raise ValueError("merged_option_row_count_changed")
    if rows_spot_out != base_spot_rows + int(gap["rows_spot"]):
        raise ValueError("merged_existing_spot_row_count_changed")
    old_summary = old_coverage.get("summary", {})
    new_spot_requests_ok = sum(
        result.get("status") in {"CACHE_HIT", "FETCHED", "FETCHED_AFTER_ONE_RETRY"}
        for result in gap["request_results"]
    )
    split_complete = (
        new_spot_requests_ok == len(requests)
        and rows_spot_out == base_spot_rows + int(gap["rows_spot"])
        and rows_options == EXPECTED_OPTION_ROWS
        and int(join_counts["spot_join_missing"]) == 0
    )
    spot_status = "SPOT_GAPFILL_COMPLETE" if split_complete else "SPOT_GAPFILL_PARTIAL"
    original_errors = old_coverage.get("errors", [])
    original_results = old_coverage.get("request_results", [])
    errors = list(original_errors) + gap["errors"]
    results = list(original_results) + gap["request_results"]
    session_dates = set()
    for path in PLAIN_ROOT.glob("nifty_1m_composite_*.csv.gz"):
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("row_type") == "SPOT":
                    session_dates.add(row.get("session_date", ""))

    previous_response_bytes = sum(int(item.get("response_bytes") or 0) for item in old_gapfill_results)
    previous_gapfill_planned = int(old_summary.get("gapfill_request_count_planned", 47))
    previous_gapfill_succeeded = int(old_summary.get("gapfill_request_count_succeeded", 41))
    previous_gapfill_failed = int(old_summary.get("gapfill_request_count_failed", 6))
    summary = {
        **{k: old_summary.get(k) for k in (
            "request_count_planned", "failed_responses", "empty_valid_responses",
            "missing_greek_inputs", "observed_trading_session_count"
        )},
        "request_count_processed": int(old_summary.get("request_count_processed", 0)) + len(requests),
        "gapfill_request_count_planned": len(requests),
        "gapfill_request_count_succeeded": new_spot_requests_ok,
        "gapfill_request_count_failed": len(requests) - new_spot_requests_ok,
        "gapfill_request_count_cumulative_planned": previous_gapfill_planned + len(requests),
        "gapfill_request_count_cumulative_succeeded": previous_gapfill_succeeded + new_spot_requests_ok,
        "gapfill_request_count_cumulative_failed": previous_gapfill_failed + len(requests) - new_spot_requests_ok,
        "wire_requests_this_run": gap["wire_requests_this_run"],
        "wire_requests_cumulative": gap["wire_requests_cumulative"],
        "retry_requests_this_run": gap["retry_requests_this_run"],
        "retry_requests_cumulative": gap["retry_requests_cumulative"],
        "rows_options": rows_options,
        "original_rows_options": EXPECTED_OPTION_ROWS,
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "rows_spot": rows_spot_out,
        "spot_rows_existing_preserved": base_spot_rows,
        "spot_rows_downloaded": int(gap["rows_spot"]),
        "spot_join_matched": int(join_counts["spot_join_matched"]),
        "spot_join_missing": int(join_counts["spot_join_missing"]),
        "spot_recovery_status": spot_status,
        "spot_volume_quality_flag_count": int(old_summary.get("spot_volume_quality_flag_count", 0)) + sum(
            "SPOT_VOLUME_MISSING_OR_MISALIGNED" in v.get("data_quality_flags", "")
            for v in gap["spot_by_epoch"].values()
        ),
        "observed_trading_session_count": len(session_dates),
        "cache_hits": int(old_summary.get("cache_hits", 0)) + gap["cache_hits"],
        "fresh_responses": int(old_summary.get("fresh_responses", 0)) + gap["fresh_responses"],
        "downloaded_bytes": previous_response_bytes + gap["downloaded_bytes"],
        "previous_downloaded_bytes_reconciled_from_request_results": True,
        "historical_option_request_grid_status": old_coverage.get("status", "PARTIAL_GRID"),
        "source_requests_made_this_run": gap["wire_requests_this_run"],
        "live_option_requests_allowed": False,
        "raw_response_persisted_unencrypted": False,
    }
    result = {
        "schema_version": 1,
        "dataset_id": "NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_SPOT_GAPFILL",
        "created_at_utc": utc_now(),
        "status": "PARTIAL_GRID",
        "spot_gapfill_status": spot_status,
        "source_provider": "DhanHQ Data API",
        "history_start_inclusive": "2021-10-11",
        "history_end_exclusive": "2026-10-11",
        "interval": "1-minute",
        "user_acceptance": "Preserve the latest partial encrypted dataset, including existing spot rows, and request only the six previously failed spot-window interval splits. No rolling-option requests are permitted.",
        "schema_columns": list(old_manifest.get("columns", COLUMNS)),
        "rows_per_month": dict(sorted(row_counts.items())),
        "summary": summary,
        "errors": errors,
        "request_results": results,
        "gapfill_request_results": gap["request_results"],
        "previous_gapfill_request_results": old_gapfill_results,
        "original_request_failures_preserved": old_coverage.get("original_request_failures_preserved", len(original_errors)),
        "missing_greek_inputs": old_coverage.get("missing_greek_inputs", []),
        "greek_method": old_coverage.get("greek_method", old_manifest.get("greek_method", "")),
        "greek_iv_unit_convention": old_coverage.get("greek_iv_unit_convention", old_manifest.get("greek_iv_unit_convention", "")),
        "spot_join_policy": "Exact timestamp_epoch match from newly recovered spot bars. Existing exact spot joins and standalone SPOT rows are preserved. Non-matching option rows remain blank and flagged.",
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
        "strategy_testing_authorized": False,
        "source_artifact_run_id": old_coverage.get("source_artifact_run_id", 38082385220),
        "base_partial_artifact_run_id": int(base["run_id"]),
        "base_partial_artifact_id": str(base["artifact_id"]),
        "split_proposal_blob_sha": args.proposal_blob_sha,
        "source_artifact_encrypted_hashes_verified": True,
        "source_rows_options_verified": EXPECTED_OPTION_ROWS,
        "source_rows_spot_preserved": rows_spot_out >= base_spot_rows,
        "plain_rows_uploaded": False,
    }
    encrypt_outputs(key, result)
    shutil.rmtree(plain_dir, ignore_errors=True)
    shutil.rmtree(WORK_ROOT, ignore_errors=True)
    shutil.rmtree(ROOT / "data/recovery/source-artifact", ignore_errors=True)
    result_safe = {
        "schema_version": 1,
        "result_type": "SPOT_ONLY_SPLIT_GAPFILL",
        "status": spot_status,
        "reviewed_developer_commit": args.reviewed_sha,
        "split_proposal_blob_sha": args.proposal_blob_sha,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "summary": summary,
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "existing_spot_rows_preserved": rows_spot_out >= base_spot_rows,
        "base_partial_artifact_id": str(base["artifact_id"]),
        "live_option_requests_allowed": False,
        "raw_market_values_committed": False,
        "completed_at_utc": utc_now(),
    }
    atomic_write(SPLIT_RECOVERY_RESULT, (json.dumps(result_safe, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({
        "status": spot_status,
        "original_option_rows": EXPECTED_OPTION_ROWS,
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "existing_spot_rows_preserved": rows_spot_out >= base_spot_rows,
        "spot_rows_total": rows_spot_out,
        "spot_rows_new": int(gap["rows_spot"]),
        "spot_join_matched": int(join_counts["spot_join_matched"]),
        "spot_join_missing": int(join_counts["spot_join_missing"]),
        "gapfill_requests_planned": len(requests),
        "gapfill_requests_succeeded": new_spot_requests_ok,
        "gapfill_requests_failed": len(requests) - new_spot_requests_ok,
        "wire_requests_this_run": gap["wire_requests_this_run"],
        "wire_requests_cumulative": gap["wire_requests_cumulative"],
        "retry_requests_this_run": gap["retry_requests_this_run"],
        "retry_requests_cumulative": gap["retry_requests_cumulative"],
        "live_option_requests_allowed": False,
        "raw_market_values_logged": False,
    }, sort_keys=True))
    return 0 if split_complete else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=pathlib.Path, required=True)
    parser.add_argument("--plain-dir", type=pathlib.Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--preflight-output", type=pathlib.Path, default=PREFLIGHT_RESULT)
    parser.add_argument("--reviewed-sha", default="")
    parser.add_argument("--split-proposal", type=pathlib.Path)
    parser.add_argument("--proposal-blob-sha", default="")
    parser.add_argument("--split-ledger", type=pathlib.Path, default=SPLIT_ATTEMPT_LEDGER)
    args = parser.parse_args()
    root = load_json(ROOT_MANIFEST)
    validate_gapfill_manifest(root)
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if args.preflight_only == args.execute:
        raise SystemExit("choose_exactly_one_of_preflight_only_or_execute")
    if args.preflight_only:
        if args.split_proposal is not None:
            raise SystemExit("split_proposal_cannot_use_original_preflight_mode")
        result = preflight(args.source_dir.resolve(), args.plain_dir.resolve(), hf_token)
        atomic_write(args.preflight_output, (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8"))
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("status") == "PASS" else 1
    if args.split_proposal is not None:
        return execute_split(args)
    return execute(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("INTERRUPTED: no unencrypted market data is uploaded.")
        raise SystemExit(130)
    except Exception as exc:
        print("SPOT_GAPFILL_ERROR " + type(exc).__name__ + ":" + _safe_exception_reason(exc))
        raise SystemExit(1)
