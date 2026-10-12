#!/usr/bin/env python3
"""Hash/count-only duplicate-key diagnosis for the pinned encrypted composite artifact.

No raw rows, option identifiers, prices, feature vectors, labels, or decrypted tables are
written to disk or emitted. This tool never deduplicates or fits a prediction model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from phase8p_greek_prediction import (
    GateBlocked,
    GREEK_SOURCE_PIN,
    iter_encrypted_composite_parts,
    verify_pinned_artifact_identity,
)

KEY_FIELDS = ("timestamp_epoch", "expiry_date", "expiry_flag", "expiry_code", "returned_strike", "option_type")

def _norm_value(v: Any) -> Any:
    if v is None or v is pd.NA:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        f = float(v)
        return None if not math.isfinite(f) else f
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return str(v) if not isinstance(v, (str, int, bool)) else v

def _raw_key(row: Mapping[str, Any]) -> bytes:
    vals = []
    for field in KEY_FIELDS:
        value = row.get(field)
        if value is None or (isinstance(value, float) and not np.isfinite(value)):
            vals.append(None if field == "timestamp_epoch" else "MISSING")
        else:
            vals.append(str(value))
    return hashlib.sha256(json.dumps(vals, separators=(",", ":"), ensure_ascii=False).encode()).digest()

def _normalized_key(row: Mapping[str, Any]) -> bytes:
    vals = []
    for field in KEY_FIELDS:
        value = row.get(field)
        if field == "timestamp_epoch":
            n = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if not np.isfinite(n):
                vals.append(None)
            else:
                n = float(n)
                vals.append(int(math.floor(n / 1000.0)) if n > 1e12 else int(math.floor(n)))
        elif field == "returned_strike":
            n = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            vals.append(None if not np.isfinite(n) else float(n))
        elif field == "expiry_date":
            t = pd.to_datetime(value, errors="coerce")
            vals.append(None if pd.isna(t) else t.strftime("%Y-%m-%d"))
        elif value is None or (isinstance(value, float) and not np.isfinite(value)):
            vals.append(None if field == "timestamp_epoch" else "MISSING")
        else:
            vals.append(str(value).strip().upper() if field == "option_type" else str(value).strip())
    return hashlib.sha256(json.dumps(vals, separators=(",", ":"), ensure_ascii=False).encode()).digest()

def _row_hash(row: Mapping[str, Any]) -> bytes:
    clean = {str(k): _norm_value(v) for k, v in row.items()}
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).digest()

def _update_seen(seen, groups, key_hash: bytes, row_hash: bytes, part_number: int) -> None:
    previous = seen.get(key_hash)
    if previous is None:
        seen[key_hash] = (row_hash, part_number)
        return
    first_hash, first_part = previous
    group = groups.get(key_hash)
    if group is None:
        group = {"count": 2, "row_hashes": {first_hash, row_hash}, "parts": {first_part, part_number}}
        groups[key_hash] = group
    else:
        group["count"] += 1
        group["row_hashes"].add(row_hash)
        group["parts"].add(part_number)
    # Keep no raw key, contract identifier, or row payload in this report.

def summarize_duplicate_groups(groups: Mapping[bytes, Mapping[str, Any]]) -> dict[str, Any]:
    exact = 0
    conflicting = 0
    extras = 0
    cross_part = 0
    within_part = 0
    for g in groups.values():
        extras += int(g["count"]) - 1
        if len(g["row_hashes"]) == 1:
            exact += 1
        else:
            conflicting += 1
        if len(g["parts"]) > 1:
            cross_part += 1
        else:
            within_part += 1
    return {
        "duplicate_key_groups": len(groups),
        "duplicate_extra_rows": extras,
        "exact_full_row_duplicate_groups": exact,
        "conflicting_full_row_duplicate_groups": conflicting,
        "groups_spanning_multiple_parts": cross_part,
        "groups_within_one_part": within_part,
        "deduplication_performed": False,
        "raw_keys_or_rows_emitted": False,
    }

def scan_frames(frames) -> dict[str, Any]:
    """Synthetic-testable scan over frames labelled by monthly part index."""
    seen_raw = {}
    groups_raw = {}
    seen_normalized = {}
    groups_normalized = {}
    option_rows = 0
    part_count = 0
    part_rows = []
    required = {"row_type", *KEY_FIELDS}
    for part_number, frame in enumerate(frames):
        part_count += 1
        if not isinstance(frame, pd.DataFrame) or not required.issubset(frame.columns):
            raise GateBlocked("DUPLICATE_DIAGNOSTIC_PART_SCHEMA_INVALID")
        types = frame["row_type"].fillna("").astype(str).str.upper()
        options = frame.loc[types.eq("OPTION")]
        part_rows.append(int(len(frame)))
        for row in options.to_dict("records"):
            option_rows += 1
            rh = _row_hash(row)
            _update_seen(seen_raw, groups_raw, _raw_key(row), rh, part_number)
            _update_seen(seen_normalized, groups_normalized, _normalized_key(row), rh, part_number)
    raw = summarize_duplicate_groups(groups_raw)
    normalized = summarize_duplicate_groups(groups_normalized)
    return {
        "parts_scanned": part_count,
        "rows_scanned": int(sum(part_rows)),
        "option_rows_scanned": option_rows,
        "raw_key_semantics": raw,
        "normalized_key_semantics": normalized,
        "normalization_only_duplicate_groups": max(0, normalized["duplicate_key_groups"] - raw["duplicate_key_groups"]),
        "diagnostic_scope": "HASH_AND_COUNT_ONLY_NO_DEDUPLICATION",
    }

def run_diagnostic(greek_zip: Path, artifact_id: int, output: Path) -> dict[str, Any]:
    receipt = verify_pinned_artifact_identity(greek_zip, "greek", artifact_id)
    scan = scan_frames(iter_encrypted_composite_parts(greek_zip))
    result = {
        "schema_version": 1,
        "gate": "PHASE8P_DUPLICATE_OPTION_KEY_DIAGNOSTIC",
        "status": "DIAGNOSTIC_COMPLETE",
        "input_artifact_id": receipt["artifact_id"],
        "input_artifact_sha256": receipt["sha256"],
        "source_revision": GREEK_SOURCE_PIN["revision"],
        "source_license": GREEK_SOURCE_PIN["license"],
        **scan,
        "model_fitted": False,
        "holdout_accessed": False,
        "external_market_source_requested": False,
        "raw_or_decrypted_data_uploaded": False,
        "deduplication_performed": False,
        "model_fit_authorized": False,
        "strategy_promotion_authorized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

def synthetic_self_test() -> dict[str, Any]:
    base = {
        "row_type":"OPTION", "timestamp_epoch":1760000000, "expiry_date":"2026-10-29",
        "expiry_flag":"WEEKLY", "expiry_code":"W1", "returned_strike":25000.0,
        "option_type":"CE", "close":100.0, "delta":0.5,
    }
    exact = dict(base)
    conflict_base = dict(base, returned_strike=25050.0)
    conflict = dict(conflict_base, close=101.0)
    seconds_ms = dict(base, timestamp_epoch=1760000000000)
    spot = {"row_type":"SPOT","timestamp_epoch":1760000000,"expiry_date":None,
            "expiry_flag":None,"expiry_code":None,"returned_strike":None,"option_type":None,
            "close":25000.0,"delta":None}
    result = scan_frames([
        pd.DataFrame([base, conflict_base, spot]),
        pd.DataFrame([exact, conflict, seconds_ms]),
    ])
    raw = result["raw_key_semantics"]
    norm = result["normalized_key_semantics"]
    assert raw["duplicate_key_groups"] == 2
    assert raw["duplicate_extra_rows"] == 2
    assert raw["exact_full_row_duplicate_groups"] == 1
    assert raw["conflicting_full_row_duplicate_groups"] == 1
    assert norm["duplicate_key_groups"] == 2
    assert norm["exact_full_row_duplicate_groups"] == 0
    assert norm["conflicting_full_row_duplicate_groups"] == 2
    assert result["parts_scanned"] == 2 and result["option_rows_scanned"] == 5
    assert result["deduplication_performed"] is False
    try:
        scan_frames([pd.DataFrame([{"row_type":"OPTION"}])])
    except GateBlocked as exc:
        assert "DUPLICATE_DIAGNOSTIC_PART_SCHEMA_INVALID" in str(exc)
    else:
        raise AssertionError("invalid synthetic schema accepted")
    return {"status":"PASS","mode":"SYNTHETIC_ONLY","exact_duplicate_case":"PASS",
            "conflicting_duplicate_case":"PASS","timestamp_normalization_case":"PASS",
            "no_deduplication":"PASS","raw_data_emitted":False,"real_artifact_opened":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--greek-zip",type=Path)
    ap.add_argument("--artifact-id",type=int)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps(synthetic_self_test(),sort_keys=True))
        return
    if args.greek_zip is None or args.artifact_id is None or args.output is None:
        ap.error("real diagnostic requires --greek-zip, --artifact-id and --output")
    report=run_diagnostic(args.greek_zip,args.artifact_id,args.output)
    print(json.dumps({
        "status":report["status"],"input_artifact_id":report["input_artifact_id"],
        "input_artifact_sha256":report["input_artifact_sha256"],
        "parts_scanned":report["parts_scanned"],"option_rows_scanned":report["option_rows_scanned"],
        "raw_key_semantics":report["raw_key_semantics"],
        "normalized_key_semantics":report["normalized_key_semantics"],
        "normalization_only_duplicate_groups":report["normalization_only_duplicate_groups"],
        "deduplication_performed":False,"model_fitted":False
    },sort_keys=True))

if __name__=="__main__": main()
