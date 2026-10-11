from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = "research/gates/PHASE8_SOURCE_CACHE_BOOTSTRAP_TESTER_DECISION_R1_2026-10-11.json"
CONSUMED_MARKER = "research/phase8/PHASE8_SOURCE_CACHE_BOOTSTRAP_CONSUMED_R1.json"
SOURCE_PATHS = {
    "daily_csv": "data/cache/raw/phase3/nifty50_daily.csv",
    "intraday_parquet": "data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet",
}
REQUIRED_CODE_PATHS = (
    ".github/workflows/phase-08-long-option.yml",
    ".github/workflows/phase8-panel-validator-test.yml",
    ".github/workflows/phase8-frozen-source-restore.yml",
    "scripts/acquire_nifty_daily_history.py",
    "scripts/acquire_hf_intraday_sample.py",
    "scripts/verify_phase8_cached_source_inputs.py",
    "scripts/authorize_phase8_source_cache_bootstrap.py",
    "scripts/test_phase8_cached_source_inputs.py",
    "scripts/test_phase8_source_cache_bootstrap.py",
)


class BootstrapAuthorizationError(RuntimeError):
    pass


def evaluate_decision(
    decision: dict,
    actual_blob_shas: dict[str, str],
    frozen_source_pins: dict[str, dict],
    *,
    consumed_marker_exists: bool,
) -> dict:
    """Pure fail-closed policy check; does not access network or GitHub APIs."""
    if consumed_marker_exists:
        raise BootstrapAuthorizationError("one-time source cache bootstrap marker already exists")
    if decision.get("decision") != "APPROVE_ONE_TIME_FREE_SOURCE_CACHE_BOOTSTRAP":
        raise BootstrapAuthorizationError("tester decision does not approve one-time source cache bootstrap")
    if decision.get("gate") != "phase8-source-cache-bootstrap-r1":
        raise BootstrapAuthorizationError("wrong tester gate identifier")
    if decision.get("source_cache_bootstrap_authorized") is not True:
        raise BootstrapAuthorizationError("one-time bootstrap flag is not true")
    if decision.get("source_audit_authorized") is not False:
        raise BootstrapAuthorizationError("option-source audit must remain unauthorized by this gate")
    for flag in (
        "empirical_option_pnl_authorized",
        "holdout_access_authorized",
        "new_option_market_sources_authorized",
        "strategy_promotion_authorized",
    ):
        if decision.get(flag) is not False:
            raise BootstrapAuthorizationError(f"{flag} must be false")

    approved_blobs = decision.get("approved_code_blob_shas")
    if not isinstance(approved_blobs, dict) or set(approved_blobs) != set(REQUIRED_CODE_PATHS):
        raise BootstrapAuthorizationError("tester decision has unexpected/missing code blob pins")
    mismatches = {
        path: {"expected": approved_blobs[path], "actual": actual_blob_shas.get(path)}
        for path in REQUIRED_CODE_PATHS
        if approved_blobs[path] != actual_blob_shas.get(path)
    }
    if mismatches:
        raise BootstrapAuthorizationError("reviewed code blob pins differ: " + json.dumps(mismatches, sort_keys=True))

    approved_sources = decision.get("frozen_source_sha256")
    if not isinstance(approved_sources, dict) or set(approved_sources) != set(SOURCE_PATHS):
        raise BootstrapAuthorizationError("tester decision has unexpected/missing frozen source pins")
    source_mismatches = {}
    for name, relative in SOURCE_PATHS.items():
        frozen = frozen_source_pins.get(name)
        expected_hash = approved_sources.get(name)
        if not isinstance(frozen, dict) or frozen.get("path") != relative or frozen.get("sha256") != expected_hash:
            source_mismatches[name] = {
                "expected_path": relative,
                "decision_sha256": expected_hash,
                "manifest_path": frozen.get("path") if isinstance(frozen, dict) else None,
                "manifest_sha256": frozen.get("sha256") if isinstance(frozen, dict) else None,
            }
    if source_mismatches:
        raise BootstrapAuthorizationError("frozen input pins differ: " + json.dumps(source_mismatches, sort_keys=True))

    artifact = decision.get("reference_artifact", {})
    if (
        artifact.get("run_id") != 37957677656
        or artifact.get("artifact_id") != 11638738288
        or artifact.get("artifact_sha256") != "3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9"
        or artifact.get("embedded_manifest_sha256") != "f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091"
    ):
        raise BootstrapAuthorizationError("Run #994 reference artifact pins differ from the frozen research baseline")

    return {
        "schema_version": 1,
        "status": "APPROVED",
        "network_accessed": False,
        "decision": decision["decision"],
        "scope": "one bootstrap of the two pinned Phase 7 source files; not the option-source audit or empirical P&L",
        "source_paths": SOURCE_PATHS,
        "source_sha256": approved_sources,
        "approved_code_blob_shas": approved_blobs,
    }


def _git_show(ref: str, path: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise BootstrapAuthorizationError(
            f"unable to read tester decision from {ref}:{path}; fetch tester branch before authorizing"
        ) from exc
    return proc.stdout


def _git_blob(path: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", f"HEAD:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise BootstrapAuthorizationError(f"unable to compute reviewed code blob for {path}") from exc
    return proc.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Authorize a one-time frozen-source cache bootstrap only from an exact tester decision."
    )
    parser.add_argument("--tester-ref", default="origin/phase-08-tester")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data/cache/reference/phase7_run994/unpacked/phase7_reference/phase7_reference_manifest.json",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "data/reports/phase8/source_cache_bootstrap_authorization.json")
    args = parser.parse_args(argv)

    try:
        decision = json.loads(_git_show(args.tester_ref, DECISION_PATH))
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        actual_blobs = {path: _git_blob(path) for path in REQUIRED_CODE_PATHS}
        report = evaluate_decision(
            decision,
            actual_blobs,
            manifest.get("source_files", {}),
            consumed_marker_exists=(ROOT / CONSUMED_MARKER).exists(),
        )
        exit_code = 0
    except (OSError, json.JSONDecodeError, BootstrapAuthorizationError) as exc:
        report = {
            "schema_version": 1,
            "status": "DENIED",
            "network_accessed": False,
            "error": str(exc),
        }
        exit_code = 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
