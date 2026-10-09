from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = Path("research/gates/PHASE7_RUN925_CORRECTION_CODE_TESTER.md")
MANIFEST_PATH = Path("research/gates/PHASE7_RUN925_CORRECTION_APPROVAL.json")
TESTER_REF = "refs/remotes/origin/phase-07-tester"
PASS_DECISION = "PASS WITH SCOPED RESTRICTIONS"
PASS_SCOPE = "fresh empirical execution only"

# Exact coverage for every file that can alter candidate forecasts, labels,
# inputs, verification or the empirical authorization path. Gate/manifest files
# are separately bound to each other and to the independent tester branch.
PROTECTED_FILES = (
    ".github/workflows/phase-07-ensemble.yml",
    ".github/workflows/research-protocol.yml",
    "research/METHOD_REGISTRY.md",
    "research/RESEARCH_PLAN.md",
    "research/RESEARCH_PROTOCOL.md",
    "research/phase6/PHASE6_METHOD_SPEC.md",
    "research/phase7/PHASE7_METHOD_SPEC.md",
    "scripts/acquire_global_reference.py",
    "scripts/acquire_hf_intraday_sample.py",
    "scripts/acquire_nifty_daily_history.py",
    "scripts/run_phase3_daily_baselines.py",
    "scripts/run_phase3_intraday_baselines.py",
    "scripts/run_phase5_family_d.py",
    "scripts/run_phase6_novel.py",
    "scripts/run_phase7_ensemble.py",
    "scripts/test_phase5_family_d.py",
    "scripts/test_phase6_novel.py",
    "scripts/test_phase7_ensemble.py",
    "scripts/test_phase7_reference_artifact.py",
    "scripts/test_phase7_correction_approval.py",
    "scripts/validate_literature_registry.py",
    "scripts/validate_phase7_results.py",
    "scripts/validate_phase7_correction_approval.py",
    "scripts/validate_protocol.py",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def validate_protected_hashes(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    protected = manifest.get("protected_files")
    if not isinstance(protected, dict):
        return ["manifest protected_files must be a JSON object"]

    expected_set = set(PROTECTED_FILES)
    actual_set = set(protected)
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)
    if missing:
        errors.append(f"protected_files missing required paths: {missing}")
    if extra:
        errors.append(f"protected_files contains unexpected paths: {extra}")

    for rel in PROTECTED_FILES:
        expected = protected.get(rel)
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            errors.append(f"invalid SHA-256 in approval manifest for {rel}")
            continue
        path = root / rel
        if not path.is_file():
            errors.append(f"protected file missing in checkout: {rel}")
            continue
        actual = sha256_path(path)
        if actual != expected:
            errors.append(f"protected file hash mismatch for {rel}: expected {expected}, actual {actual}")
    return errors


def validate_approval_payload(
    manifest: dict[str, Any],
    gate_markdown: str,
    current_head: str,
    root: Path = ROOT,
    reviewed_is_ancestor: bool = True,
    local_gate_bytes: bytes | None = None,
    tester_gate_bytes: bytes | None = None,
    local_manifest_bytes: bytes | None = None,
    tester_manifest_bytes: bytes | None = None,
) -> list[str]:
    """Pure fail-closed approval checks, also used by synthetic positive/negative tests."""
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("approval manifest schema_version must equal 1")
    if manifest.get("status") != "PASS":
        errors.append("approval manifest status is not PASS")
    if manifest.get("decision") != PASS_DECISION:
        errors.append(f"approval manifest decision must equal {PASS_DECISION!r}")
    if manifest.get("approval_scope") != PASS_SCOPE:
        errors.append(f"approval scope must equal {PASS_SCOPE!r}")

    reviewed = manifest.get("reviewed_developer_commit")
    if not isinstance(reviewed, str) or re.fullmatch(r"[0-9a-f]{40}", reviewed) is None:
        errors.append("reviewed_developer_commit must be a 40-character lowercase Git SHA")
        reviewed = ""

    if not isinstance(current_head, str) or re.fullmatch(r"[0-9a-f]{40}", current_head) is None:
        errors.append("current checkout HEAD must be a 40-character lowercase Git SHA")
    if reviewed and not reviewed_is_ancestor:
        errors.append("reviewed developer commit is not an ancestor of the current checkout")

    tick = chr(96)
    expected_gate_line = (
        f"Reviewed developer commit: {tick}{reviewed}{tick}"
        if reviewed else "Reviewed developer commit: INVALID"
    )
    if expected_gate_line not in gate_markdown:
        errors.append("tester report reviewed commit does not match approval manifest")
    if f"Decision: {PASS_DECISION}" not in gate_markdown:
        errors.append("tester report does not contain the required PASS decision")
    if PASS_SCOPE not in gate_markdown:
        errors.append("tester report does not scope approval to fresh empirical execution only")

    if local_gate_bytes is not None and tester_gate_bytes is not None:
        if local_gate_bytes != tester_gate_bytes:
            errors.append("developer-branch tester report differs from the independent tester branch copy")
    else:
        errors.append("could not verify tester report against independent tester branch")

    if local_manifest_bytes is not None and tester_manifest_bytes is not None:
        if local_manifest_bytes != tester_manifest_bytes:
            errors.append("developer-branch approval manifest differs from the independent tester branch copy")
    else:
        errors.append("could not verify approval manifest against independent tester branch")

    gate_digest = sha256_bytes(local_gate_bytes) if local_gate_bytes is not None else None
    if manifest.get("tester_report_sha256") != gate_digest:
        errors.append("approval manifest tester_report_sha256 does not match tester report bytes")

    errors.extend(validate_protected_hashes(manifest, root))
    return errors


def run_git(args: list[str], root: Path = ROOT) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def show_tester_file(path: Path) -> bytes:
    result = run_git(["show", f"{TESTER_REF}:{path.as_posix()}"])
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"independent tester branch file unavailable: {path}: {message}")
    return result.stdout


