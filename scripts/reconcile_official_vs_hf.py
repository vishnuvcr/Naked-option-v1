from __future__ import annotations
from pathlib import Path
import csv
import io
import json
import zipfile
import math
import datetime
import hashlib

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "data" / "cache" / "raw" / "nse_fno_samples" / "2024-07-08_udiff.zip"
HF_MANIFEST = ROOT / "data" / "reports" / "hf_reference_acquisition.json"
OUT = ROOT / "data" / "reports"
OUT.mkdir(parents=True,exist_ok=True)

if not OFFICIAL.exists():
    raise SystemExit("ERROR: official UDiFF sample missing")
if not HF_MANIFEST.exists():
    raise SystemExit("ERROR: HF acquisition manifest missing")

hf_meta=json.loads(HF_MANIFEST.read_text(encoding="utf-8"))
hf_path=ROOT / hf_meta["local_path"]
if not hf_path.exists():
    raise SystemExit("ERROR: HF reference file missing")

def pick(cols, candidates):
    lower={c.lower():c for c in cols}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    for c in cols:
        if c.lower().replace("_","") in {x.lower().replace("_","") for x in candidates}:
            return c
    return None

table=pq.read_table(hf_path)
cols=list(table.column_names)

mapping={
    "date": pick(cols,["date","datetime","timestamp"]),
    "expiry": pick(cols,["expiry","expiry_date","expiryDate"]),
    "strike": pick(cols,["strike","strike_price","strikePrice"]),
    "option_type": pick(cols,["option_type","optionType","type","opt_type"]),
    "close": pick(cols,["close","cls_price","close_price"]),
    "open": pick(cols,["open","opn_price","open_price"]),
    "high": pick(cols,["high","high_price"]),
    "low": pick(cols,["low","low_price"]),
    "volume": pick(cols,["volume","traded_volume"]),
    "oi": pick(cols,["oi","open_interest"]),
    "spot": pick(cols,["spot","underlying","underlying_value","underlying_price"]),
}
critical=["date","expiry","strike","option_type","close"]
missing=[k for k in critical if mapping[k] is None]
if missing:
    raise SystemExit(f"ERROR: HF schema cannot be mapped for critical fields: {missing}")

import pyarrow.compute as pc
hf=table
date_col=hf[mapping["date"]]
if str(date_col.type).startswith("timestamp"):
    date_vals=pc.cast(date_col, "date32")
else:
    date_vals=pc.cast(date_col, "date32")
mask=pc.equal(date_vals, __import__("pyarrow").scalar(datetime.date(2024,7,8), type=__import__("pyarrow").date32()))
hf_day=hf.filter(mask)

# Normalize official UDiFF.
with zipfile.ZipFile(OFFICIAL) as z:
    csv_names=[n for n in z.namelist() if n.lower().endswith(".csv")]
    with z.open(csv_names[0]) as fh:
        text=fh.read().decode("utf-8-sig",errors="replace")
rows=list(csv.DictReader(io.StringIO(text)))
nifty=[]
for r in rows:
    if r.get("TckrSymb","").strip()=="NIFTY" and r.get("OptnTp","").strip() in {"CE","PE"}:
        try:
            expiry=datetime.date.fromisoformat(r["XpryDt"].split("T")[0])
            strike=float(r["StrkPric"])
            close=float(r["ClsPric"])
            nifty.append((expiry,strike,r["OptnTp"].strip(),close,float(r.get("UndrlygPric",r.get("UndrlygPric_1", "nan")) or "nan")))
        except Exception:
            continue

# Convert HF rows into deterministic keys.
import pyarrow
def scalar_list(col):
    return col.to_pylist()

hf_rows=[]
for i in range(hf_day.num_rows):
    def get(k):
        return hf_day[mapping[k]][i].as_py()
    d=get("date")
    if isinstance(d,datetime.datetime): d=d.date()
    elif isinstance(d,str): d=datetime.datetime.fromisoformat(d).date()
    try:
        exp=get("expiry")
        if isinstance(exp,datetime.datetime): exp=exp.date()
        elif isinstance(exp,datetime.date): exp=exp
        else: exp=datetime.datetime.fromisoformat(str(exp)).date()
        strike=float(get("strike"))
        opt=str(get("option_type")).upper()
        close=float(get("close"))
    except Exception:
        continue
    hf_rows.append((exp,strike,opt,close))

off_map={(e,s,o):(c,spot) for e,s,o,c,spot in nifty}
hf_map={}
for e,s,o,c in hf_rows:
    hf_map[(e,s,o)]=c

matched=set(off_map)&set(hf_map)
if not matched:
    raise SystemExit("ERROR: zero matched NIFTY option keys between official UDiFF and HF reference")

abs_err=[]
rel_err=[]
for k in matched:
    a=off_map[k][0]
    b=hf_map[k]
    if not math.isfinite(a) or not math.isfinite(b):
        continue
    abs_err.append(abs(a-b))
    if a!=0:
        rel_err.append(abs(a-b)/abs(a))

within_tick=sum(e <= max(0.05,0.0025*abs(off_map[k][0])) for k,e in [(k,abs(off_map[k][0]-hf_map[k])) for k in matched if math.isfinite(off_map[k][0])])/max(1,len(matched))
report={
    "official_snapshot":"2024-07-08_UDiFF",
    "hf_dataset":hf_meta["dataset"],
    "hf_file":hf_meta["selected_file"],
    "official_nifty_option_rows":len(nifty),
    "hf_nifty_day_rows":len(hf_rows),
    "matched_contract_keys":len(matched),
    "official_key_coverage_of_hf":len(matched)/max(1,len(hf_rows)),
    "hf_key_coverage_of_official":len(matched)/max(1,len(nifty)),
    "median_abs_close_error":sorted(abs_err)[len(abs_err)//2] if abs_err else None,
    "p95_abs_close_error":sorted(abs_err)[min(len(abs_err)-1,int(0.95*len(abs_err)))] if abs_err else None,
    "median_relative_close_error":sorted(rel_err)[len(rel_err)//2] if rel_err else None,
    "within_tolerance_fraction":within_tick,
    "critical_schema_mapping":mapping,
}
(OUT/"official_vs_hf_reconciliation.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
print(json.dumps(report,indent=2,default=str))
