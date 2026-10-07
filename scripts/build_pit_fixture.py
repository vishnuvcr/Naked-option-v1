from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "data" / "fixtures" / "pit_fixture.csv"
out.parent.mkdir(parents=True, exist_ok=True)

rows = [
    ["decision_time","observation_time","available_at","value","source_id","case"],
    ["2026-01-05T09:30:00+05:30","2026-01-05T09:15:00+05:30","2026-01-05T09:20:00+05:30","101","SYN","usable"],
    ["2026-01-05T09:30:00+05:30","2026-01-05T09:15:00+05:30","2026-01-05T09:35:00+05:30","102","SYN","future_available"],
    ["2026-01-05T10:00:00+05:30","2026-01-05T09:55:00+05:30","2026-01-05T09:59:00+05:30","103","SYN","usable"],
    ["2026-01-05T10:00:00+05:30","2026-01-05T10:05:00+05:30","2026-01-05T10:06:00+05:30","104","SYN","future_observation"],
]
with out.open("w", encoding="utf-8", newline="") as fh:
    csv.writer(fh).writerows(rows)
print(out)
