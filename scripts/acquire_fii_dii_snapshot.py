from __future__ import annotations
from pathlib import Path
import datetime, json, urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

url="https://www.nseindia.com/api/fiidiiTradeReact"
headers={
    "User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept":"application/json,text/plain,*/*",
    "Referer":"https://www.nseindia.com/",
}
req=urllib.request.Request(url,headers=headers)
with urllib.request.urlopen(req,timeout=30) as resp:
    raw=resp.read()
try:
    data=json.loads(raw.decode("utf-8"))
except Exception as exc:
    raise SystemExit(f"ERROR: NSE FII/DII endpoint did not return JSON: {exc}")

if not isinstance(data,list) or not data:
    raise SystemExit("ERROR: NSE FII/DII response is empty or not a list")

sample=data[:5]
report={
    "retrieved_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_url":url,
    "row_count":len(data),
    "sample":sample,
    "availability_rule":"FII/FPI/DII values are used only after their publication/availability timestamp; when historical publication time cannot be demonstrated, default to next Indian trading session",
    "status":"PASS",
}
(OUT/"fii_dii_snapshot.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
print(json.dumps({"row_count":len(data),"status":"PASS"},indent=2))
