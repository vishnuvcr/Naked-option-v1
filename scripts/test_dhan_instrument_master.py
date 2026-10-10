#!/usr/bin/env python3
"""Offline-only tests for Dhan instrument-master validation. No network access."""
from __future__ import annotations
import importlib.util
import pathlib
import tempfile
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dhan_instrument_master", ROOT / "scripts/dhan_instrument_master.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

HEADER = "SEM_SMST_SECURITY_ID,SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_INSTRUMENT_NAME,SEM_TRADING_SYMBOL\n"
VALID = (HEADER + "13,NSE,IDX_I,INDEX,NIFTY\n14,NSE,IDX_I,INDEX,INDIAVIX\n").encode()


def test_import_is_offline_and_urls_are_documented() -> None:
    assert mod.ALLOWED_URLS == {mod.COMPACT_URL, mod.DETAILED_URL}
    assert not hasattr(mod, "requests") and not hasattr(mod, "urllib")


def test_valid_csv_parses_and_hashes() -> None:
    result, rows = mod.validate_instrument_csv(VALID)
    assert result.row_count == 2 and result.security_id_count == 2
    assert len(result.sha256) == 64
    assert rows[0]["SEM_SMST_SECURITY_ID"] == "13"


def test_utf8_bom_supported() -> None:
    result, _ = mod.validate_instrument_csv(b"\xef\xbb\xbf" + VALID)
    assert result.row_count == 2


def test_empty_or_oversized_rejected() -> None:
    for payload, cap, expected in [(b"", 100, "csv_empty_or_not_bytes"), (VALID, 5, "csv_byte_cap_exceeded")]:
        try:
            mod.validate_instrument_csv(payload, max_bytes=cap)
        except ValueError as exc:
            assert str(exc) == expected
        else:
            raise AssertionError("invalid size accepted")


def test_invalid_utf8_and_nul_rejected() -> None:
    for payload, expected in [(b"\xff", "csv_encoding_invalid"), (VALID + b"\x00", "csv_nul_byte")]:
        try:
            mod.validate_instrument_csv(payload)
        except ValueError as exc:
            assert str(exc) == expected
        else:
            raise AssertionError("invalid encoding accepted")


def test_missing_and_duplicate_headers_rejected() -> None:
    bad = [
        b"SEM_SMST_SECURITY_ID,SEM_SEGMENT\n1,IDX_I\n",
        (HEADER.replace("SEM_SEGMENT,", "SEM_SEGMENT,SEM_SEGMENT,") + "1,NSE,IDX_I,IDX_I,INDEX,NIFTY\n").encode(),
    ]
    for payload in bad:
        try:
            mod.validate_instrument_csv(payload)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid header accepted")


def test_missing_values_and_duplicate_ids_rejected() -> None:
    for payload in [
        (HEADER + "13,NSE,IDX_I,INDEX,\n").encode(),
        (HEADER + "13,NSE,IDX_I,INDEX,NIFTY\n13,NSE,IDX_I,INDEX,INDIAVIX\n").encode(),
    ]:
        try:
            mod.validate_instrument_csv(payload)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid identifiers accepted")


def test_atomic_cache_writes_validated_content(tmp_path=None) -> None:
    with tempfile.TemporaryDirectory() as folder:
        target = pathlib.Path(folder) / "cache" / "instruments.csv"
        report = mod.atomic_cache(VALID, target)
        assert target.read_bytes() == VALID
        assert report["status"] == "CACHE_VALIDATED"
        old = target.read_bytes()
        try:
            mod.atomic_cache(b"not,a,valid,csv\n", target)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid CSV cached")
        assert target.read_bytes() == old


def test_cli_declares_no_network() -> None:
    assert mod.main() == 0


TESTS = [v for k, v in globals().copy().items() if k.startswith("test_") and callable(v)]
for test in TESTS:
    test()
print(f"PASS {len(TESTS)} Dhan instrument-master offline tests")
