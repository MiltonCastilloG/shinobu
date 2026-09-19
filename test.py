#!/usr/bin/env python3
"""Run Shinobu harness and workflow smoke tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Allow `python3 test.py` from repo root without installing the package.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.smoke import (  # noqa: E402
    agent_tools,
    archive_side_effects,
    bootstrap_contract,
    errors_append,
    git_tail,
    harness_failure,
    jump_mode,
    path_resolution,
    readiness_mapping,
    routing_next_step,
    routing_write,
    rule_drift,
    status_boundary,
    status_update,
    status_vocabulary,
)

MODULES = [
    ("agent_tools", agent_tools),
    ("harness_failure", harness_failure),
    ("errors_append", errors_append),
    ("bootstrap_contract", bootstrap_contract),
    ("status_update", status_update),
    ("status_vocabulary", status_vocabulary),
    ("status_boundary", status_boundary),
    ("readiness_mapping", readiness_mapping),
    ("routing_next_step", routing_next_step),
    ("routing_write", routing_write),
    ("git_tail", git_tail),
    ("archive_side_effects", archive_side_effects),
    ("jump_mode", jump_mode),
    ("rule_drift", rule_drift),
    ("path_resolution", path_resolution),
]


def main() -> int:
    for name, module in MODULES:
        print(f"==> {name}")
        module.run(ROOT)
    print("test: all smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
