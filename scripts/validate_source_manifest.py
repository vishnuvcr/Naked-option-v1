from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "research" / "data" / "SOURCE_MANIFEST.csv"

with path.open("r", encoding="utf-8", newline="") as fh:
    rows = list(csv.DictReader(fh))

if not rows:
    raise SystemExit("ERROR: source manifest is empty")

required = {"source_id","tier","source_name","url_or_repo","coverage_or_role","priority","status","license_note"}
for r in rows:
    if set(r) != required:
        raise SystemExit(f"ERROR: manifest schema mismatch for {r.get('source_id')}")
ids=[r["source_id"] for r in rows]
if len(ids) != len(set(ids)):
    raise SystemExit("ERROR: duplicate source IDs")
tiers={"PRIMARY","DERIVED_FREE","OPEN_SOURCE","PAID"}
for r in rows:
    if r["tier"] not in tiers:
        raise SystemExit(f"ERROR: unknown source tier {r['tier']}")
free_priority=min(int(r["priority"]) for r in rows if r["tier"] in {"PRIMARY","DERIVED_FREE","OPEN_SOURCE"})
if any(r["tier"]=="PAID" and int(r["priority"]) < free_priority for r in rows):
    raise SystemExit("ERROR: paid source has higher priority than free/official sources")
for r in rows:
    if not r["url_or_repo"].startswith(("https://","git+https://")):
        raise SystemExit(f"ERROR: invalid URL for {r['source_id']}")
print(f"PASS: source manifest contains {len(rows)} sources with free/primary sources prioritized")
