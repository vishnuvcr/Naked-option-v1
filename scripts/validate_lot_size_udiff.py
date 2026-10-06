from __future__ import annotations
from pathlib import Path
import csv, datetime, io, json, zipfile

ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/"data/cache/raw/nse_fno_samples/2024-07-08_udiff.zip"
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

if not ZIP.exists():
    raise SystemExit("ERROR: official UDiFF sample missing")

with zipfile.ZipFile(ZIP) as z:
    names=[n for n in z.namelist() if n.lower().endswith(".csv")]
    with z.open(names[0]) as fh:
        rows=list(csv.DictReader(io.StringIO(fh.read().decode("utf-8-sig",errors="replace"))))

expiry=datetime.date(2024,7,11)
aliases=["NewBrdLotQty","NewBrdLotQtyPerOrder","BoardLotQty","LotSize","NewBrdLot"]
field=next((x for x in aliases if rows and x in rows[0]),None)
if field is None:
    raise SystemExit(f"ERROR: UDiFF lot-size field not found; available candidates missing. Headers: {list(rows[0])[:80] if rows else []}")

values=[]
for r in rows:
    if r.get("TckrSymb","").strip()!="NIFTY":
        continue
    if r.get("OptnTp","").strip().upper() not in {"CE","PE"}:
        continue
    try:
        exp=datetime.date.fromisoformat(r["XpryDt"].split("T")[0])
    except Exception:
        continue
    if exp!=expiry:
        continue
    try:
        v=int(float(r.get(field,"")))
    except Exception:
        continue
    if v>0:
        values.append(v)

uniq=sorted(set(values))
if not uniq:
    raise SystemExit("ERROR: no positive NIFTY lot-size values found")
report={
    "trade_date":"2024-07-08",
    "expiry":expiry.isoformat(),
    "field":field,
    "unique_lot_sizes":uniq,
    "row_count":len(values),
    "status":"PASS" if len(uniq)==1 else "FAIL",
    "pit_rule":"use this effective-dated official value for the 2024-07-08 regime; never forward/backfill across an unverified regime change",
}
(OUT/"lot_size_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if len(uniq)!=1:
    raise SystemExit(f"ERROR: multiple NIFTY lot sizes found: {uniq}")
print(json.dumps(report,indent=2))
