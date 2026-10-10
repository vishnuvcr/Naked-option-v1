#!/usr/bin/env python3
"""Offline PPR-2 crosswalk validation. Does not access the internet or load market data."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research/literature/LITERATURE_REGISTRY.csv"
CROSSWALK = ROOT / "research/literature/PPR2_LITERATURE_REGISTRY_CROSSWALK.csv"

BASE_FIELDS = [
    "source_id", "title", "year", "source_class", "evidence_class",
    "url_or_doi", "verification_status", "related_methods",
    "related_hypotheses", "replication_requirement", "notes",
]
EXTRA_FIELDS = [
    "review_depth", "ppr2_disposition", "uploaded_pdf_exact_match",
    "conceptual_overlap_only", "paper_or_source_task", "ppr2_action",
    "limitations_and_blockers",
]
ALLOWED_VERIFICATION = {"verified", "verified_pending", "pending", "unverified", "blocked"}
FIDELITY_WORDS = ("exact", "overlap", "blocked", "metadata", "abstract", "source", "method", "background", "registry", "strategy", "context", "target", "repository", "readme", "verified")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate():
    errors = []
    if not REGISTRY.is_file() or not CROSSWALK.is_file():
        return ["required registry/crosswalk file missing"]
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as handle:
        registry_reader = csv.DictReader(handle)
        if registry_reader.fieldnames != BASE_FIELDS:
            errors.append("registry header does not match the expected 11-field schema")
            return errors
        registry_rows = list(registry_reader)
    with CROSSWALK.open("r", encoding="utf-8-sig", newline="") as handle:
        cross_reader = csv.DictReader(handle)
        if cross_reader.fieldnames != BASE_FIELDS + EXTRA_FIELDS:
            errors.append("PPR-2 crosswalk header does not match expected 18-field schema")
            return errors
        cross_rows = list(cross_reader)

    expected_ids = [f"L{i:03d}" for i in range(1, 37)]
    reg_ids = [row.get("source_id", "") for row in registry_rows]
    map_ids = [row.get("source_id", "") for row in cross_rows]
    if len(registry_rows) != 36:
        errors.append(f"registry has {len(registry_rows)} records; expected 36")
    if len(cross_rows) != 36:
        errors.append(f"crosswalk has {len(cross_rows)} records; expected 36")
    if reg_ids != expected_ids:
        errors.append("registry source IDs are not exactly L001-L036 in order")
    if map_ids != expected_ids:
        errors.append("crosswalk source IDs are not exactly L001-L036 in order")
    if len(set(reg_ids)) != len(reg_ids) or len(set(map_ids)) != len(map_ids):
        errors.append("duplicate source IDs detected")
    registry_by_id = {row.get("source_id"): row for row in registry_rows}
    for line, mapped in enumerate(cross_rows, start=2):
        sid = mapped.get("source_id", "")
        source = registry_by_id.get(sid)
        if source is None:
            errors.append(f"row {line}: source ID missing from registry: {sid}")
            continue
        for field in BASE_FIELDS:
            if mapped.get(field) != source.get(field):
                errors.append(f"row {line} ({sid}): base source field {field} differs from registry")
        for field in EXTRA_FIELDS:
            if not (mapped.get(field) or "").strip():
                errors.append(f"row {line} ({sid}): {field} is blank")
        if mapped.get("uploaded_pdf_exact_match") != "NONE_EXACT":
            errors.append(f"row {line} ({sid}): exact uploaded-PDF match needs explicit evidence review")
        disposition = (mapped.get("ppr2_disposition") or "").strip()
        if not disposition or not disposition.replace("_", "").isalnum():
            errors.append(f"row {line} ({sid}): invalid disposition token")
        depth = (mapped.get("review_depth") or "").strip()
        if not any(word in depth.lower() for word in FIDELITY_WORDS):
            errors.append(f"row {line} ({sid}): review-depth label is not explanatory")
        if mapped.get("verification_status") not in ALLOWED_VERIFICATION:
            errors.append(f"row {line} ({sid}): unrecognized verification status")
        url = (mapped.get("url_or_doi") or "").strip()
        if not (url.startswith("https://") or url.startswith("http://") or url.startswith("10.") or url.startswith("doi:")):
            errors.append(f"row {line} ({sid}): URL/DOI field does not look like a URL or DOI")
        if mapped.get("source_id") == "L003":
            if mapped.get("url_or_doi") != "https://doi.org/10.1111/0022-1082.00163":
                errors.append("L003 URL is not in url_or_doi")
            if mapped.get("related_methods") != "B01-B13|J01-J07":
                errors.append("L003 related_methods field shifted/mismatched")
            if mapped.get("related_hypotheses") != "H01|H13":
                errors.append("L003 related_hypotheses field shifted/mismatched")
            if mapped.get("replication_requirement") != "method/evidence source; no empirical performance accepted":
                errors.append("L003 replication_requirement field shifted/mismatched")
    if errors:
        return errors
    return []


def main():
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: all 36 literature records are mapped once, with source fields preserved and explicit PPR-2 dispositions.")
    print("Scope: offline registry integrity and documentation checks only; no network, data pull, model fit or scoring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
