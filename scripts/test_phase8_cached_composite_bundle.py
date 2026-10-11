from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_phase8_cached_composite_bundle as bundle


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(root: Path):
    bundle.EXPECTED_DATASET_ID = "TEST_DATASET"
    bundle.EXPECTED_PARENT_ARTIFACT_ID = 123
    bundle.EXPECTED_PARENT_RUN_ID = 456
    bundle.EXPECTED_PARENT_ARTIFACT_SHA256 = "a" * 64
    parent = root / "bundle"
    parent.mkdir()
    rows = []
    parts_ref = []
    for idx, content in enumerate((b"ciphertext-1", b"ciphertext-2"), 1):
        name = f"part{idx}.csv.gz.enc"
        (parent / name).write_bytes(content)
        item = {
            "file": name, "row_count": 1, "encrypted_bytes": len(content),
            "encrypted_sha256": _sha(content), "plain_gzip_sha256": _sha(b"plain"+bytes([idx])),
        }
        parts_ref.append(dict(item))
        rows.append(dict(item))
    ref = {
        "dataset_id": "TEST_DATASET", "encrypted_only": True,
        "parent_artifact_id": 123, "parent_artifact_run_id": 456,
        "parent_artifact_sha256": "a" * 64, "part_count": 2, "part_hashes": parts_ref,
    }
    actual = {
        "dataset_id": "TEST_DATASET", "download_bundle_contains_encrypted_data_only": True,
        "derived_from": {
            "parent_artifact_id": 123, "parent_artifact_run_id": 456,
            "parent_artifact_sha256": "a" * 64,
        }, "parts": rows,
    }
    (parent / "dataset_manifest.json").write_text(json.dumps(actual), encoding="utf-8")
    ref_path = root / "reference.json"
    ref_path.write_text(json.dumps(ref), encoding="utf-8")
    bundle.EXPECTED_PART_COUNT = 2
    bundle.EXPECTED_TOTAL_ROWS = 2
    return parent, ref_path


def test_accepts_exact_encrypted_bundle():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        part_dir, reference = _fixture(root)
        result = bundle.validate_bundle(part_dir, reference)
        assert result["status"] == "PASS_ENCRYPTED_BUNDLE_INTEGRITY"
        assert result["encrypted_part_count"] == 2
        assert result["expected_data_rows"] == 2
        assert result["plaintext_opened"] is False


def test_rejects_modified_ciphertext_and_manifest():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        part_dir, reference = _fixture(root)
        (part_dir / "part1.csv.gz.enc").write_bytes(b"altered")
        try:
            bundle.validate_bundle(part_dir, reference)
        except ValueError as exc:
            assert "byte count mismatch" in str(exc) or "SHA-256 mismatch" in str(exc)
        else:
            raise AssertionError("modified ciphertext must be rejected")


def test_rejects_unsafe_filename():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        part_dir, reference = _fixture(root)
        manifest_path = part_dir / "dataset_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["parts"][0]["file"] = "../escape.csv.gz.enc"
        manifest_path.write_text(json.dumps(manifest))
        try:
            bundle.validate_bundle(part_dir, reference)
        except ValueError as exc:
            assert "unsafe encrypted-part filename" in str(exc)
        else:
            raise AssertionError("path traversal must be rejected")


if __name__ == "__main__":
    test_accepts_exact_encrypted_bundle()
    test_rejects_modified_ciphertext_and_manifest()
    test_rejects_unsafe_filename()
    print("Phase 8 encrypted-bundle preflight tests PASS")