def validate_workspace(head_commit: str | None = None, root: Path = ROOT) -> list[str]:
    gate_path = root / GATE_PATH
    manifest_path = root / MANIFEST_PATH
    if not gate_path.is_file():
        return [f"independent tester gate missing: {GATE_PATH}"]
    if not manifest_path.is_file():
        return [f"independent tester approval manifest missing: {MANIFEST_PATH}"]

    try:
        local_gate_bytes = gate_path.read_bytes()
        local_manifest_bytes = manifest_path.read_bytes()
        gate_markdown = local_gate_bytes.decode("utf-8")
        manifest = json.loads(local_manifest_bytes.decode("utf-8"))
    except Exception as exc:
        return [f"unable to read tester gate/manifest: {type(exc).__name__}: {exc}"]

    fetch = run_git([
        "fetch", "--no-tags", "origin",
        "refs/heads/phase-07-tester:refs/remotes/origin/phase-07-tester",
    ], root)
    if fetch.returncode != 0:
        message = fetch.stderr.decode("utf-8", errors="replace").strip()
        return [f"could not fetch independent tester branch; authorization denied: {message}"]

    try:
        tester_gate_bytes = show_tester_file(GATE_PATH)
        tester_manifest_bytes = show_tester_file(MANIFEST_PATH)
    except Exception as exc:
        return [str(exc)]

    actual = run_git(["rev-parse", "HEAD"], root)
    if actual.returncode != 0:
        return ["unable to resolve current checkout HEAD"]
    actual_head = actual.stdout.decode("utf-8").strip()
    if head_commit is not None and head_commit != actual_head:
        return ["requested validation head does not match the checked-out commit"]
    current_head = actual_head

    reviewed = manifest.get("reviewed_developer_commit", "")
    ancestor = False
    if isinstance(reviewed, str) and re.fullmatch(r"[0-9a-f]{40}", reviewed):
        found = run_git(["cat-file", "-e", f"{reviewed}^{{commit}}"], root)
        relation = run_git(["merge-base", "--is-ancestor", reviewed, current_head], root)
        ancestor = found.returncode == 0 and relation.returncode == 0

    return validate_approval_payload(
        manifest=manifest,
        gate_markdown=gate_markdown,
        current_head=current_head,
        root=root,
        reviewed_is_ancestor=ancestor,
        local_gate_bytes=local_gate_bytes,
        tester_gate_bytes=tester_gate_bytes,
        local_manifest_bytes=local_manifest_bytes,
        tester_manifest_bytes=tester_manifest_bytes,
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fail-closed validator for independent Phase 7 correction approval."
    )
    parser.add_argument("--head", default=None, help="Expected checkout commit; defaults to HEAD.")
    args = parser.parse_args()
    try:
        errors = validate_workspace(args.head)
    except Exception as exc:
        errors = [f"authorization validator exception: {type(exc).__name__}: {exc}"]

    authorized = not errors
    print(json.dumps({
        "authorized": authorized,
        "reason": "exact tester-approved protected snapshot verified" if authorized else "authorization denied",
        "errors": errors,
    }, indent=2))
    return 0 if authorized else 1


if __name__ == "__main__":
    raise SystemExit(main())
