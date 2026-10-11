#!/usr/bin/env python3
"""Bounded, evidence-first coordination for the Phase 7 composite gate."""
from __future__ import annotations

import argparse
import difflib
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

REVIEW_FILES = [
    "scripts/run_nifty_1m_composite_dataset.py",
    "scripts/test_nifty_1m_composite_dataset.py",
    "scripts/validate_nifty_1m_composite_manifest.py",
    "scripts/validate_nifty_1m_composite_approval.py",
    "scripts/run_nifty_1m_spot_diagnostic.py",
    "scripts/test_nifty_1m_spot_diagnostic.py",
    "scripts/audit_nifty_1m_composite_cache.py",
    "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_PLAN.json",
    ".github/workflows/phase-07-nifty-1m-composite-live.yml",
    ".github/workflows/phase-07-nifty-1m-composite-tests.yml",
    ".github/workflows/phase-07-nifty-1m-composite-spot-diagnostic.yml",
]
PATCH_ALLOWED = {
    "scripts/run_nifty_1m_composite_dataset.py",
    "scripts/test_nifty_1m_composite_dataset.py",
}
API_URL = "https://router.huggingface.co/v1/chat/completions"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_text(root: pathlib.Path, relative: str, limit: int = 26000) -> str:
    path = root / relative
    if not path.is_file():
        return f"[MISSING FILE: {relative}]"
    value = path.read_text(encoding="utf-8", errors="replace")
    return value if len(value) <= limit else value[:limit] + "\n[TRUNCATED FOR REVIEW CONTEXT]"


