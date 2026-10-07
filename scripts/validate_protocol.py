from pathlib import Path
import re
import sys

REQUIRED = [
    "README.md",
    "RESEARCH_INSTRUCTIONS.md",
    "research/RESEARCH_PLAN.md",
    "research/RESEARCH_PROTOCOL.md",
    "research/METHOD_REGISTRY.md",
    "research/COST_MODEL.md",
    "research/DATA_SOURCE_REGISTRY.md",
    "research/STATUS.md",
    "research/logs/RESEARCH_LOG.md",
    "research/logs/ERROR_LOG.md",
    "research/logs/CHAT_LOG.md",
]

def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)

root = Path(__file__).resolve().parents[1]
missing = [p for p in REQUIRED if not (root / p).is_file()]
if missing:
    fail("missing required files: " + ", ".join(missing))

registry = (root / "research/METHOD_REGISTRY.md").read_text(encoding="utf-8")
ids = re.findall(r"^([A-J]\d{2})\s", registry, flags=re.M)
if len(ids) < 80:
    fail(f"method registry unexpectedly small: {len(ids)}")
if len(ids) != len(set(ids)):
    fail("duplicate method IDs detected")

status = (root / "research/STATUS.md").read_text(encoding="utf-8")
for phase in range(12):
    if f"Phase {phase}" not in status:
        fail(f"status ledger missing Phase {phase}")

plan = (root / "research/RESEARCH_PLAN.md").read_text(encoding="utf-8")
for phrase in ["walk-forward", "untouched holdout", "transaction-cost", "tester"]:
    if phrase.lower() not in plan.lower():
        fail(f"research plan missing required control: {phrase}")

print("PASS: protocol structure, registry, status ledger and core research controls")
