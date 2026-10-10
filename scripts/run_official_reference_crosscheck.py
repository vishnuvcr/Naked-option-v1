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
import os
import pathlib
import re
import shutil
import tempfile
from typing import Any, Callable

import official_reference_crosscheck as adapter

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_REQUEST.json"
APPROVAL_PATH = ROOT / "research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_APPROVAL.json"
DEFAULT_CACHE_ROOT = ROOT / "data/cache/dhan_sample_official_crosscheck"
DEFAULT_REPORT_PATH = ROOT / "data/reports/dhan_sample_official_crosscheck_status.json"
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
    if auth.get("expected_mapping") != adapter.EXPECTED_MAPPING:
        raise ValueError("crosscheck_expected_mapping_mismatch")
    return manifest, approval, digest


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
        if (existing_nifty.is_file() and existing_master.is_file() and
                _sha256(existing_nifty.read_bytes()) == expected_nifty_hash and
                _sha256(existing_master.read_bytes()) == expected_master_hash):
            return {"status": "CACHE_ALREADY_PRESENT", "path": str(final_dir), "bundle_name": bundle_name}
        raise ValueError("crosscheck_cache_collision")

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
        comparison = adapter.compare_ohlc(nifty_row, adapter.EXPECTED_DHAN_ROW)
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
            cache_root=cache_root,
            fetched_at_utc=fetched_at,
        )
        report.update({
            "status": "OFFICIAL_CROSSCHECK_MATCHED",
            "request_count": attempts,
            "source_metadata": source_metadata,
            "official_nifty_row": nifty_row,
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


def main() -> int:
    return run_crosscheck()


if __name__ == "__main__":
    raise SystemExit(main())