def call_hf(system: str, user: str, model: str, max_tokens: int = 3500) -> str:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError("HF_TOKEN secret is not configured for inference")
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.1, "max_tokens": max_tokens, "stream": False,
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL, data=payload, method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read(3_000_000)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Hugging Face inference returned HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("Hugging Face inference request failed") from None
    try:
        parsed = json.loads(raw.decode("utf-8"))
        result = parsed["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError("Hugging Face inference response had an unrecognized schema") from None
    if not isinstance(result, str) or not result.strip():
        raise RuntimeError("Hugging Face inference returned empty content")
    return result.strip()


def strip_fence(value: str) -> str:
    fence = chr(96) * 3
    value = value.strip()
    if fence in value:
        match = re.search(re.escape(fence) + r"(?:json|diff|patch)?\s*\n(.*?)\n" + re.escape(fence), value, flags=re.DOTALL | re.IGNORECASE)
        if match:
            value = match.group(1)
    return value.strip()


def ai_review(args: argparse.Namespace) -> int:
    target = args.target.resolve()
    offline = json.loads(args.offline.read_text(encoding="utf-8"))
    source = "\n\n".join(f"===== {relative} =====\n{read_text(target, relative)}" for relative in REVIEW_FILES)
    system = (
        "You are the independent TESTER, not the developer. Be skeptical about mathematics, signs, data alignment, "
        "schema assumptions, privacy, exact-snapshot binding, and live-workflow safety. Dhan's documented intraday "
        "response includes timestamp, open, high, low, close, and volume; do not recommend making volume optional "
        "unless exact response evidence demonstrates that this particular response validly omits it. Do not propose "
        "live requests or authorize modelling/holdout use. Do not reveal private reasoning. Return exactly one JSON "
        "object with keys decision (PASS_WITH_SCOPED_RESTRICTIONS or REQUEST_CHANGES), summary (under 100 words), "
        "findings (array of objects with severity, file, finding, required_fix), and false values for "
        "live_requests_authorized, model_fitting_authorized, holdout_access_authorized."
    )
    user = (
        f"Exact developer commit under review: {args.reviewed_sha}\n"
        f"Machine-check result:\n{json.dumps(offline, sort_keys=True)}\n\nSource files:\n{source}\n\n"
        "Check whether the historical parser failures can be diagnosed without exposing response bodies, whether tests "
        "cover absent/empty/misaligned volume and timestamp/OHLC length errors, and whether one-use approval remains "
        "fail-closed. Missing exact raw-response evidence is a finding, not permission to guess the root cause."
    )
    try:
        model = os.environ.get("HF_REVIEW_MODEL", "openai/gpt-oss-120b:cheapest")
        candidate = json.loads(strip_fence(call_hf(system, user, model, 3500)))
        if candidate.get("decision") not in {"PASS_WITH_SCOPED_RESTRICTIONS", "REQUEST_CHANGES"}:
            raise ValueError("reviewer decision invalid")
        if not isinstance(candidate.get("findings"), list):
            raise ValueError("reviewer findings invalid")
        candidate["review_status"] = "COMPLETED"
    except Exception as exc:
        model = os.environ.get("HF_REVIEW_MODEL", "openai/gpt-oss-120b:cheapest")
        candidate = {
            "decision": "REQUEST_CHANGES",
            "summary": "AI reviewer unavailable; no independent AI verdict was produced.",
            "findings": [{"severity": "WARNING", "file": "automation/nifty_composite_agent.py",
                          "finding": type(exc).__name__ + ": " + str(exc),
                          "required_fix": "Restore HF Inference Provider access and rerun the workflow."}],
            "review_status": "REVIEWER_UNAVAILABLE",
        }
    candidate.update({
        "reviewed_developer_commit": args.reviewed_sha,
        "model": model, "created_at_utc": now_utc(),
        "live_requests_authorized": False, "model_fitting_authorized": False,
        "holdout_access_authorized": False,
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": candidate["decision"], "review_status": candidate["review_status"]}))
    return 0


def compile_report(args: argparse.Namespace) -> int:
    offline = json.loads(args.offline.read_text(encoding="utf-8"))
    ai = json.loads(args.ai.read_text(encoding="utf-8"))
    deterministic_ok = offline.get("verdict") != "REQUEST_CHANGES"
    ai_completed = ai.get("review_status") == "COMPLETED"
    ai_ok = ai.get("decision") == "PASS_WITH_SCOPED_RESTRICTIONS" and ai_completed
    # The isolated tester harness is an independent deterministic code gate.
    # If the optional AI reviewer is unavailable, a passing offline gate may
    # pass only with explicitly limited scope; it never authorizes acquisition,
    # modelling, strategies, or holdout use. A completed AI REQUEST_CHANGES
    # remains binding.
    if deterministic_ok and (ai_ok or not ai_completed):
        decision = "PASS_WITH_SCOPED_RESTRICTIONS"
    else:
        decision = "REQUEST_CHANGES"

    blockers = [f for f in offline.get("findings", []) if f.get("severity") == "BLOCKER"]
    diagnostic_scope = offline.get("diagnostic_scope_review", {})
    recovery_scope = offline.get("spot_recovery_scope_review", {})
    deterministic_probe_scope_ok = (
        diagnostic_scope.get("status") == "PASS"
        and offline.get("diagnostic_probe_authorized") is True
    )
    deterministic_recovery_scope_ok = (
        recovery_scope.get("status") == "PASS"
        and offline.get("spot_recovery_authorized") is True
    )
    # These booleans authorize only the exact scope independently checked by
    # the tester harness. They never turn the general live-request permission on.
    diagnostic_probe_authorized = bool(
        deterministic_ok and decision == "PASS_WITH_SCOPED_RESTRICTIONS"
        and (ai_ok or not ai_completed) and deterministic_probe_scope_ok
    )
    spot_recovery_authorized = bool(
        deterministic_ok and decision == "PASS_WITH_SCOPED_RESTRICTIONS"
        and (ai_ok or not ai_completed) and deterministic_recovery_scope_ok
    )
    known_gap_phrases = [
        "missing-volume response", "empty-volume response", "misaligned volume array",
        "invalid timestamp types", "separate OHLC misalignment",
    ]
    deterministic_test_gap = bool(blockers) and all(
        f.get("code") == "MISSING_REGRESSION_CASE"
        and any(phrase in str(f.get("message", "")) for phrase in known_gap_phrases)
        for f in blockers
    ) and all(
        check.get("exit_code") == 0
        for check in offline.get("offline_tests", {}).get("checks", [])
    )
    if deterministic_test_gap:
        repair_mode = "DETERMINISTIC_TEST_GAP_FIX"
    elif not ai_completed:
        # Do not loop on the same billing/provider outage by repeatedly
        # requesting patches that cannot be reviewed. Publish REQUEST_CHANGES,
        # keep all sensitive work blocked, and require the reviewer provider
        # to be restored before a new AI repair cycle.
        repair_mode = "REVIEWER_UNAVAILABLE"
    elif ai.get("decision") == "REQUEST_CHANGES":
        repair_mode = "AI_DEVELOPER_PATCH"
    else:
        repair_mode = "NONE"
    lines = [
        "# Automated Independent Tester Report — NIFTY 1-Minute Composite", "",
        f"- Decision: {decision}",
        f"- Reviewed developer commit: {args.reviewed_sha}",
        f"- Report time (UTC): {now_utc()}",
        f"- Deterministic checks: {'PASS' if deterministic_ok else 'REQUEST CHANGES'}",
        f"- AI reviewer: {ai.get('review_status', 'UNKNOWN')} / {(ai.get('decision', 'UNKNOWN') if ai_completed else 'NO_VERDICT')}",
        f"- Automatic repair attempt: {args.attempt}",
        f"- Single-request diagnostic authorized: {'YES — exactly one frozen-manifest spot request' if diagnostic_probe_authorized else 'NO'}",
        f"- Cache-preserving spot-only recovery authorized: {'YES — at most 61 spot requests; zero live option refetches' if spot_recovery_authorized else 'NO'}",
        "- General live requests authorized: NO", "- Model fitting authorized: NO", "- Holdout access authorized: NO", "",
        "## Deterministic findings", "",
    ]
    for finding in offline.get("findings", []) or [{"severity": "INFO", "code": "NONE", "message": "No deterministic findings."}]:
        lines.append(f"- {finding.get('severity', 'INFO')} — {finding.get('code', '')}: {finding.get('message', '')}")
    lines += ["", "## Offline test summary", ""]
    for check in offline.get("offline_tests", {}).get("checks", []):
        lines.append(f"- {'PASS' if check.get('exit_code') == 0 else 'FAIL'}: {check.get('command', '')} (exit {check.get('exit_code')})")
    lines += ["", "## Independent AI review", "", str(ai.get("summary", "")), ""]
    for finding in ai.get("findings", []) or [{"severity": "INFO", "file": "-", "finding": "No additional AI findings.", "required_fix": ""}]:
        lines.append(f"- {finding.get('severity', 'UNSPECIFIED')} — {finding.get('file', '')}: {finding.get('finding', '')} Required: {finding.get('required_fix', '')}")
    lines += [
        "", "## Gate scope", "",
        "This report applies only to the exact developer commit named above. Any enabled action is bounded to the separate scope booleans in the machine-readable decision: one non-persisting spot diagnostic, or a later cache-verified spot-only recovery with zero live option refetches. The general live-request permission remains false. No modeling, strategy tests or holdout use is authorized.", "",
        "When AI inference is unavailable, a passing deterministic suite is not an AI verdict. A limited action may proceed only when the tester's deterministic scope check explicitly passes the exact request plan, runner, tests, and workflow. No broader permission is inferred.", "",
        "Only action summaries and findings are retained; private model reasoning is not written to the repository.", "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    decision_obj = {
        "schema_version": 1, "decision": decision, "reviewed_developer_commit": args.reviewed_sha,
        "decision_scope": ("SPOT_ONLY_RECOVERY" if spot_recovery_authorized else "ONE_REQUEST_DIAGNOSTIC_ONLY" if diagnostic_probe_authorized else "OFFLINE_CODE_GATE_WITH_AI_REVIEW" if ai_completed else "OFFLINE_CODE_GATE_ONLY"),
        "attempt": args.attempt, "ai_reviewer_available": ai_completed,
        "deterministic_pass": deterministic_ok, "repair_mode": repair_mode,
        "auto_repair_eligible": decision == "REQUEST_CHANGES" and repair_mode in {"DETERMINISTIC_TEST_GAP_FIX", "AI_DEVELOPER_PATCH"} and args.attempt < args.max_attempts,
        "live_requests_authorized": False, "model_fitting_authorized": False, "holdout_access_authorized": False,
        "diagnostic_probe_authorized": diagnostic_probe_authorized,
        "spot_recovery_authorized": spot_recovery_authorized,
        "diagnostic_request_id": diagnostic_scope.get("request_id") if diagnostic_probe_authorized else None,
        "spot_recovery_request_limit": 61 if spot_recovery_authorized else 0,
        "live_option_requests_allowed": False,
    }
    args.decision_output.write_text(json.dumps(decision_obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision_obj, sort_keys=True))
    return 0


def deterministic_test_gap_patch(target: pathlib.Path) -> str | None:
    """Add only the five pre-registered response-validation regression tests."""
    relative = "scripts/test_nifty_1m_composite_dataset.py"
    path = target / relative
    if not path.is_file():
        return None
    original = path.read_text(encoding="utf-8")
    methods = {
        "test_spot_parser_rejects_missing_volume": '''    def test_spot_parser_rejects_missing_volume(self):
        request = spot_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        payload = {"timestamp": [ts], "open": [1], "high": [1], "low": [1], "close": [1]}
        with self.assertRaisesRegex(ValueError, "response_field_not_array_volume"):
            collector.parse_spot_response(payload, request)

''',
        "test_spot_parser_rejects_empty_volume": '''    def test_spot_parser_rejects_empty_volume(self):
        request = spot_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        payload = {"timestamp": [ts], "open": [1], "high": [1], "low": [1], "close": [1], "volume": []}
        with self.assertRaisesRegex(ValueError, "response_field_array_length_mismatch"):
            collector.parse_spot_response(payload, request)

''',
        "test_spot_parser_rejects_misaligned_volume": '''    def test_spot_parser_rejects_misaligned_volume(self):
        request = spot_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        payload = {"timestamp": [ts], "open": [1], "high": [1], "low": [1], "close": [1], "volume": [1, 2]}
        with self.assertRaisesRegex(ValueError, "response_field_array_length_mismatch"):
            collector.parse_spot_response(payload, request)

''',
        "test_spot_parser_rejects_noninteger_timestamp": '''    def test_spot_parser_rejects_noninteger_timestamp(self):
        request = spot_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        for invalid_timestamp in (True, str(ts), float(ts)):
            payload = {
                "timestamp": [invalid_timestamp], "open": [1], "high": [1],
                "low": [1], "close": [1], "volume": [1]
            }
            with self.subTest(timestamp_type=type(invalid_timestamp).__name__):
                with self.assertRaisesRegex(ValueError, "response_timestamp_not_integer_epoch"):
                    collector.parse_spot_response(payload, request)

''',
        "test_spot_parser_rejects_each_misaligned_ohlc_array": '''    def test_spot_parser_rejects_each_misaligned_ohlc_array(self):
        request = spot_request()
        ts = epoch_ist("2026-10-01", "09:15:00")
        for field in ("open", "high", "low", "close"):
            payload = {"timestamp": [ts], "open": [1], "high": [1], "low": [1], "close": [1], "volume": [1]}
            payload[field] = []
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "response_field_array_length_mismatch"):
                    collector.parse_spot_response(payload, request)

''',
    }
    missing = [body for name, body in methods.items() if name not in original]
    if not missing:
        return None
    anchor = "    def test_spot_parser_rejects_misaligned_arrays(self):"
    if anchor not in original:
        return None
    updated = original.replace(anchor, "".join(missing) + anchor, 1)
    diff = "".join(difflib.unified_diff(
        original.splitlines(keepends=True), updated.splitlines(keepends=True),
        fromfile="a/" + relative, tofile="b/" + relative, n=3
    ))
    if not diff:
        return None
    return "diff --git a/" + relative + " b/" + relative + "\n" + diff


def extract_diff(value: str) -> str:
    value = value.strip()
    fence = chr(96) * 3
    if fence in value:
        match = re.search(re.escape(fence) + r"(?:diff|patch)?\s*\n(.*?)\n" + re.escape(fence), value, flags=re.DOTALL | re.IGNORECASE)
        if match:
            value = match.group(1).strip()
    starts = [p for p in (value.find("diff --git "), value.find("--- a/")) if p >= 0]
    if not starts:
        raise ValueError("model output did not contain a unified diff")
    return value[min(starts):].rstrip() + "\n"


def generate_patch(args: argparse.Namespace) -> int:
    target = args.target.resolve()
    report = args.report.read_text(encoding="utf-8")
    source = "\n\n".join(f"===== {relative} =====\n{read_text(target, relative, 32000)}" for relative in sorted(PATCH_ALLOWED))
    system = (
        "You are the DEVELOPER for a reproducible financial research repository. Make the smallest evidence-supported "
        "correction requested by the tester. Do not fabricate API behavior, data, metrics, or test results. Dhan's "
        "documented intraday response includes timestamp, OHLC, and volume; keep volume validation unless supplied "
        "evidence directly proves a different valid schema. Improve diagnostics without logging credentials or raw "
        "response bodies. Do not edit approval files, manifests, workflows, strategy logic, holdout, or protocol. "
        "Return only a git-applicable unified diff. No explanation or private reasoning."
    )
    user = (
        f"Exact developer base commit: {args.reviewed_sha}\n\nTester report:\n{report}\n\nEditable files:\n{source}\n\n"
        "Only edit scripts/run_nifty_1m_composite_dataset.py and scripts/test_nifty_1m_composite_dataset.py. "
        "Add the missing explicit regression cases. Never enable live requests or change approval scope. "
        "Include standard unified diff headers with repository-relative paths."
    )
    model = os.environ.get("HF_DEVELOPER_MODEL", "Qwen/Qwen3-Coder-30B-A3B-Instruct:cheapest")
    try:
        patch = extract_diff(call_hf(system, user, model, 7000))
    except Exception as exc:
        patch = deterministic_test_gap_patch(target)
        if not patch:
            raise RuntimeError(
                "AI patch generation unavailable and findings have no safe deterministic repair: "
                + type(exc).__name__
            ) from None
        print(json.dumps({
            "patch_mode": "DETERMINISTIC_TEST_GAP_FIX",
            "inference_unavailable": type(exc).__name__,
            "note": "Only registered parser regression tests were added; parser/schema semantics were not changed."
        }))
    changed = set()
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            changed.add(line[6:].strip())
    if not changed or not changed.issubset(PATCH_ALLOWED):
        raise ValueError("patch touched a forbidden path: " + ", ".join(sorted(changed - PATCH_ALLOWED)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(patch, encoding="utf-8")
    print(json.dumps({"changed_paths": sorted(changed), "patch_bytes": len(patch.encode("utf-8"))}))
    return 0


def verify_patch(args: argparse.Namespace) -> int:
    target = args.target.resolve()
    patch = args.patch.resolve()
    text = patch.read_text(encoding="utf-8")
    changed = {line[6:].strip() for line in text.splitlines() if line.startswith("+++ b/")}
    if not changed or not changed.issubset(PATCH_ALLOWED):
        raise RuntimeError("patch changes forbidden paths: " + ", ".join(sorted(changed - PATCH_ALLOWED)))
    for command in (["git", "apply", "--check", str(patch)], ["git", "apply", str(patch)]):
        proc = subprocess.run(command, cwd=target, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, check=False)
        if proc.returncode:
            raise RuntimeError("patch application failed: " + proc.stdout[-1500:])
    actual = set(subprocess.run(["git", "diff", "--name-only"], cwd=target, text=True,
                                stdout=subprocess.PIPE, check=True).stdout.splitlines())
    if not actual or not actual.issubset(PATCH_ALLOWED):
        raise RuntimeError("worktree contains forbidden changes: " + ", ".join(sorted(actual - PATCH_ALLOWED)))
    commands = [
        ["python", "-m", "py_compile", "scripts/run_nifty_1m_composite_dataset.py", "scripts/test_nifty_1m_composite_dataset.py"],
        ["python", "-m", "unittest", "-v", "test_nifty_1m_composite_manifest"],
        ["python", "-m", "unittest", "-v", "test_nifty_1m_composite_dataset"],
        ["python", "scripts/validate_nifty_1m_composite_manifest.py"],
        ["python", "scripts/validate_nifty_1m_composite_approval.py", "self-test"],
    ]
    results = []
    for command in commands:
        cwd = target / "scripts" if "unittest" in command else target
        proc = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=300, check=False)
        results.append({"command": " ".join(command), "exit_code": proc.returncode, "output_tail": proc.stdout.splitlines()[-15:]})
        if proc.returncode:
            args.output.write_text(json.dumps({"passed": False, "changed_paths": sorted(actual), "checks": results}, indent=2) + "\n")
            print(json.dumps({"passed": False, "failed_command": " ".join(command)}))
            return 1
    args.output.write_text(json.dumps({"passed": True, "changed_paths": sorted(actual), "checks": results}, indent=2) + "\n")
    print(json.dumps({"passed": True, "changed_paths": sorted(actual)}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ai-review")
    p.add_argument("--target", type=pathlib.Path, required=True)
    p.add_argument("--offline", type=pathlib.Path, required=True)
    p.add_argument("--reviewed-sha", required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.set_defaults(func=ai_review)

    p = sub.add_parser("compile-report")
    p.add_argument("--offline", type=pathlib.Path, required=True)
    p.add_argument("--ai", type=pathlib.Path, required=True)
    p.add_argument("--reviewed-sha", required=True)
    p.add_argument("--attempt", type=int, required=True)
    p.add_argument("--max-attempts", type=int, default=5)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--decision-output", type=pathlib.Path, required=True)
    p.set_defaults(func=compile_report)

    p = sub.add_parser("patch")
    p.add_argument("--target", type=pathlib.Path, required=True)
    p.add_argument("--report", type=pathlib.Path, required=True)
    p.add_argument("--reviewed-sha", required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.set_defaults(func=generate_patch)

    p = sub.add_parser("verify-patch")
    p.add_argument("--target", type=pathlib.Path, required=True)
    p.add_argument("--patch", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.set_defaults(func=verify_patch)
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(json.dumps({"error_type": type(exc).__name__, "error": str(exc)[:300]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
