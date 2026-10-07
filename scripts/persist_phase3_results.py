from __future__ import annotations
from pathlib import Path
import json
import os
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/reports"
GATE=ROOT/"research/gates/PHASE3_DATA_RUN.md"

required=[
    "nifty50_daily_manifest.json",
    "hf_intraday_discovery.json",
    "hf_intraday_acquisition.json",
    "phase3_daily_baseline_results.json",
    "phase3_intraday_baseline_results.json",
]
data={}
for name in required:
    p=REPORT/name
    if not p.exists():
        raise SystemExit(f"ERROR: missing result report {name}")
    data[name]=json.loads(p.read_text(encoding="utf-8"))

daily=data["phase3_daily_baseline_results.json"]
intr=data["phase3_intraday_baseline_results.json"]
hf=data["hf_intraday_acquisition.json"]
nifty=data["nifty50_daily_manifest.json"]

lines=[
"# Phase 3 Data Run",
"",
f"- Generated UTC: {datetime.now(timezone.utc).isoformat()}",
f"- GitHub run: {os.environ.get('GITHUB_RUN_NUMBER','unknown')}",
f"- Commit: {os.environ.get('GITHUB_SHA','unknown')}",
"",
"## Daily data",
f"- Rows: {nifty.get('rows')}",
f"- Range: {nifty.get('observed_start')} to {nifty.get('observed_end')}",
f"- SHA-256: {nifty.get('sha256')}",
f"- Source: {nifty.get('source')}",
"",
"## Intraday reference",
f"- Dataset: {hf.get('dataset')}",
f"- Revision: {hf.get('revision')}",
f"- Rows: {hf.get('rows')}",
f"- Span days: {hf.get('span_days')}",
f"- Status: {hf.get('status')}",
f"- SHA-256: {hf.get('sha256')}",
"",
"## Daily baseline coverage",
f"- Data rows evaluated: {daily.get('data_rows')}",
f"- Horizons: {', '.join(daily.get('horizons',{}).keys())}",
"",
"## Intraday baseline coverage",
f"- Full rows: {intr.get('full_rows')}",
f"- Decision-grid rows: {intr.get('rows')}",
f"- Status: {intr.get('status')}",
f"- Horizons: {', '.join(intr.get('horizons',{}).keys())}",
"",
"## Gate interpretation",
"- These are implementation/data-run results only; no method family beyond registered baselines is being accepted from this run.",
"- Derived intraday data remain non-canonical and are subject to the Phase 2 source restrictions.",
"- A separate tester gate must independently reproduce labels and B0-B11 metrics before Phase 3 is passed.",
]
GATE.write_text("\n".join(lines)+"\n",encoding="utf-8")
print(GATE)
