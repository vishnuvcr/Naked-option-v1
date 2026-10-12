#!/usr/bin/env python3
"""Synthetic-only R4 regression tests for the manifest-bound duplicate diagnostic."""
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("phase8p_duplicate_key_diagnostic.py")
spec = importlib.util.spec_from_file_location("phase8p_duplicate_diag", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    result = m.synthetic_self_test()
    assert result["status"] == "PASS"
    assert result["mode"] == "SYNTHETIC_ONLY"
    assert result["manifest_bound_schema"] == "PASS"
    assert result["exact_duplicates_excluding_provenance"] == "PASS"
    assert result["conflicting_signature_field_detection"] == "PASS"
    assert result["seconds_milliseconds_timestamp_normalization"] == "PASS"
    assert result["ordered_header_fail_closed"] == "PASS"
    assert result["no_deduplication_or_raw_output"] == "PASS"
    assert result["real_artifact_opened"] is False
    assert result["model_fitted"] is False

    # Required manifest columns must be present and column ordering must be preserved.
    required = sorted(m.CONTRACT_REQUIRED_MANIFEST_FIELDS)
    try:
        m.validate_greek_manifest_columns([*required, "timestamp_utc", "timestamp_ist", "timestamp_utc"])
    except m.GateBlocked as exc:
        assert "GREEK_MANIFEST_COLUMNS_DUPLICATE" in str(exc)
    else:
        raise AssertionError("duplicate manifest column was accepted")

    try:
        m.validate_greek_manifest_columns([*required])
    except m.GateBlocked as exc:
        assert "GREEK_MANIFEST_TIMESTAMP_TEXT_FIELD_MISSING" in str(exc)
    else:
        raise AssertionError("manifest without a timestamp text column was accepted")

    print("PASS: manifest-bound duplicate diagnostic regression suite; real artifact untouched")


if __name__ == "__main__":
    main()
