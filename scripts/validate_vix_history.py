from __future__ import annotations

import csv
import datetime as dt
import json
import io
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
meta_path=ROOT/"data/reports/india_vix_history_acquisition.json"
if not meta_path.exists():
    raise SystemExit("ERROR: VIX acquisition manifest missing")
meta=json.loads(meta_path.read_text())
rows=0
dates=[]

def append_row(date_raw, val_raw):
    global rows
    if not date_raw or val_raw in (None,""):
        return
    try:
        date=dt.datetime.fromisoformat(str(date_raw).replace("T"," ").replace("Z","")).date()
        value=float(str(val_raw).replace(",",""))
    except Exception:
        return
    if value<=0:
        raise SystemExit(f"ERROR: non-positive India VIX value on {date}")
    dates.append(date)
    rows+=1

for rec in meta["records"]:
    raw=(ROOT/rec["path"]).read_text(encoding="utf-8-sig",errors="replace")
    parsed=False
    try:
        data=json.loads(raw)
        data_rows=data.get("data",data if isinstance(data,list) else [])
        if data_rows:
            for row in data_rows:
                append_row(
                    row.get("EOD_TIMESTAMP") or row.get("date") or row.get("Date") or row.get("timestamp"),
                    row.get("EOD_CLOSE_INDEX_VAL") or row.get("close") or row.get("value"),
                )
            parsed=True
    except Exception:
        parsed=False
    if not parsed:
        reader=csv.DictReader(io.StringIO(raw))
        if not reader.fieldnames:
            raise SystemExit(f"ERROR: VIX response is neither JSON nor CSV: {rec['path']}")
        for row in reader:
            append_row(
                row.get("EOD_TIMESTAMP") or row.get("date") or row.get("Date") or row.get("timestamp"),
                row.get("EOD_CLOSE_INDEX_VAL") or row.get("close") or row.get("value") or row.get("Close"),
            )

if not dates:
    raise SystemExit("ERROR: no usable India VIX observations parsed")
if len(dates)!=len(set(dates)):
    raise SystemExit("ERROR: duplicate India VIX dates across chunks")

report={
    "window_start":min(dates).isoformat(),
    "window_end":max(dates).isoformat(),
    "rows":rows,
    "unique_dates":len(set(dates)),
    "status":"PASS",
}
(ROOT/"data/reports/india_vix_history_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
