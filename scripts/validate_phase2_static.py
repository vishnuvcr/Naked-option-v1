from __future__ import annotations
import ast
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

required_files=[
    "scripts/validate_source_manifest.py",
    "scripts/build_pit_fixture.py",
    "scripts/validate_pit_fixture.py",
    "scripts/probe_sources.py",
    "scripts/acquire_official_option_samples.py",
    "scripts/validate_official_option_samples.py",
    "scripts/build_snapshot_manifest.py",
    "scripts/probe_huggingface_datasets.py",
    "scripts/acquire_hf_reference.py",
    "scripts/reconcile_official_vs_hf.py",
    "scripts/probe_global_sources.py",
    "scripts/acquire_s31_reference.py",
    "scripts/reconcile_s31_vs_official.py",
    "scripts/validate_phase2_reconciliation_reports.py",
    "scripts/acquire_global_reference.py",
    "scripts/validate_lot_size_udiff.py",
    "scripts/acquire_india_vix_snapshot.py",
    "scripts/acquire_fii_dii_snapshot.py",
    "scripts/validate_lot_size_history.py",
    "scripts/build_nifty_eod_parquet_year.py",
    "scripts/acquire_global_reference_window.py",
    "scripts/validate_vix_history.py",
    "scripts/acquire_vix_history.py",
]

for rel in required_files:
    p=ROOT/rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing required script {rel}")
    try:
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except SyntaxError as exc:
        raise SystemExit(f"ERROR: syntax failure in {rel}: {exc}")

for rel in ["research/data/SOURCE_MANIFEST.csv","research/data/GLOBAL_SOURCE_MANIFEST.csv"]:
    with (ROOT/rel).open("r",encoding="utf-8",newline="") as fh:
        rows=list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"ERROR: empty manifest {rel}")
    if len({r["source_id"] for r in rows}) != len(rows):
        raise SystemExit(f"ERROR: duplicate source IDs in {rel}")

req=ROOT/"requirements-phase2.txt"
if "pyarrow" not in req.read_text(encoding="utf-8").lower():
    raise SystemExit("ERROR: Phase 2 parquet dependency missing")

workflow_specs=[
    (
        ROOT/".github/workflows/phase-02-data-audit.yml",
        ["workflow_dispatch","data/cache/raw","HF_TOKEN","acquire_hf_reference.py","reconcile_official_vs_hf.py","probe_global_sources.py","acquire_s31_reference.py","reconcile_s31_vs_official.py","validate_phase2_reconciliation_reports.py","acquire_global_reference.py","validate_lot_size_udiff.py","acquire_india_vix_snapshot.py","acquire_fii_dii_snapshot.py"],
    ),
    (
        ROOT/".github/workflows/phase-02c-bulk.yml",
        ["workflow_dispatch","data/cache/raw","acquire_vix_history.py","validate_vix_history.py","acquire_global_reference_window.py","acquire_fii_dii_snapshot.py","build_nifty_eod_parquet_year.py","validate_lot_size_history.py","validate_phase2c_bulk_reports.py"],
    ),
]
for wf_path,markers in workflow_specs:
    if not wf_path.exists():
        raise SystemExit(f"ERROR: missing Phase 2 workflow {wf_path}")
    wf=wf_path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in wf:
            raise SystemExit(f"ERROR: {wf_path.name} missing {marker}")

print("PASS: Phase 2 static syntax, manifest, dependency and workflow checks")
