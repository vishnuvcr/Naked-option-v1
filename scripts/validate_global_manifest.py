from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]
for name in ["SOURCE_MANIFEST.csv","GLOBAL_SOURCE_MANIFEST.csv"]:
    path=ROOT/"research"/"data"/name
    with path.open("r",encoding="utf-8",newline="") as fh:
        rows=list(csv.DictReader(fh))
    required={"source_id","tier","source_name","url_or_repo","coverage_or_role","priority","status","license_note"}
    for r in rows:
        if set(r)!=required:
            raise SystemExit(f"ERROR: {name} schema mismatch")
        if not r["url_or_repo"].startswith("https://"):
            raise SystemExit(f"ERROR: invalid URL for {r['source_id']}")
        if int(r["priority"])<1:
            raise SystemExit(f"ERROR: invalid priority for {r['source_id']}")
print("PASS: global and local source manifests parse")
