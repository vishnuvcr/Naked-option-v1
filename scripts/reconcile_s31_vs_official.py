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
        if x.lower() in low:return low[x.lower()]
    norm={x.lower().replace("_","") for x in cands}
    for c in cols:
        if c.lower().replace("_","") in norm:return c
    return None

def dt(v):
    if isinstance(v,datetime.datetime): return v
    if isinstance(v,datetime.date): return datetime.datetime.combine(v,datetime.time())
    return datetime.datetime.fromisoformat(str(v).strip().replace("Z","").replace(" ","T"))

def d(v): return dt(v).date()

def num(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except:
        return None

if not OFFICIAL.exists() or not MANIFEST.exists():
    raise SystemExit("ERROR: required S31 reconciliation inputs missing")

meta=json.loads(MANIFEST.read_text())
selected_expiry=datetime.date(2024,7,11)
files=[ROOT/x["path"] for x in meta["files"] if x["status"]=="ok"]

with zipfile.ZipFile(OFFICIAL) as z:
    name=[n for n in z.namelist() if n.lower().endswith(".csv")][0]
    with z.open(name) as fh:
        rows=list(csv.DictReader(io.StringIO(fh.read().decode("utf-8-sig",errors="replace"))))

official={}
for r in rows:
    if r.get("TckrSymb","").strip()!="NIFTY": continue
    typ=r.get("OptnTp","").strip().upper()
    if typ not in {"CE","PE"}: continue
    try:
        exp=d(r["XpryDt"])
    except:
        continue
    if exp!=selected_expiry: continue
    strike=num(r.get("StrkPric"))
    lp=num(r.get("LastPric"))
    if strike is not None and lp is not None:
        official[(exp,strike,typ)]=lp

reports=[]
for p in files:
    table=pq.read_table(p)
    cols=list(table.column_names)
    mapping={
        "timestamp":pick(cols,["datetime","timestamp","date_time","time"]),
        "date":pick(cols,["date","trading_date","trade_date"]),
        "expiry":pick(cols,["expiry","expiry_date","expiryDate"]),
        "strike":pick(cols,["strike","strike_price","strikePrice"]),
        "type":pick(cols,["option_type","optionType","type","opt_type"]),
        "close":pick(cols,["close","close_price","cls_price"]),
    }
    critical=["timestamp","expiry","strike","type","close"]
    missing=[k for k in critical if mapping[k] is None]
    if missing:
        reports.append({"file":p.name,"status":"NOT_COMPARABLE","missing":missing})
        continue

    latest={}
    for i in range(table.num_rows):
        try:
            exp=d(table[mapping["expiry"]][i].as_py())
            if exp!=selected_expiry: continue
            st=num(table[mapping["strike"]][i].as_py())
            typ=str(table[mapping["type"]][i].as_py()).upper()
            if st is None or typ not in {"CE","PE"}: continue
            ts=dt(table[mapping["timestamp"]][i].as_py())
            cl=num(table[mapping["close"]][i].as_py())
            key=(exp,st,typ)
            if key not in latest or ts>latest[key][0]:
                latest[key]=(ts,cl)
        except Exception:
            continue

    matched=set(official)&set(latest)
    usable=[k for k in matched if latest[k][1] is not None]
    within=sum(abs(official[k]-latest[k][1])<=max(0.05,0.0025*abs(official[k])) for k in usable)
    frac=within/max(1,len(usable))
    reports.append({
        "file":p.name,
        "status":"PASS" if frac>=0.99 and len(matched)>=20 else "FAIL",
        "matched_keys":len(matched),
        "usable_keys":len(usable),
        "strict_last_price_tolerance_fraction":frac,
    })

report={
    "dataset":"artist-23/nifty-options-data",
    "selected_expiry":selected_expiry.isoformat(),
    "reports":reports,
}
(OUT/"s31_reconciliation.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
print(json.dumps(report,indent=2,default=str))
