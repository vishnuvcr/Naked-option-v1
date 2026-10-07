from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"data/reports/phase4_classical_results.json"
METHODS=[f"B{i:02d}" for i in range(1,14)]

if not R.exists():
    raise SystemExit("ERROR: missing Phase 4 classical result artifact")
d=json.loads(R.read_text(encoding="utf-8"))

for scope in ["daily","intraday"]:
    if scope not in d:
        raise SystemExit(f"ERROR: missing scope {scope}")
    for h, block in d[scope]["horizons"].items():
        missing=[m for m in METHODS if m not in block]
        if missing:
            raise SystemExit(f"ERROR: {scope} horizon {h} missing {missing}")
        for m in METHODS:
            x=block[m]
            if x.get("status")=="EXECUTED":
                n=int(x.get("n",0))
                bins=x.get("future_return_by_probability_bin",{})
                bn=sum(int(v.get("n",0)) for v in bins.values())
                if bn!=n:
                    raise SystemExit(f"ERROR: {scope} {h} {m} bin denominator {bn} != n {n}")
                cm=sum(int(x[k]) for k in ["tn","fp","fn","tp"])
                if cm!=n:
                    raise SystemExit(f"ERROR: {scope} {h} {m} confusion count {cm} != n {n}")
            elif x.get("status") not in {"BLOCKED_DATA","NOT_APPLICABLE"}:
                raise SystemExit(f"ERROR: {scope} {h} {m} invalid status {x.get('status')}")

print("PASS: Phase 4 classical family result schema")
