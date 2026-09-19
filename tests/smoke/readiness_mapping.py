"""Retired readiness_routing and operational artifact keys stay gone."""

from __future__ import annotations

import json
from pathlib import Path


def run(root: Path) -> None:
    routing = json.loads(
        (root / "workflow-runtime/skills/shinobu/routing.json").read_text(encoding="utf-8")
    )
    if routing.get("readiness_routing"):
        raise AssertionError("fail: readiness_routing must be removed")

    steps = routing.get("steps") or {}
    for name in ("review", "sync", "integrate", "acceptance", "close"):
        if (steps.get(name) or {}).get("artifact_key"):
            raise AssertionError(f"fail: {name} must not declare artifact_key")

    for name in ("gherkin", "spec", "archive"):
        if not (steps.get(name) or {}).get("artifact_key"):
            raise AssertionError(f"fail: document step {name} needs artifact_key")

    print("smoke-readiness-mapping: ok (retired surfaces absent)")
