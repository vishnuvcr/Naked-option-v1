from __future__ import annotations
from pathlib import Path
import hashlib
import json
import csv
import zipfile
import io
import datetime

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cache" / "raw" / "nse_fno_samples"
OUT = ROOT / "data" / "manifests"
OUT.mkdir(parents=True, exist_ok=True)

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def row_count(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.lower().endswith((".csv",".txt"))]
        with z.open(names[0]) as fh:
            data=fh.read()
    text=data.decode("utf-8-sig", errors="replace")
    return max(0, sum(1 for _ in csv.reader(io.StringIO(text))) - 1)

records=[]
for path in sorted(RAW.glob("*.zip")):
    records.append({
        "snapshot_id": f"NSEFO-{path.stem}",
        "source_id": "S01",
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "row_count": row_count(path),
        "parser_version": "phase2-snapshot-v1",
    })
manifest={
    "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "records": records,
}
(OUT/"phase2_official_option_samples.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(OUT/"phase2_official_option_samples.json")
