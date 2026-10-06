from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
meta_path=ROOT/"data/reports/india_vix_history_acquisition.json"
if not meta_path.exists():
    raise SystemExit("ERROR: VIX acquisition manifest missing")
meta=json.loads(meta_path.read_text())
rows=0
dates=[]
for rec in meta["records"]:
    raw=(ROOT/rec["path"]).read_text(encoding="utf-8",errors="replace")
    try:
        data=json.loads(raw)
    except Exception:
        raise SystemExit("ERROR: VIX acquisition response is not JSON; inspect endpoint format")
    data_rows=data.get("data",data if isinstance(data,list) else [])
    if not data_rows:
        raise SystemExit(f"ERROR: empty VIX block {rec['from']} to {rec['to']}")
    for row in data_rows:
        date_raw=row.get("EOD_TIMESTAMP") or row.get("date") or row.get("Date") or row.get("timestamp")
        val_raw=row.get("EOD_CLOSE_INDEX_VAL") or row.get("close") or row.get("value")
        if not date_raw or val_raw in (None,""):
            continue
        try:
            date=dt.datetime.fromisoformat(str(date_raw).replace("T"," ").replace("Z","")).date()
            value=float(str(val_raw).replace(",",""))
        except Exception:
            continue
        if value<=0:
            raise SystemExit(f"ERROR: non-positive India VIX value on {date}")
        dates.append(date)
        rows+=1
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
