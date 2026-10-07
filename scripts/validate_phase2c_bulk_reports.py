from __future__ import annotations
import json
from pathlib import Path
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/reports"
DERIVED=ROOT/"data/cache/derived/official_nifty_eod"
YEARS=list(range(2019,2027))
missing=[]
failed=[]
small=[]
for year in YEARS:
    v=REPORT/f"nse_year_{year}_validation.json"
    p=REPORT/f"nifty_option_eod_{year}_parquet.json"
    q=DERIVED/f"nifty_option_eod_{year}.parquet"
    if not v.exists() or not p.exists() or not q.exists():
        missing.append(year)
        continue
    vm=json.loads(v.read_text())
    pm=json.loads(p.read_text())
    if vm.get("status")!="PASS":
        failed.append((year,vm.get('status')))
    if pm.get("rows",0)<=0:
        small.append(year)
    table=pq.read_table(q,columns=["trade_date","expiry","strike","option_type"])
    keys=list(zip(table['trade_date'].to_pylist(),table['expiry'].to_pylist(),table['strike'].to_pylist(),table['option_type'].to_pylist()))
    if len(keys)!=len(set(keys)):
        failed.append((year,'parquet_duplicate_keys'))
for name in ["india_vix_history_validation.json","global_reference_window.json","india_vix_history_acquisition.json"]:
    if not (REPORT/name).exists():
        missing.append(name)
if missing or failed or small:
    raise SystemExit(f'ERROR: Phase 2C bulk gate failed; missing={missing}, failed={failed}, small={small}')
glob=json.loads((REPORT/"global_reference_window.json").read_text())
records=glob.get("records",[])
if len(records)<5:
    raise SystemExit('ERROR: fewer than 5 global/rates series')
if any(int(r.get("rows",0))<=0 or int(r.get("numeric_value_rows",0))<=0 for r in records):
    raise SystemExit('ERROR: global/rates series contains no numeric observations')
if any(not r.get("provider") for r in records):
    raise SystemExit('ERROR: global/rates provider not recorded')
vix=json.loads((REPORT/"india_vix_history_validation.json").read_text())
if vix.get("status")!="PASS":
    raise SystemExit('ERROR: India VIX validation did not pass')
print("PASS: all 2019-2026 official NSE year artifacts and contextual histories are present")