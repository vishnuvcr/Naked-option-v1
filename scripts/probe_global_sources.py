from __future__ import annotations

from pathlib import Path
import csv
import json
import time
import urllib.request
import datetime

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "data" / "GLOBAL_SOURCE_MANIFEST.csv"
OUT = ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept": "text/html,application/json,text/csv,*/*",
}
TIMEOUT = 20

def probe(url: str):
    start = time.time()
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            sample = resp.read(4096)
            return {
                "status": resp.status,
                "content_type": resp.headers.get("Content-Type"),
                "bytes_sampled": len(sample),
                "latency_sec": round(time.time()-start, 3),
                "error": None,
            }
    except Exception as exc:
        return {
            "status": None,
            "content_type": None,
            "bytes_sampled": 0,
            "latency_sec": round(time.time()-start, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }

with MANIFEST.open("r", encoding="utf-8", newline="") as fh:
    rows=list(csv.DictReader(fh))

results=[]
for row in rows:
    results.append({**row, **probe(row["url_or_repo"])})

report={
    "generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "results":results,
}
(OUT/"global_source_probe.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(OUT/"global_source_probe.json")
