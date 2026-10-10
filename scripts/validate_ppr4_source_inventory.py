#!/usr/bin/env python3
"""Offline PPR-4 source/cache inventory validation.

This validates metadata artifacts only. It never requests sources, reads market-data
values, downloads files, builds features, fits models, or opens a holdout.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/phase7/PPR4_SOURCE_AVAILABILITY_MANIFEST.json"
REGISTER = ROOT / "research/phase7/PPR4_SOURCE_AVAILABILITY_REGISTER.csv"
AUDIT = ROOT / "research/phase7/PPR4_SOURCE_FEASIBILITY_AUDIT.md"
HOLDOUT = ROOT / "research/phase7/PPR4_HOLDOUT_METADATA_AUDIT.json"
CACHE = ROOT / "research/phase7/PPR4_REPO_CACHE_INVENTORY.csv"

EXPECTED_IDS = [f"P4-{n:03d}" for n in range(1, 33)]
REQUIRED_REGISTER_COLUMNS = {
    "source_id", "data_family", "source_name", "source_url", "source_class",
    "data_grain", "coverage_start_claim", "coverage_end_claim", "frequency",
    "expected_fields", "public_metadata_evidence", "point_in_time_and_quality_risks",
    "availability_status", "license_status", "existing_cache_state",
    "project_acceptance_status", "next_permitted_action",
    "bulk_acquisition_authorized", "model_panel_accepted", "notes",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def validate() -> list[str]:
    errors: list[str] = []
    for path in (MANIFEST, REGISTER, AUDIT, HOLDOUT, CACHE):
        if not path.is_file():
            errors.append(f"missing PPR-4 artifact: {path.relative_to(ROOT)}")
    if errors:
        return errors

    try:
        manifest = read_json(MANIFEST)
        holdout = read_json(HOLDOUT)
        register = read_csv(REGISTER)
        cache = read_csv(CACHE)
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        return [f"cannot parse PPR-4 artifacts: {exc}"]

    if manifest.get("schema_version") != 1:
        errors.append("PPR-4 manifest schema_version must be 1")
    if manifest.get("phase") != "PPR-4":
        errors.append("manifest phase must be PPR-4")
    if manifest.get("audit_status") != "READ_ONLY_INVENTORY_COMPLETE_EXIT_BLOCKED":
        errors.append("PPR-4 status must remain read-only inventory complete / exit blocked")
    if manifest.get("gate_decision") != "BLOCKED_GATE_NO_MACHINE_READABLE_BOUNDARY_FOUND":
        errors.append("manifest must preserve the holdout-boundary gate block")

    required_false = (
        "bulk_dataset_download_authorized",
        "pretrained_model_download_authorized",
        "model_panel_acceptance_authorized",
        "model_fitting_tuning_scoring_authorized",
        "final_holdout_access_authorized",
        "option_pnl_authorized",
        "one_use_dhan_approval_reusable",
    )
    boundary = manifest.get("hard_boundary", {})
    for key in required_false:
        if boundary.get(key) is not False:
            errors.append(f"hard boundary {key} must be false")
    if boundary.get("public_source_metadata_search_authorized") is not True:
        errors.append("read-only public metadata search must be explicitly authorized")
    if boundary.get("read_only_repo_and_artifact_metadata_inspection_authorized") is not True:
        errors.append("read-only repository/artifact metadata inspection must be explicitly authorized")

    inventory = manifest.get("inventory_summary", {})
    if inventory.get("read_only_sources_registered") != 32 or len(register) != 32:
        errors.append(f"expected 32 PPR-4 source rows, manifest={inventory.get('read_only_sources_registered')}, CSV={len(register)}")
    if inventory.get("accepted_modeling_datasets") != 0:
        errors.append("accepted_modeling_datasets must remain zero")
    if inventory.get("free_source_search_exhausted") is not False:
        errors.append("source inventory must not claim the free-source landscape is exhausted")

    if register:
        missing_columns = REQUIRED_REGISTER_COLUMNS - set(register[0])
        if missing_columns:
            errors.append(f"source register missing columns: {sorted(missing_columns)}")
        ids = [row.get("source_id", "") for row in register]
        if ids != EXPECTED_IDS:
            errors.append("source register IDs must be ordered P4-001 through P4-032 with no gaps or duplicates")
        for row in register:
            sid = row.get("source_id", "")
            for field in REQUIRED_REGISTER_COLUMNS:
                if not row.get(field, "").strip():
                    errors.append(f"{sid}: blank required register field {field}")
            if row.get("bulk_acquisition_authorized") != "false":
                errors.append(f"{sid}: bulk_acquisition_authorized must be false")
            if row.get("model_panel_accepted") != "false":
                errors.append(f"{sid}: model_panel_accepted must be false")
            if row.get("project_acceptance_status") not in {
                "NOT_ACCEPTED_FOR_MODELING",
                "BLOCKED_GATE_NO_MACHINE_READABLE_HOLDOUT_BOUNDARY",
                "REJECTED_WHOLE_FILE_MIXED_PROVENANCE",
                "BLOCKED_DATA_UNVERIFIED",
                "NOT_AUTHORIZED_FOR_DOWNLOAD",
            }:
                errors.append(f"{sid}: unexpected acceptance status {row.get('project_acceptance_status')}")
        p4_004 = next((r for r in register if r.get("source_id") == "P4-004"), {})
        if "other" not in p4_004.get("license_status", "").lower():
            errors.append("P4-004 HF mixed-source option dataset must preserve its unresolved 'other' license status")
        p4_005 = next((r for r in register if r.get("source_id") == "P4-005"), {})
        if "CC-BY-NC-4.0" not in p4_005.get("license_status", ""):
            errors.append("P4-005 must preserve CC-BY-NC license limitation")
        p4_013 = next((r for r in register if r.get("source_id") == "P4-013"), {})
        if p4_013.get("project_acceptance_status") != "REJECTED_WHOLE_FILE_MIXED_PROVENANCE":
            errors.append("P4-013 mixed synthetic-history source must remain rejected")
        p4_026 = next((r for r in register if r.get("source_id") == "P4-026"), {})
        if p4_026.get("project_acceptance_status") != "BLOCKED_GATE_NO_MACHINE_READABLE_HOLDOUT_BOUNDARY":
            errors.append("P4-026 must preserve the critical holdout metadata blocker")

    if len(cache) != 5:
        errors.append(f"repository data/cache inventory must include 5 metadata-tree entries, got {len(cache)}")
    if cache:
        cache_ids = [r.get("inventory_id", "") for r in cache]
        if cache_ids != [f"CACHE-{n:03d}" for n in range(1, 6)]:
            errors.append("cache inventory IDs must be CACHE-001 through CACHE-005")
        for row in cache:
            if not row.get("path") or not row.get("git_blob_sha") or not row.get("disposition"):
                errors.append(f"{row.get('inventory_id')}: missing cache inventory metadata")
        sample = next((r for r in cache if r.get("inventory_id") == "CACHE-004"), {})
        if sample.get("size_bytes") != "121" or sample.get("inspection_scope") != "No; content not opened.":
            errors.append("Dhan raw response must remain a 121-byte metadata-listed file whose contents were not opened")
        approval = next((r for r in cache if r.get("inventory_id") == "CACHE-003"), {})
        if approval.get("authorization_status") != "SPENT":
            errors.append("Dhan one-use approval must remain spent")

    if holdout.get("branches_scanned_count") != 23 or len(holdout.get("branches_scanned", [])) != 23:
        errors.append("holdout metadata audit must report a complete 23-branch tree-name scan")
    findings = holdout.get("findings", {})
    if findings.get("machine_readable_boundary_found") is not False:
        errors.append("holdout finding must remain not found until real evidence is added and reviewed")
    if findings.get("holdout_values_opened") is not False or findings.get("holdout_labels_opened") is not False:
        errors.append("holdout observations/labels must remain unopened")
    if findings.get("workflow_artifact_contents_downloaded") is not False:
        errors.append("workflow artifact contents must remain undownloaded")
    if holdout.get("hard_decision") != "BLOCKED_GATE_NO_MACHINE_READABLE_BOUNDARY_FOUND":
        errors.append("holdout audit hard decision must stay blocked")
    if manifest.get("holdout_boundary", {}).get("machine_readable_boundary_found") is not False:
        errors.append("source manifest must preserve unverified holdout boundary")
    if manifest.get("holdout_boundary", {}).get("exact_date_boundary") is not None:
        errors.append("do not invent a holdout date boundary")
    if manifest.get("holdout_boundary", {}).get("holdout_row_id_hash") is not None:
        errors.append("do not invent a holdout row-ID hash")

    # Validate pins against the exact checkout tested by Actions.
    pins = []
    pins.extend(manifest.get("source_artifacts", {}).values())
    pins.extend(manifest.get("frozen_files", {}).values())
    for pin in pins:
        if not isinstance(pin, dict):
            errors.append("manifest pin must be an object")
            continue
        if pin.get("branch") and pin.get("branch") != manifest.get("branch"):
            # Cross-branch tester evidence is referenced by exact blob, but not in the current checkout.
            if not pin.get("blob"):
                errors.append("cross-branch reference lacks blob SHA")
            continue
        rel = pin.get("path", "")
        expected = pin.get("blob", "")
        if not rel or not expected:
            errors.append("same-branch pin requires path and blob SHA")
            continue
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"manifest-pinned file not found in exact checkout: {rel}")
            continue
        try:
            actual = subprocess.run(
                ["git", "hash-object", str(path)],
                cwd=ROOT, check=True, capture_output=True, text=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"cannot hash {rel}: {exc}")
            continue
        if actual != expected:
            errors.append(f"manifest blob mismatch for {rel}: expected {expected}, got {actual}")

    if not manifest.get("source_artifacts") or not manifest.get("frozen_files"):
        errors.append("PPR-4 manifest must pin source and audit artifacts")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: PPR-4 source register, cache inventory, metadata-only holdout audit, source/license statuses and exact blob pins reconcile.")
    print("IMPORTANT: PPR-4 exit remains BLOCKED because no machine-readable final-holdout boundary was found.")
    print("Scope: offline metadata validation only; no source requests, file downloads, data-value reads, model fitting, tuning, scoring or holdout access.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
