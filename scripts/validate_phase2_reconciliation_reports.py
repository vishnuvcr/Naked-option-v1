from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
required = {
    "official_vs_hf_reconciliation.json": "PASS",
    "s31_reconciliation.json": None,
}

for name, expected in required.items():
    path = ROOT / "data" / "reports" / name
    if not path.exists():
        raise SystemExit(f"ERROR: missing reconciliation artifact {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if expected is not None and data.get("status") != expected:
        raise SystemExit(f"ERROR: {name} status is {data.get('status')}, expected {expected}")
    if name == "s31_reconciliation.json":
        reports = data.get("reports", [])
        if not reports:
            raise SystemExit("ERROR: S31 reconciliation contains no file-level reports")
        for r in reports:
            if r.get("status") not in {"PASS", "FAIL", "NOT_COMPARABLE"}:
                raise SystemExit(f"ERROR: unexpected S31 report status {r.get('status')}")

print("PASS: mandatory Phase 2 reconciliation artifacts exist and have explicit statuses")
