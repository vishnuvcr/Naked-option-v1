from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_phase8_cached_source_inputs",
    ROOT / "scripts" / "verify_phase8_cached_source_inputs.py",
)
assert SPEC and SPEC.loader
verify_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_module)


def _write_fixture(root: Path, *, include_daily=True, include_intraday=True):
    daily_rel = "data/cache/raw/phase3/nifty50_daily.csv"
    intraday_rel = "data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet"
    daily_bytes = b"date,close\n2026-01-01,25000.0\n"
    intraday_bytes = b"synthetic parquet fixture bytes"
    files = {
        "daily_csv": (daily_rel, daily_bytes, include_daily),
        "intraday_parquet": (intraday_rel, intraday_bytes, include_intraday),
    }
    source_manifest = {}
    for name, (relative, payload, include) in files.items():
        source_manifest[name] = {
            "path": relative,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        if include:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)

    manifest_path = root / "reference_manifest.json"
    manifest_path.write_text(json.dumps({"source_files": source_manifest}), encoding="utf-8")
    return manifest_path, files


def test_exact_cached_sources_pass_without_network():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        manifest, _ = _write_fixture(root)
        result = verify_module.verify_cached_source_inputs(manifest, root)
        assert result["status"] == "PASS", result
        assert result["network_accessed"] is False
        assert len(result["checked"]) == 2
        assert all(item["matches"] for item in result["checked"])


def test_missing_source_is_reported_not_downloaded():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        manifest, _ = _write_fixture(root, include_intraday=False)
        result = verify_module.verify_cached_source_inputs(manifest, root, allow_missing=True)
        assert result["status"] == "MISSING", result
        assert result["network_accessed"] is False
        assert [item["name"] for item in result["missing"]] == ["intraday_parquet"]


def test_existing_wrong_hash_fails_closed_even_if_another_source_is_missing():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        manifest, files = _write_fixture(root, include_daily=True, include_intraday=False)
        daily_path = root / files["daily_csv"][0]
        daily_path.write_bytes(b"tampered content")
        result = verify_module.verify_cached_source_inputs(manifest, root, allow_missing=True)
        assert result["status"] == "HASH_MISMATCH", result
        assert result["network_accessed"] is False
        assert len(result["mismatches"]) == 1
        assert result["mismatches"][0]["name"] == "daily_csv"


def test_manifest_cannot_redirect_a_pinned_source_path():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        manifest, _ = _write_fixture(root)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["source_files"]["daily_csv"]["path"] = "../../outside.csv"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        result = verify_module.verify_cached_source_inputs(manifest, root, allow_missing=True)
        assert result["status"] == "ERROR", result
        assert result["network_accessed"] is False
        assert "source path pin changed" in result["error"]


def test_missing_or_malformed_manifest_fails_closed():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        try:
            verify_module.verify_cached_source_inputs(root / "missing.json", root)
        except verify_module.SourceCacheError:
            pass
        else:
            raise AssertionError("missing manifest did not fail closed")


def main():
    tests = [
        test_exact_cached_sources_pass_without_network,
        test_missing_source_is_reported_not_downloaded,
        test_existing_wrong_hash_fails_closed_even_if_another_source_is_missing,
        test_manifest_cannot_redirect_a_pinned_source_path,
        test_missing_or_malformed_manifest_fails_closed,
    ]
    for test in tests:
        test()
    print(json.dumps({"status": "PASS", "tests": len(tests), "network_accessed": False}, sort_keys=True))


if __name__ == "__main__":
    import json
    main()
