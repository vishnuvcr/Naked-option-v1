#!/usr/bin/env python3
"""One-use official-source cross-check of the already cached 2024-01-02 NIFTY row.

No request occurs on import or via normal CLI use. The live workflow must first
verify a separately tester-approved manifest and push its approval as SPENT.
This program never sends a Dhan token or other credentials to either source.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import sys
import tempfile
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import official_reference_crosscheck as adapter

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_REQUEST.json"
APPROVAL_PATH = ROOT / "research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_APPROVAL.json"
DEFAULT_CACHE_ROOT = ROOT / "data/cache/dhan_sample_official_crosscheck"
DEFAULT_REPORT_PATH = ROOT / "data/reports/dhan_sample_official_crosscheck_status.json"
DEFAULT_DHAN_SAMPLE_BUNDLE = ROOT / "data/cache/dhan_daily_sample/478f0942f8654bd763b8343a05370f8065ef5041483cb59cc3f7dd6b57ef78ba-efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70"
DEFAULT_DHAN_SAMPLE_RESPONSE_PATH = DEFAULT_DHAN_SAMPLE_BUNDLE / "response.json"
DEFAULT_DHAN_SAMPLE_MANIFEST_PATH = DEFAULT_DHAN_SAMPLE_BUNDLE / "manifest.json"
SAFE_CODE = re.compile(r"[a-zA-Z0-9_:-]{1,120}\Z")
SCOPE_ID = adapter.EXPECTED_SCOPE_ID


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json_atomic(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise


def _load_json(path: pathlib.Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(code) from None
    if not isinstance(value, dict):
        raise ValueError(code)
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256(raw)


def _verify_spent_approval(
    manifest_path: pathlib.Path,
    approval_path: pathlib.Path,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    raw = manifest_path.read_bytes()
    manifest = _load_json(manifest_path, "crosscheck_manifest_unreadable")
    approval = _load_json(approval_path, "crosscheck_approval_unreadable")
    digest = _sha256(raw)
    auth = manifest.get("authorization")
    if not isinstance(auth, dict):
        raise ValueError("crosscheck_authorization_missing")
    if manifest.get("status") != "PROPOSED" or manifest.get("decision") != "AWAITING_INDEPENDENT_MANIFEST_REVIEW":
        raise ValueError("crosscheck_manifest_state_invalid")
    if auth.get("scope_id") != SCOPE_ID:
        raise ValueError("crosscheck_scope_mismatch")
    if manifest.get("authorization_sha256") != _canonical_sha256(auth):
        raise ValueError("crosscheck_authorization_digest_mismatch")
    if approval.get("status") != "SPENT" or approval.get("decision") != "SPENT_BEFORE_SOURCE_REQUEST":
        raise ValueError("crosscheck_approval_not_spent")
    if approval.get("scope_id") != SCOPE_ID or approval.get("authorized_scope_id") != SCOPE_ID:
        raise ValueError("crosscheck_approval_scope_mismatch")
    if approval.get("request_manifest_sha256") != digest:
        raise ValueError("crosscheck_manifest_hash_mismatch")
    if approval.get("approved_authorization_sha256") != manifest.get("authorization_sha256"):
        raise ValueError("crosscheck_approval_authorization_digest_mismatch")
    spent_from = approval.get("spent_from_commit")
    if not isinstance(spent_from, str) or not re.fullmatch(r"[0-9a-f]{40}", spent_from):
        raise ValueError("crosscheck_spent_from_commit_invalid")
    if auth.get("source_specs") != [
        {
            "source": "nifty_indices",
            "url": adapter.NIFTY_INDICES_URL,
            "method": "POST",
            "request_count_max": 1,
            "response_bytes_max": adapter.NIFTY_MAX_RESPONSE_BYTES,
            "timeout_seconds": adapter.NIFTY_TIMEOUT_SECONDS,
            "redirect_follow_allowed": False,
            "retry_allowed": False,
            "credential_allowed": False,
        },
        {
            "source": "dhan_instrument_master",
            "url": adapter.DHAN_COMPACT_MASTER_URL,
            "method": "GET",
            "request_count_max": 1,
            "response_bytes_max": adapter.MAX_CSV_BYTES,
            "timeout_seconds": adapter.DHAN_MASTER_TIMEOUT_SECONDS,
            "redirect_follow_allowed": False,
            "retry_allowed": False,
            "credential_allowed": False,
        },
    ]:
        raise ValueError("crosscheck_source_scope_mismatch")
    if auth.get("expected_date") != adapter.EXPECTED_DATE:
        raise ValueError("crosscheck_expected_date_mismatch")
    if auth.get("expected_dhan_row") != adapter.EXPECTED_DHAN_ROW:
        raise ValueError("crosscheck_expected_dhan_row_mismatch")
    if auth.get("dhan_sample_response_sha256") != adapter.EXPECTED_DHAN_SAMPLE_RESPONSE_SHA256:
        raise ValueError("crosscheck_dhan_sample_hash_scope_mismatch")
    if auth.get("expected_mapping") != adapter.EXPECTED_MAPPING:
        raise ValueError("crosscheck_expected_mapping_mismatch")
    return manifest, approval, digest


def _load_verified_dhan_sample(
    response_path: pathlib.Path,
    manifest_path: pathlib.Path,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Load the existing cached source bytes, never compare only against Python literals."""
    try:
        raw = response_path.read_bytes()
    except OSError:
        raise ValueError("crosscheck_cached_dhan_sample_missing") from None
    response_hash = _sha256(raw)
    if response_hash != adapter.EXPECTED_DHAN_SAMPLE_RESPONSE_SHA256:
        raise ValueError("crosscheck_cached_dhan_sample_hash_mismatch")
    try:
        manifest_raw = manifest_path.read_bytes()
    except OSError:
        raise ValueError("crosscheck_cached_dhan_manifest_missing") from None
    cache_manifest = _load_json(manifest_path, "crosscheck_cached_dhan_manifest_invalid")

    expected_params = adapter.EXPECTED_DHAN_SAMPLE_PARAMS
    metadata = cache_manifest.get("request_metadata")
    if (cache_manifest.get("schema_version") != 1
            or cache_manifest.get("source_url") != "https://api.dhan.co/v2/charts/historical"
            or cache_manifest.get("request_parameters") != expected_params
            or cache_manifest.get("response_sha256") != response_hash
            or cache_manifest.get("response_bytes") != len(raw)
            or not isinstance(metadata, dict)
            or metadata.get("http_status") != 200
            or metadata.get("content_type") != "application/json"
            or metadata.get("request_count") != 1
            or metadata.get("response_bytes") != len(raw)
            or metadata.get("cumulative_response_bytes") != len(raw)
            or metadata.get("response_sha256") != response_hash):
        raise ValueError("crosscheck_cached_dhan_manifest_mismatch")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("crosscheck_cached_dhan_json_invalid") from None
    if not isinstance(payload, dict):
        raise ValueError("crosscheck_cached_dhan_payload_invalid")
    required = ("timestamp", "open", "high", "low", "close", "volume")
    for key in required:
        if not isinstance(payload.get(key), list) or len(payload[key]) != 1:
            raise ValueError("crosscheck_cached_dhan_array_invalid")
    try:
        timestamp_value = float(payload["timestamp"][0])
    except (TypeError, ValueError, OverflowError):
        raise ValueError("crosscheck_cached_dhan_timestamp_invalid") from None
    if not math.isfinite(timestamp_value) or timestamp_value <= 0 or not timestamp_value.is_integer():
        raise ValueError("crosscheck_cached_dhan_timestamp_invalid")
    timestamp = int(timestamp_value)
    india = dt.timezone(dt.timedelta(hours=5, minutes=30))
    local_date = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).astimezone(india).date().isoformat()
    if local_date != adapter.EXPECTED_DATE:
        raise ValueError("crosscheck_cached_dhan_date_mismatch")

    row: dict[str, str] = {}
    for key in ("open", "high", "low", "close"):
        value = payload[key][0]
        if isinstance(value, bool):
            raise ValueError("crosscheck_cached_dhan_numeric_invalid")
        try:
            numeric = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("crosscheck_cached_dhan_numeric_invalid") from None
        if not numeric.is_finite():
            raise ValueError("crosscheck_cached_dhan_numeric_invalid")
        row[key] = format(numeric, ".2f")
    volume_value = payload["volume"][0]
    if isinstance(volume_value, bool):
        raise ValueError("crosscheck_cached_dhan_volume_invalid")
    try:
        volume_decimal = Decimal(str(volume_value))
    except (InvalidOperation, ValueError):
        raise ValueError("crosscheck_cached_dhan_volume_invalid") from None
    if not volume_decimal.is_finite() or volume_decimal < 0 or volume_decimal != volume_decimal.to_integral_value():
        raise ValueError("crosscheck_cached_dhan_volume_invalid")
    row["volume"] = str(int(volume_decimal))
    if row != adapter.EXPECTED_DHAN_ROW:
        raise ValueError("crosscheck_cached_dhan_row_mismatch")

    validation = cache_manifest.get("validation")
    if (not isinstance(validation, dict)
            or validation.get("row_count") != 1
            or validation.get("first_timestamp") != timestamp
            or validation.get("last_timestamp") != timestamp):
        raise ValueError("crosscheck_cached_dhan_validation_mismatch")
    return row, {
        "response_sha256": response_hash,
        "response_bytes": len(raw),
        "cache_manifest_sha256": _sha256(manifest_raw),
        "timestamp": timestamp,
        "local_date": local_date,
        "row": row,
    }


