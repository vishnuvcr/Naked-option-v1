from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"data/reports/phase4_family_c_results.json"
methods=[f"C{i:02d}" for i in range(1,12)]
if not p.exists(): raise SystemExit("ERROR: missing Family C result artifact")
d=json.loads(p.read_text())
for scope in ["daily","intraday"]:
    for h,b in d[scope]["horizons"].items():
        miss=[m for m in methods if m not in b]
        if miss: raise SystemExit(f"ERROR: {scope} {h} missing {miss}")
        for m in methods:
            x=b[m]
            if x.get("status")=="EXECUTED":
                n=int(x["n"])
                bn=sum(int(v.get("n",0)) for v in x.get("future_return_by_probability_bin",{}).values())
                cm=sum(int(x[k]) for k in ["tn","fp","fn","tp"])
                if bn!=n or cm!=n:
                    raise SystemExit(f"ERROR: {scope} {h} {m} denominator mismatch")
            elif x.get("status") not in {"BLOCKED_DATA"}:
                raise SystemExit(f"ERROR: {scope} {h} {m} invalid status {x.get('status')}")
print("PASS: Family C result schema")
