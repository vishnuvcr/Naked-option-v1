#!/usr/bin/env python3
"""Publish PM0001 pipeline outcome, status and diagnostics; standard-library only."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any, Mapping


RESULT_REL = Path("research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.json")
SUMMARY_REL = Path("research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.summary.json")
ERRORS_REL = Path("research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.errors.jsonl")
MANIFEST_REL = Path("research/results/PM0001_PREDICTION_RESULT_MANIFEST_R3_2026-10-14.json")
PRECHECK_REL = Path("research/gates/PREDICTION_PM0001_DATA_EXECUTION_PRECHECK_R3_2026-10-14.json")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def read_errors(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
            rows.append(item if isinstance(item, dict) else {"step": "parse_error_log", "exception_message": "non-object JSONL entry"})
        except json.JSONDecodeError:
            rows.append({"step": "parse_error_log", "exception_message": "invalid JSONL entry"})
    return rows


def publish_status(
    root: Path,
    *,
    run_id: str,
    repository: str,
    source_commit: str,
    job_status: str,
) -> dict[str, Any]:
    root = root.resolve()
    run_url = f"https://github.com/{repository}/actions/runs/{run_id}"
    marker = f"<!-- pm0001-run:{run_id} -->"
    result_path = root / RESULT_REL
    summary_path = root / SUMMARY_REL
    errors_path = root / ERRORS_REL
    manifest_path = root / MANIFEST_REL
    precheck_path = root / PRECHECK_REL

    result = read_json(result_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    precheck = read_json(precheck_path)
    error_rows = read_errors(errors_path)
    status = str(summary.get("status", result.get("status", precheck.get("status", job_status or "UNKNOWN"))))
    acquired = bool(summary.get("results_acquired", result.get("results_acquired", False)))
    terminal = summary.get("terminal_status_counts", {})
    precheck_counts = precheck.get("status_counts", {})
    frozen = manifest_path.is_file()
    links = (
        "[results report](research/results/PM0001_PREDICTION_RESULTS_R3_2026-10-14.md) · "
        "[CSV](research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.csv) · "
        "[frozen manifest](research/results/PM0001_PREDICTION_RESULT_MANIFEST_R3_2026-10-14.json)"
        if frozen else "No validated result manifest yet; see workflow artifacts and logs."
    )
    block = f"""{marker}
## 2026-10-14 — Phase 8P PM0001 pipeline outcome

- Workflow: [run #{run_id}]({run_url}); tested source commit: {source_commit}.
- Job status: {job_status}; research status: {status}; results acquired: {str(acquired).lower()}.
- Canonical data SHA-256: {precheck.get('source_csv_sha256', result.get('source_data_sha256', 'not verified'))}.
- Config/fold precheck accounting: {json.dumps(precheck_counts, sort_keys=True)} across {precheck.get('result_row_count', 0)}/320 cells.
- Empirical terminal accounting: {json.dumps(terminal, sort_keys=True)}; fit rows: {summary.get('empirical_fits_performed', 0)}; blocked/failed rows: {summary.get('blocked_or_failed_rows', 'not acquired')}.
- Holdout accessed: {result.get('holdout_accessed', manifest.get('holdout_accessed', False))}. This is prediction research only; no option strategy is selected here.
- Artifacts: {links}
- Structured diagnostics: {len(error_rows)} entries in {ERRORS_REL.as_posix() if errors_path.is_file() else 'no runner JSONL created'}.
- Next: independent review of the frozen result bundle only when results_acquired is true; do not advance to strategy selection before tester report.

Developer to Tester: independently audit exact source/data/result pins, all 320 terminal rows, label timing, sample-support exclusions, purge/embargo, rolling refits, calibration, bootstrap sign/p-value arithmetic, BY multiplicity and technical failures. Return concrete file/line evidence; do not accept claims based solely on the developer summary.
"""
    for rel in ("README.md", "research/STATUS.md", "research/logs/RESEARCH_LOG.md"):
        path = root / rel
        old = path.read_text(encoding="utf-8") if path.is_file() else ""
        if marker not in old:
            path.write_text(block.rstrip() + "\n\n" + old, encoding="utf-8")

    chat_path = root / "research/logs/CHAT_LOG.md"
    chat_old = chat_path.read_text(encoding="utf-8") if chat_path.is_file() else ""
    chat_block = f"""{marker}
## 2026-10-14 — User: Resume

Resumed Phase 8P prediction work from the recorded precheck and synthetic-gate state. The canonical-data precheck and PM0001 run were attempted on source {source_commit}; outcome {status}; results acquired: {str(acquired).lower()}. See [workflow #{run_id}]({run_url}) and the status block in README/STATUS. This log records decisions, outcomes and reproducibility artifacts rather than private chain-of-thought.
"""
    if marker not in chat_old:
        chat_path.write_text(chat_block.rstrip() + "\n\n" + chat_old, encoding="utf-8")

    if error_rows or job_status != "success":
        error_marker = f"## 2026-10-14 — PM0001 empirical pipeline diagnostics (run {run_id})"
        for rel in ("research/ERROR_LOG.md", "research/logs/ERROR_LOG.md"):
            path = root / rel
            old = path.read_text(encoding="utf-8") if path.is_file() else ""
            if error_marker in old:
                continue
            lines = [error_marker, f"- Workflow: [run #{run_id}]({run_url}); job status {job_status}; pipeline status {status}."]
            if not error_rows:
                lines.append("- Pipeline stopped before a structured runner error was written; retain workflow logs and uploaded attempt artifacts.")
            for entry in error_rows:
                lines.append(
                    "- Step {}; config {}; fold {}; {}: {}; traceback SHA-256 {}.".format(
                        entry.get("step", "unknown"),
                        entry.get("config_id") or "global",
                        entry.get("fold_id") or "global",
                        entry.get("exception_type", "Error"),
                        str(entry.get("exception_message", ""))[:500],
                        entry.get("traceback_sha256", "not recorded"),
                    )
                )
            path.write_text(old.rstrip() + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")

    if result_path.is_file() and not frozen:
        attempts = root / "research/gates/attempts"
        attempts.mkdir(parents=True, exist_ok=True)
        suffix = "partial" if result.get("partial") else "unfrozen"
        target = attempts / f"PM0001_PREDICTION_SWEEP_R3_RUN_{run_id}_{suffix}.json"
        if not target.exists():
            shutil.move(str(result_path), str(target))

    return {
        "run_id": run_id,
        "job_status": job_status,
        "research_status": status,
        "results_acquired": acquired,
        "precheck_status_counts": precheck_counts,
        "terminal_status_counts": terminal,
        "structured_error_count": len(error_rows),
        "frozen_manifest_exists": frozen,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--job-status", default=os.environ.get("JOB_STATUS", "UNKNOWN"))
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "unknown"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "unknown/unknown"))
    parser.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", "unknown"))
    args = parser.parse_args()
    summary = publish_status(
        args.root,
        run_id=str(args.run_id),
        repository=args.repository,
        source_commit=args.source_commit,
        job_status=args.job_status,
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
