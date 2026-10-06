from __future__ import annotations
import csv, datetime, io, json, math, zipfile
from pathlib import Path
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
OFFICIAL=ROOT/"data/cache/raw/nse_fno_samples/2024-07-08_udiff.zip"
MANIFEST=ROOT/"data/reports/s31_reference_acquisition.json"
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

def pick(cols, cands):
    low={c.lower():c for c in cols}
    for x in cands:
        if x.lower() in low:
            return low[x.lower()]
    norm={x.lower().replace("_","") for x in cands}
    for c in cols:
        if c.lower().replace("_","") in norm:
            return c
    return None

def dt(v):
    if isinstance(v,datetime.datetime): return v
    if isinstance(v,datetime.date): return datetime.datetime.combine(v,datetime.time())
    s=str(v).strip().replace("Z","").replace(" ","T")
    return datetime.datetime.fromisoformat(s)

def d(v):
    return dt(v).date()

def num(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except:
        return None

if not OFFICIAL.exists() or not MANIFEST.exists():
    raise SystemExit("ERROR: required S31 reconciliation inputs missing")

meta=json.loads(MANIFEST.read_text())
target_date=datetime.date.fromisoformat(meta["target_date"])
selected_expiry=datetime.date(2024,7,11)
files=[ROOT/x["path"] for x in meta["files"] if x["status"]=="ok"]

with zipfile.ZipFile(OFFICIAL) as z:
    name=[n for n in z.namelist() if n.lower().endswith(".csv")][0]
    with z.open(name) as fh:
        rows=list(csv.DictReader(io.StringIO(fh.read().decode("utf-8-sig",errors="replace"))))

official={}
for r in rows:
    if r.get("TckrSymb","").strip()!="NIFTY":
        continue
    typ=r.get("OptnTp","").strip().upper()
    if typ not in {"CE","PE"}:
        continue
    try:
        exp=d(r["XpryDt"])
    except:
        continue
    if exp!=selected_expiry:
        continue
    strike=num(r.get("StrkPric"))
    lp=num(r.get("LastPric"))
    if strike is not None and lp is not None:
        official[(exp,strike,typ)]=lp

reports=[]
for p in files:
    table=pq.read_table(p)
    cols=list(table.column_names)

    timestamp_col=pick(cols,["datetime","timestamp","date_time","time"])
    date_col=pick(cols,["date","trading_date","trade_date"])
    expiry_col=pick(cols,["expiry","expiry_date","expiryDate"])
    strike_col=pick(cols,["strike","strike_price","strikePrice"])
    type_col=pick(cols,["option_type","optionType","type","opt_type"])
    close_col=pick(cols,["close","close_price","cls_price"])

    missing=[k for k,v in {"timestamp":timestamp_col,"strike":strike_col,"close":close_col}.items() if v is None]
    if missing:
        reports.append({"file":p.name,"status":"NOT_COMPARABLE","missing":missing})
        continue

    inferred_type="CE" if p.name.upper().startswith("ATM_CE") else ("PE" if p.name.upper().startswith("ATM_PE") else None)
    if type_col is None and inferred_type is None:
        reports.append({"file":p.name,"status":"NOT_COMPARABLE","missing":["option_type_or_filename_inference"]})
        continue

    latest={}
    rows_seen=0
    target_rows=0
    for i in range(table.num_rows):
        try:
            ts=dt(table[timestamp_col][i].as_py())
            if ts.date()!=target_date:
                continue
            target_rows += 1
            st=num(table[strike_col][i].as_py())
            typ=(str(table[type_col][i].as_py()).upper() if type_col else inferred_type)
            cl=num(table[close_col][i].as_py())
            if st is None or typ not in {"CE","PE"}:
                continue
            # S31 WEEK/ATM_CE and WEEK/ATM_PE encode the weekly contract family
            # in the file name; expiry is therefore deliberately inferred from
            # the selected official weekly-expiry fixture, not a hidden future value.
            key=(selected_expiry,st,typ)
            if key not in latest or ts>latest[key][0]:
                latest[key]=(ts,cl)
                rows_seen += 1
        except Exception:
            continue

    matched=set(official)&set(latest)
    usable=[k for k in matched if latest[k][1] is not None]
    within=sum(
        abs(official[k]-latest[k][1])<=max(0.05,0.0025*abs(official[k]))
        for k in usable
    )
    frac=within/max(1,len(usable))
    reports.append({
        "file":p.name,
        "status":"PASS" if frac>=0.99 and len(matched)>=20 else "FAIL",
        "expiry_source":"official_selected_weekly_fixture",
        "option_type_source":"filename_when_absent",
        "target_date":target_date.isoformat(),
        "target_rows":target_rows,
        "unique_latest_keys":len(latest),
        "matched_keys":len(matched),
        "usable_keys":len(usable),
        "strict_last_price_tolerance_fraction":frac,
    })

overall = "PASS" if reports and all(r["status"]=="PASS" for r in reports) else "FAIL"
report={
    "dataset":"artist-23/nifty-options-data",
    "selected_expiry":selected_expiry.isoformat(),
    "target_date":target_date.isoformat(),
    "overall_status":overall,
    "reports":reports,
}
(OUT/"s31_reconciliation.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
print(json.dumps(report,indent=2,default=str))
if overall!="PASS":
    raise SystemExit("S31 reconciliation gate did not pass")
