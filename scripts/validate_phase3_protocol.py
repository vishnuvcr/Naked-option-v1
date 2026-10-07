from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

required = [
    "research/phase3/LABEL_PROTOCOL.md",
    "research/phase3/BASELINE_PROTOCOL.md",
    "research/phase3/OPTION_BREAKEVEN_PROTOCOL.md",
    "research/phase3/DATA_REQUIREMENTS.md",
    "research/phase3/BASELINE_DATA_GAPS.md",
    "research/phase3/COST_BREAK_EVEN_CONFIG.json",
    "scripts/acquire_hf_intraday_sample.py",
    "scripts/run_phase3_daily_baselines.py",
    "scripts/run_phase3_intraday_baselines.py",
    "scripts/validate_phase3_result_schema.py",
    "scripts/persist_phase3_results.py",
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
label_lower = label.lower()
for phrase in ["5 minutes","15 minutes","30 minutes","60 minutes","120 minutes","+1 trading session","+5","+10 sessions","no trade","leakage"]:
    if phrase.lower() not in label_lower:
        raise SystemExit(f"ERROR: label protocol missing {phrase}")

baseline = (ROOT / "research/phase3/BASELINE_PROTOCOL.md").read_text()
for baseline_id in ["B0","B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","B11"]:
    if baseline_id not in baseline:
        raise SystemExit(f"ERROR: baseline {baseline_id} missing")

baseline_protocol=(ROOT / "research/phase3/BASELINE_PROTOCOL.md").read_text(encoding="utf-8")
for marker in ["min(H, 30)", "BLOCKED_DATA", "20-session blocks", "60 decision-observation blocks"]:
    if marker not in baseline_protocol:
        raise SystemExit(f"ERROR: baseline protocol missing frozen marker {marker}")

workflow=(ROOT / ".github/workflows/phase-03-labels-baselines.yml").read_text(encoding="utf-8")
for marker in [
    "acquire_hf_intraday_sample.py",
    "run_phase3_daily_baselines.py",
    "run_phase3_intraday_baselines.py",
    "validate_phase3_result_schema.py",
    "persist_phase3_results.py",
]:
    if marker not in workflow:
        raise SystemExit(f"ERROR: Phase 3 workflow missing {marker}")

print("PASS: Phase 3 label, baseline, data, workflow and cost protocols are frozen")

log_paths = [ROOT / "research" / "logs" / "RESEARCH_LOG.md", ROOT / "research" / "logs" / "ERROR_LOG.md"]
for log_path in log_paths:
    if log_path.read_text(encoding="utf-8").strip() == "[object Object]" or "\n[object Object]\n" in log_path.read_text(encoding="utf-8"):
        raise SystemExit(f"ERROR: object-placeholder detected in {log_path}")
