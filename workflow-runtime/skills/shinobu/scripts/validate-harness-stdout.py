#!/usr/bin/env python3
"""Validate harness script stdout against routing.json harness_failure contracts.

Usage:
  validate-harness-stdout.py --script bootstrap-context.py [--stdout JSON] [--exit-code N]

Stdout JSON: valid (bool), errors (list[str])
Exit 0 when valid, 1 when invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from bootstrap_utils import load_routing


def contract_for(script_key: str) -> dict[str, Any] | None:
    routing = load_routing()
    scripts = (routing.get("harness_failure") or {}).get("scripts") or {}
    cfg = scripts.get(script_key)
    return cfg if isinstance(cfg, dict) else None


def validate(script_key: str, stdout: str, exit_code: int) -> dict[str, Any]:
    errors: list[str] = []
    cfg = contract_for(script_key)
    if not cfg:
        return {"valid": False, "errors": [f"unknown harness script: {script_key}"]}

    required = (
        ((cfg.get("expected_stdout") or {}).get("required_fields")) or []
    )

    if exit_code != 0 and not stdout.strip():
        errors.append(f"non-zero exit ({exit_code}) with empty stdout")
        return {"valid": False, "errors": errors}

    try:
        data = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError as exc:
        errors.append(f"stdout is not valid JSON: {exc}")
        return {"valid": False, "errors": errors}

    if not isinstance(data, dict):
        errors.append("stdout JSON must be an object")
        return {"valid": False, "errors": errors}

    for field in required:
        if field not in data:
            errors.append(f"missing field: {field}")

    if script_key == "update-status.py" and data.get("written") is False:
        errs = data.get("errors")
        if not isinstance(errs, list) or not errs:
            errors.append("written is false but errors[] missing or empty")

    return {"valid": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate harness stdout contract.")
    parser.add_argument("--script", required=True, help="Script key from routing.json")
    parser.add_argument("--stdout", default="", help="Captured stdout")
    parser.add_argument("--exit-code", type=int, default=0)
    args = parser.parse_args()

    result = validate(args.script, args.stdout, args.exit_code)
    print(json.dumps(result))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
