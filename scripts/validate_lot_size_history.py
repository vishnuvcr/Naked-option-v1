from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/cache/derived/official_nifty_eod"
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

files=sorted(DATA.glob("nifty_option_eod_*.parquet"))
if not files:
    raise SystemExit("ERROR: no yearly NIFTY Parquet files available")

by_date=defaultdict(set)
coverage={}
for path in files:
    table=pq.read_table(path,columns=["trade_date","lot_size"])
    dates=table["trade_date"].to_pylist()
    lots=table["lot_size"].to_pylist()
    covered=0
    for d,v in zip(dates,lots):
        if v is not None and float(v)>0:
            by_date[str(d)].add(int(float(v)))
            covered+=1
    coverage[path.name]={"rows":table.num_rows,"lot_size_rows":covered}

conflicts={d:sorted(v) for d,v in by_date.items() if len(v)>1}
missing_dates=[d for d,v in by_date.items() if not v]

report={
    "files":coverage,
    "known_daily_lot_size_values":{d:sorted(v) for d,v in by_date.items()},
    "conflicting_dates":conflicts,
    "known_days":len(by_date),
    "conflict_days":len(conflicts),
    "status":"PASS" if not conflicts else "FAIL",
    "policy":"Known official lot-size fields are retained with effective dates. Missing legacy-era lot size remains quarantined rather than inferred silently.",
}
(OUT/"lot_size_history_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if conflicts:
    raise SystemExit(f"ERROR: conflicting lot sizes on {len(conflicts)} dates")
print(json.dumps({"known_days":len(by_date),"conflict_days":len(conflicts),"status":report["status"]},indent=2))
