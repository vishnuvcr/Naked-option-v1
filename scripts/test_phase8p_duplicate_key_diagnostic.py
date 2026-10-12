#!/usr/bin/env python3
"""Synthetic-only regression tests for the duplicate-key diagnostic."""
import importlib.util
from pathlib import Path

path=Path(__file__).with_name("phase8p_duplicate_key_diagnostic.py")
spec=importlib.util.spec_from_file_location("phase8p_duplicate_diag",path)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def main():
    r=m.synthetic_self_test()
    assert r["status"]=="PASS"
    assert r["exact_duplicate_case"]=="PASS"
    assert r["conflicting_duplicate_case"]=="PASS"
    assert r["timestamp_normalization_case"]=="PASS"
    assert r["no_deduplication"]=="PASS"
    assert r["real_artifact_opened"] is False
    assert r["raw_data_emitted"] is False

    # The diagnostic must classify conflicts rather than silently deduplicate.
    import pandas as pd
    a={"row_type":"OPTION","timestamp_epoch":1760000000,"expiry_date":"2026-10-29",
       "expiry_flag":"WEEKLY","expiry_code":"W1","returned_strike":25000.0,
       "option_type":"CE","close":100.0,"delta":0.5}
    b=dict(a,close=100.01)
    out=m.scan_frames([pd.DataFrame([a]),pd.DataFrame([b])])
    assert out["raw_key_semantics"]["duplicate_key_groups"]==1
    assert out["raw_key_semantics"]["exact_full_row_duplicate_groups"]==0
    assert out["raw_key_semantics"]["conflicting_full_row_duplicate_groups"]==1
    assert out["deduplication_performed"] is False
    assert out["raw_keys_or_rows_emitted"] is False

    # Invalid required schema must fail closed.
    try:
        m.scan_frames([pd.DataFrame([{"row_type":"OPTION"}])])
    except m.GateBlocked as exc:
        assert "DUPLICATE_DIAGNOSTIC_PART_SCHEMA_INVALID" in str(exc)
    else:
        raise AssertionError("invalid schema accepted")
    print("PASS: duplicate diagnostic synthetic tests; no real artifact opened; no deduplication")
if __name__=="__main__": main()
