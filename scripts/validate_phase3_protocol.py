from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

required = [
    "research/phase3/LABEL_PROTOCOL.md",
    "research/phase3/BASELINE_PROTOCOL.md",
    "research/phase3/OPTION_BREAKEVEN_PROTOCOL.md",
    "research/phase3/DATA_REQUIREMENTS.md",
    "research/phase3/COST_BREAK_EVEN_CONFIG.json",
]

for rel in required:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"ERROR: missing {rel}")

cfg = json.loads((ROOT / "research/phase3/COST_BREAK_EVEN_CONFIG.json").read_text())
scenarios = cfg["scenarios"]
expected = {"optimistic","base","adverse","extreme"}
if set(scenarios) != expected:
    raise SystemExit("ERROR: cost scenario set mismatch")

slips = [scenarios[x]["slippage_points"] for x in ["optimistic","base","adverse","extreme"]]
if slips != sorted(slips) or slips[0] < 0:
    raise SystemExit("ERROR: slippage scenarios are not monotonic")

label = (ROOT / "research/phase3/LABEL_PROTOCOL.md").read_text()
for phrase in ["5 minutes","15 minutes","30 minutes","60 minutes","120 minutes","+1 trading session","+5","+10 sessions","NO TRADE","leakage"]:
    if phrase not in label:
        raise SystemExit(f"ERROR: label protocol missing {phrase}")

baseline = (ROOT / "research/phase3/BASELINE_PROTOCOL.md").read_text()
for baseline_id in ["B0","B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","B11"]:
    if baseline_id not in baseline:
        raise SystemExit(f"ERROR: baseline {baseline_id} missing")

print("PASS: Phase 3 label, baseline, data and cost protocols are frozen")
