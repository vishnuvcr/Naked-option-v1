from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
required=[
    "india_vix_history_acquisition.json",
    "india_vix_history_validation.json",
    "global_reference_window.json",
]
for name in required:
    if not (ROOT/"data/reports"/name).exists():
        raise SystemExit(f"ERROR: missing Phase 2C report {name}")

vix=json.loads((ROOT/"data/reports/india_vix_history_validation.json").read_text())
if vix.get("status")!="PASS" or vix.get("rows",0)<1000:
    raise SystemExit("ERROR: India VIX history is incomplete or failed validation")

glob=json.loads((ROOT/"data/reports/global_reference_window.json").read_text())
if len(glob.get("records",[]))<5:
    raise SystemExit("ERROR: expected five global/rates series")

for rec in glob["records"]:
    if rec.get("rows",0)<500:
        raise SystemExit(f"ERROR: global series too short: {rec.get('source_id')}")
    if not rec.get("sha256"):
        raise SystemExit(f"ERROR: missing hash for {rec.get('source_id')}")

print("PASS: Phase 2C contextual bulk completeness checks")
