from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "research" / "literature" / "LITERATURE_REGISTRY.csv"

with path.open("r", encoding="utf-8", newline="") as fh:
    rows = list(csv.reader(fh))

if not rows:
    raise SystemExit("ERROR: literature registry is empty")

header = rows[0]
required = [
    "source_id","title","year","source_class","evidence_class",
    "url_or_doi","verification_status","related_methods",
    "related_hypotheses","replication_requirement","notes"
]
if header != required:
    raise SystemExit(f"ERROR: unexpected registry header: {header}")

for i, row in enumerate(rows[1:], start=2):
    if len(row) != len(header):
        raise SystemExit(f"ERROR: row {i} has {len(row)} fields; expected {len(header)}")
    if not row[0].startswith("L"):
        raise SystemExit(f"ERROR: invalid source id on row {i}: {row[0]}")

ids=[r[0] for r in rows[1:]]
if len(ids) != len(set(ids)):
    raise SystemExit("ERROR: duplicate literature source IDs")
if len(ids) < 30:
    raise SystemExit(f"ERROR: unexpectedly small literature registry: {len(ids)}")

print(f"PASS: literature registry parsed as RFC-style CSV with {len(ids)} sources")
