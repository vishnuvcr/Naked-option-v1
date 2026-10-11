#!/usr/bin/env python3
"""Enforce reviewed immutable GitHub Actions pins and least-privilege workflow permissions."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

APPROVED_ACTIONS = {
    "actions/checkout": {"sha": "3d3c42e5aac5ba805825da76410c181273ba90b1", "version": "v7.0.1"},
    "actions/setup-python": {"sha": "5fda3b95a4ea91299a34e894583c3862153e4b97", "version": "v7.0.0"},
    "actions/download-artifact": {"sha": "fa0a91b85d4f404e444e00e005971372dc801d16", "version": "v4.1.8"},
    "actions/upload-artifact": {"sha": "ea165f8d65b6e75b540449e92b4886f43607fa02", "version": "v4.6.2"},
}
USES_LINE = re.compile(r"^\s*-\s+uses:\s*(?P<ref>\S+)(?:\s+#\s*(?P<comment>.*))?$")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_SECRETS = {"GITHUB_TOKEN", "HF_TOKEN"}


def inspect_workflow(text: str, allow_secrets: bool = False, allow_actions_read: bool = False) -> list[str]:
    errors: list[str] = []
    found = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = USES_LINE.match(line)
        if not match:
            continue
        found += 1
        ref = match.group("ref")
        comment = match.group("comment") or ""
        if ref.startswith("./"):
            continue
        if "@" not in ref:
            errors.append(f"line {line_number}: external action lacks a pinned ref")
            continue
        action, sha = ref.rsplit("@", 1)
        approved = APPROVED_ACTIONS.get(action)
        if not FULL_SHA.fullmatch(sha):
            errors.append(f"line {line_number}: {action} must use a full 40-character lowercase commit SHA")
            continue
        if approved is None:
            errors.append(f"line {line_number}: unapproved external action {action}")
            continue
        if sha != approved["sha"]:
            errors.append(f"line {line_number}: SHA for {action} does not match the reviewed allowlist")
        if approved["version"] not in comment:
            errors.append(f"line {line_number}: missing release comment {approved['version']} for {action}")
    if found == 0:
        errors.append("no actions were found; review the workflow manually")
    if "workflow_dispatch:" not in text:
        errors.append("manual workflow_dispatch trigger is missing")
    permission_block = text.split("permissions:", 1)[1].split("\njobs:", 1)[0] if "permissions:" in text and "\njobs:" in text else ""
    permissions = dict(re.findall(r"(?m)^\s{2}([a-z_]+):\s*([a-z_]+)\s*$", permission_block))
    expected = {"contents": "read"}
    if allow_actions_read:
        expected["actions"] = "read"
    if permissions != expected:
        errors.append(f"permissions must be exactly {expected}, found {permissions}")
    if not allow_secrets and "secrets." in text:
        errors.append("synthetic-only workflow must not reference repository secrets")
    if allow_secrets:
        referenced = set(re.findall(r"secrets\.([A-Z_]+)", text))
        unknown = referenced - ALLOWED_SECRETS
        if unknown:
            errors.append(f"workflow references unapproved secrets: {sorted(unknown)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", nargs="?", default=".github/workflows/phase-07-offline-preflight-tests.yml")
    parser.add_argument("--allow-secrets", action="store_true")
    parser.add_argument("--allow-actions-read", action="store_true")
    args = parser.parse_args()
    path = Path(args.workflow)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"status": "FAIL", "errors": [f"cannot read workflow: {exc}"]}), file=sys.stderr)
        return 2
    errors = inspect_workflow(text, allow_secrets=args.allow_secrets, allow_actions_read=args.allow_actions_read)
    result = {"status": "PASS" if not errors else "FAIL", "workflow": str(path), "errors": errors}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
