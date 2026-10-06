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

wf=(ROOT/".github/workflows/phase-02-data-audit.yml").read_text(encoding="utf-8")
for marker in ["workflow_dispatch","data/cache/raw","HF_TOKEN","acquire_hf_reference.py","reconcile_official_vs_hf.py"]:
    if marker not in wf:
        raise SystemExit(f"ERROR: Phase 2 workflow missing {marker}")

print("PASS: Phase 2 static syntax, manifest, dependency and workflow checks")