def _safe_failure_code(exc: Exception) -> str:
    if isinstance(exc, (ValueError, RuntimeError)):
        code = str(exc)
        if SAFE_CODE.fullmatch(code):
            return code
    return f"crosscheck_error_{type(exc).__name__}"


def _atomic_bundle(
    *,
    nifty_raw: bytes,
    master_raw: bytes,
    nifty_meta: dict[str, Any],
    master_meta: dict[str, Any],
    nifty_row: dict[str, str],
    master_row: dict[str, str],
    comparison: dict[str, Any],
    manifest_sha256: str,
    dhan_sample_row: dict[str, str],
    dhan_sample_response_sha256: str,
    dhan_sample_manifest_sha256: str,
    cache_root: pathlib.Path,
    fetched_at_utc: str,
) -> dict[str, Any]:
    if comparison.get("status") != "MATCH" or comparison.get("mismatch_count") != 0:
        raise ValueError("crosscheck_comparison_not_match")
    expected_nifty_hash = nifty_meta.get("response_sha256")
    expected_master_hash = master_meta.get("response_sha256")
    if expected_nifty_hash != _sha256(nifty_raw) or expected_master_hash != _sha256(master_raw):
        raise ValueError("crosscheck_raw_hash_mismatch")
    if nifty_meta.get("response_bytes") != len(nifty_raw) or master_meta.get("response_bytes") != len(master_raw):
        raise ValueError("crosscheck_raw_byte_count_mismatch")

    cache_root.mkdir(parents=True, exist_ok=True)
    bundle_name = f"{expected_nifty_hash}-{expected_master_hash}"
    final_dir = cache_root / bundle_name
    if final_dir.exists():
        existing_nifty = final_dir / "nifty_indices_response.json"
        existing_master = final_dir / "dhan_instrument_master.csv"
        existing_manifest_path = final_dir / "manifest.json"
        if (not existing_nifty.is_file() or not existing_master.is_file()
                or _sha256(existing_nifty.read_bytes()) != expected_nifty_hash
                or _sha256(existing_master.read_bytes()) != expected_master_hash):
            raise ValueError("crosscheck_cache_collision")
        existing_manifest = _load_json(existing_manifest_path, "crosscheck_existing_manifest_invalid")
        raw_sources = {
            "nifty_indices_response": {
                "path": "nifty_indices_response.json",
                "sha256": expected_nifty_hash,
                "bytes": len(nifty_raw),
            },
            "dhan_instrument_master": {
                "path": "dhan_instrument_master.csv",
                "sha256": expected_master_hash,
                "bytes": len(master_raw),
            },
        }
        checks = {
            "schema_version": 1,
            "scope_id": SCOPE_ID,
            "manifest_sha256": manifest_sha256,
            "raw_sources": raw_sources,
            "validated_official_row": nifty_row,
            "validated_dhan_mapping": master_row,
            "ohlc_comparison": comparison,
            "volume_crosschecked": False,
            "data_accepted_for_prediction": False,
            "model_fitting_authorized": False,
            "holdout_access_authorized": False,
            "prior_dhan_sample": {
                "response_sha256": dhan_sample_response_sha256,
                "cache_manifest_sha256": dhan_sample_manifest_sha256,
                "row": dhan_sample_row,
            },
        }
        if any(existing_manifest.get(key) != value for key, value in checks.items()):
            raise ValueError("crosscheck_existing_manifest_mismatch")
        for source, expected_hash, expected_bytes in (
            ("nifty_indices", expected_nifty_hash, len(nifty_raw)),
            ("dhan_instrument_master", expected_master_hash, len(master_raw)),
        ):
            source_meta = existing_manifest.get("source_metadata", {}).get(source, {})
            if (source_meta.get("http_status") != 200
                    or source_meta.get("response_sha256") != expected_hash
                    or source_meta.get("response_bytes") != expected_bytes
                    or source_meta.get("request_count") != 1
                    or source_meta.get("retry_count") != 0
                    or source_meta.get("redirect_followed") is not False):
                raise ValueError("crosscheck_existing_manifest_mismatch")
        return {"status": "CACHE_ALREADY_PRESENT", "path": str(final_dir), "bundle_name": bundle_name}

    bundle_manifest = {
        "schema_version": 1,
        "scope_id": SCOPE_ID,
        "fetched_at_utc": fetched_at_utc,
        "manifest_sha256": manifest_sha256,
        "source_metadata": {
            "nifty_indices": nifty_meta,
            "dhan_instrument_master": master_meta,
        },
        "raw_sources": {
            "nifty_indices_response": {
                "path": "nifty_indices_response.json",
                "sha256": expected_nifty_hash,
                "bytes": len(nifty_raw),
            },
            "dhan_instrument_master": {
                "path": "dhan_instrument_master.csv",
                "sha256": expected_master_hash,
                "bytes": len(master_raw),
            },
        },
        "validated_official_row": nifty_row,
        "validated_dhan_mapping": master_row,
        "prior_dhan_sample": {
            "response_sha256": dhan_sample_response_sha256,
            "cache_manifest_sha256": dhan_sample_manifest_sha256,
            "row": dhan_sample_row,
        },
        "ohlc_comparison": comparison,
        "volume_crosschecked": False,
        "data_accepted_for_prediction": False,
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
    }
    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix=".crosscheck.", dir=str(cache_root)))
    try:
        (temp_dir / "nifty_indices_response.json").write_bytes(nifty_raw)
        (temp_dir / "dhan_instrument_master.csv").write_bytes(master_raw)
        (temp_dir / "manifest.json").write_text(
            json.dumps(bundle_manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_dir, final_dir)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return {"status": "CACHE_CREATED", "path": str(final_dir), "bundle_name": bundle_name}


def run_crosscheck(
    *,
    env: dict[str, str] | None = None,
    opener_factory: Callable[[], Any] = adapter.no_redirect_opener,
    manifest_path: pathlib.Path = MANIFEST_PATH,
    approval_path: pathlib.Path = APPROVAL_PATH,
    cached_dhan_response_path: pathlib.Path = DEFAULT_DHAN_SAMPLE_RESPONSE_PATH,
    cached_dhan_manifest_path: pathlib.Path = DEFAULT_DHAN_SAMPLE_MANIFEST_PATH,
    cache_root: pathlib.Path = DEFAULT_CACHE_ROOT,
    report_path: pathlib.Path = DEFAULT_REPORT_PATH,
    fetched_at_utc: str | None = None,
) -> int:
    """Fetch exactly two public sources after external workflow has marked approval SPENT."""
    environment = dict(os.environ if env is None else env)
    attempts = 0
    source_metadata: dict[str, Any] = {}
    report: dict[str, Any] = {
        "schema_version": 1,
        "scope_id": SCOPE_ID,
        "status": "BLOCKED_BEFORE_REQUEST",
        "request_count": 0,
        "retry_count": 0,
        "redirect_followed": False,
        "credentials_sent": False,
        "data_accepted_for_prediction": False,
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
    }
    try:
        if environment.get("OFFICIAL_CROSSCHECK_AUTHORIZED") != "1":
            raise ValueError("crosscheck_live_request_not_authorized")
        manifest, approval, manifest_sha = _verify_spent_approval(manifest_path, approval_path)
        report["manifest_sha256"] = manifest_sha
        report["approval_spent_from_commit"] = approval["spent_from_commit"]
        cached_dhan_row, cached_dhan_meta = _load_verified_dhan_sample(
            cached_dhan_response_path, cached_dhan_manifest_path
        )
        report["cached_dhan_sample"] = cached_dhan_meta
        report["cached_dhan_sample_verified"] = True

        attempts += 1
        nifty_raw, nifty_meta = adapter.request_once(
            source="nifty_indices",
            url=adapter.NIFTY_INDICES_URL,
            allowed_url=adapter.NIFTY_INDICES_URL,
            method="POST",
            body=adapter.make_nifty_request_body(),
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": adapter.NIFTY_INDICES_REFERER,
                "User-Agent": "Mozilla/5.0 (compatible; NakedOptionResearch/1.0)",
                "Accept": "application/json",
            },
            allowed_content_types=adapter.CONTENT_TYPE_NIFTY,
            byte_cap=adapter.NIFTY_MAX_RESPONSE_BYTES,
            timeout_seconds=adapter.NIFTY_TIMEOUT_SECONDS,
            opener_factory=opener_factory,
        )
        source_metadata["nifty_indices"] = nifty_meta
        nifty_row = adapter.parse_nifty_indices_response(nifty_raw)
        attempts += 1
        master_raw, master_meta = adapter.request_once(
            source="dhan_instrument_master",
            url=adapter.DHAN_COMPACT_MASTER_URL,
            allowed_url=adapter.DHAN_COMPACT_MASTER_URL,
            method="GET",
            body=None,
            headers={"Accept": "text/csv, application/csv, application/octet-stream, text/plain"},
            allowed_content_types=adapter.CONTENT_TYPE_CSV,
            byte_cap=adapter.MAX_CSV_BYTES,
            timeout_seconds=adapter.DHAN_MASTER_TIMEOUT_SECONDS,
            opener_factory=opener_factory,
        )
        source_metadata["dhan_instrument_master"] = master_meta
        mapping_row = adapter.parse_dhan_instrument_mapping(master_raw)
        comparison = adapter.compare_ohlc(nifty_row, cached_dhan_row)
        if comparison["status"] != "MATCH":
            raise ValueError("official_nifty_ohlc_mismatch")
        fetched_at = fetched_at_utc or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        cache_result = _atomic_bundle(
            nifty_raw=nifty_raw,
            master_raw=master_raw,
            nifty_meta=nifty_meta,
            master_meta=master_meta,
            nifty_row=nifty_row,
            master_row=mapping_row,
            comparison=comparison,
            manifest_sha256=manifest_sha,
            dhan_sample_row=cached_dhan_row,
            dhan_sample_response_sha256=cached_dhan_meta["response_sha256"],
            dhan_sample_manifest_sha256=cached_dhan_meta["cache_manifest_sha256"],
            cache_root=cache_root,
            fetched_at_utc=fetched_at,
        )
        report.update({
            "status": "OFFICIAL_CROSSCHECK_MATCHED",
            "request_count": attempts,
            "source_metadata": source_metadata,
            "official_nifty_row": nifty_row,
            "cached_dhan_row": cached_dhan_row,
            "cached_dhan_sample_sha256": cached_dhan_meta["response_sha256"],
            "dhan_instrument_mapping": mapping_row,
            "ohlc_comparison": comparison,
            "cache_created": cache_result["status"] == "CACHE_CREATED",
            "cache_status": cache_result["status"],
            "cache_bundle_name": cache_result["bundle_name"],
            "fetched_at_utc": fetched_at,
            "volume_crosschecked": False,
            "data_accepted_for_prediction": False,
        })
        _write_json_atomic(report_path, report)
        print(json.dumps(report, sort_keys=True))
        return 0
    except Exception as exc:
        report.update({
            "status": "OFFICIAL_CROSSCHECK_FAILED_CLOSED",
            "failure_code": _safe_failure_code(exc),
            "request_count": attempts,
            "source_metadata": source_metadata,
            "retry_count": 0,
            "redirect_followed": False,
            "credentials_sent": False,
            "raw_provider_error_saved": False,
            "cache_created": False,
            "data_accepted_for_prediction": False,
        })
        _write_json_atomic(report_path, report)
        print(json.dumps(report, sort_keys=True))
        return 1


def main(argv: list[str] | None = None) -> int:
    """Default CLI is offline-only; live mode requires the explicit flag and workflow gate."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(json.dumps({
            "status": "OFFLINE_VALIDATION_ONLY",
            "network_enabled": False,
            "live_request_authorized": False,
            "scope_id": SCOPE_ID,
        }, sort_keys=True))
        return 0
    if args != ["--live"]:
        print(json.dumps({
            "status": "BLOCKED",
            "failure_code": "crosscheck_cli_arguments_invalid",
            "network_enabled": False,
        }, sort_keys=True))
        return 2
    if os.environ.get("OFFICIAL_CROSSCHECK_AUTHORIZED") != "1":
        print(json.dumps({
            "status": "BLOCKED",
            "failure_code": "crosscheck_live_request_not_authorized",
            "network_enabled": False,
        }, sort_keys=True))
        return 1
    return run_crosscheck()


if __name__ == "__main__":
    raise SystemExit(main())
