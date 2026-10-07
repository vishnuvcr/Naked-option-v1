from pathlib import Path
import csv
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data" / "fixtures" / "pit_fixture.csv"

def dt(s):
    return datetime.fromisoformat(s)

with path.open("r", encoding="utf-8", newline="") as fh:
    rows = list(csv.DictReader(fh))

for r in rows:
    decision = dt(r["decision_time"])
    obs = dt(r["observation_time"])
    avail = dt(r["available_at"])
    usable = avail <= decision and obs <= decision
    expected = r["case"] == "usable"
    if usable != expected:
        raise SystemExit(
            f"ERROR: PIT rule mismatch for case={r['case']}: "
            f"decision={decision}, obs={obs}, available={avail}, usable={usable}"
        )

print("PASS: synthetic PIT fixture rejects future observations and future availability")
