from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_phase7_correction_approval as approval


def _fixture():
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    hashes = {}
    for rel in approval.PROTECTED_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        data = ("protected-file:" + rel + "\n").encode("utf-8")
        path.write_bytes(data)
        hashes[rel] = hashlib.sha256(data).hexdigest()

    reviewed = "a" * 40
    tick = chr(96)
    gate = (
        "# Independent Tester Report\n\n"
        "**Decision: PASS WITH SCOPED RESTRICTIONS — fresh empirical execution only**\n"
        f"Reviewed developer commit: {tick}{reviewed}{tick}\n"
    )
    gate_bytes = gate.encode("utf-8")
    manifest = {
        "schema_version": 1,
        "status": "PASS",
        "decision": "PASS WITH SCOPED RESTRICTIONS",
        "approval_scope": "fresh empirical execution only",
        "reviewed_developer_commit": reviewed,
        "tester_report_sha256": hashlib.sha256(gate_bytes).hexdigest(),
        "protected_files": hashes,
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
    return temp, root, gate, gate_bytes, manifest, manifest_bytes


def _validate(root, gate, gate_bytes, manifest, manifest_bytes, **kwargs):
    return approval.validate_approval_payload(
        manifest=manifest,
        gate_markdown=gate,
        current_head="b" * 40,
        root=root,
        reviewed_is_ancestor=True,
        local_gate_bytes=gate_bytes,
        tester_gate_bytes=gate_bytes,
        local_manifest_bytes=manifest_bytes,
        tester_manifest_bytes=manifest_bytes,
        **kwargs,
    )


def test_matching_snapshot_is_authorized():
    temp, root, gate, gate_bytes, manifest, manifest_bytes = _fixture()
    try:
        errors = _validate(root, gate, gate_bytes, manifest, manifest_bytes)
        assert errors == [], errors
    finally:
        temp.cleanup()


def test_changed_protected_file_denies_authorization():
    temp, root, gate, gate_bytes, manifest, manifest_bytes = _fixture()
    try:
        (root / "scripts/run_phase7_ensemble.py").write_text(
            "mutated after tester approval\n", encoding="utf-8"
        )
        errors = _validate(root, gate, gate_bytes, manifest, manifest_bytes)
        assert any("hash mismatch" in error for error in errors), errors
    finally:
        temp.cleanup()


def test_changed_tester_branch_copy_denies_authorization():
    temp, root, gate, gate_bytes, manifest, manifest_bytes = _fixture()
    try:
        errors = approval.validate_approval_payload(
            manifest=manifest,
            gate_markdown=gate,
            current_head="b" * 40,
            root=root,
            reviewed_is_ancestor=True,
            local_gate_bytes=gate_bytes,
            tester_gate_bytes=gate_bytes + b"modified",
            local_manifest_bytes=manifest_bytes,
            tester_manifest_bytes=manifest_bytes,
        )
        assert any("differs from the independent tester branch copy" in error for error in errors), errors
    finally:
        temp.cleanup()


def test_non_ancestor_approved_commit_denies_authorization():
    temp, root, gate, gate_bytes, manifest, manifest_bytes = _fixture()
    try:
        errors = approval.validate_approval_payload(
            manifest=manifest,
            gate_markdown=gate,
            current_head="b" * 40,
            root=root,
            reviewed_is_ancestor=False,
            local_gate_bytes=gate_bytes,
            tester_gate_bytes=gate_bytes,
            local_manifest_bytes=manifest_bytes,
            tester_manifest_bytes=manifest_bytes,
        )
        assert any("not an ancestor" in error for error in errors), errors
    finally:
        temp.cleanup()


def test_manifest_must_cover_exact_protected_path_set():
    temp, root, gate, gate_bytes, manifest, manifest_bytes = _fixture()
    try:
        manifest["protected_files"].pop("scripts/run_phase7_ensemble.py")
        errors = _validate(root, gate, gate_bytes, manifest, manifest_bytes)
        assert any("missing required paths" in error for error in errors), errors
    finally:
        temp.cleanup()


def test_both_execution_workflows_use_snapshot_validator():
    caller = (ROOT / ".github/workflows/research-protocol.yml").read_text(encoding="utf-8")
    reusable = (ROOT / ".github/workflows/phase-07-ensemble.yml").read_text(encoding="utf-8")
    assert "python scripts/validate_phase7_correction_approval.py --head" in caller
    assert "PHASE7_RUN925_CORRECTION_APPROVAL.json" in caller
    assert "python scripts/validate_phase7_correction_approval.py --head" in reusable
    assert "fetch-depth: 0" in reusable
    assert "PHASE7_RUN925_CORRECTION_APPROVAL.json" in reusable


def main():
    test_matching_snapshot_is_authorized()
    test_changed_protected_file_denies_authorization()
    test_changed_tester_branch_copy_denies_authorization()
    test_non_ancestor_approved_commit_denies_authorization()
    test_manifest_must_cover_exact_protected_path_set()
    test_both_execution_workflows_use_snapshot_validator()
    print("Phase 7 correction approval positive/negative tests PASS")


if __name__ == "__main__":
    main()
