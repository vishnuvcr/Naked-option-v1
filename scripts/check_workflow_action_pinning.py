#!/usr/bin/env python3
"""Enforce the approved immutable action pins for the Phase 7 preflight workflow."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APPROVED_ACTIONS = {
    "actions/checkout": {
        "sha": "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "version": "v7.0.1",
    },
    "actions/setup-python": {
        "sha": "5fda3b95a4ea91299a34e894583c3862153e4b97",
        "version": "v7.0.0",
    },
}
USES_LINE = re.compile(r"^\s*-\s+uses:\s*(?P<ref>\S+)(?:\s+#\s*(?P<comment>.*))?$")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def inspect_workflow(text: str) -> list[str]:
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
    if not re.search(r"(?m)^permissions:\n\s+contents:\s*read\s*$", text):
        errors.append("minimal contents: read permission block is missing")
    if "secrets." in text:
        errors.append("synthetic-only workflow must not reference repository secrets")
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        ".github/workflows/phase-07-offline-preflight-tests.yml"
    )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"status": "FAIL", "errors": [f"cannot read workflow: {exc}"]}), file=sys.stderr)
        return 2
    errors = inspect_workflow(text)
    result = {"status": "PASS" if not errors else "FAIL", "workflow": str(path), "errors": errors}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
