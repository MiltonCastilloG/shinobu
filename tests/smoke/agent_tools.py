from __future__ import annotations

from pathlib import Path

from tests.smoke._helpers import run_hook, script


def run(root: Path) -> None:
    hook = script(root, ".cursor/hooks/enforce-agent-tools.sh")
    cases = [
        {"tool_name": "Shell", "agent_type": "shinobu"},
        {"tool_name": "Read", "agent_type": "shinobu"},
        {"tool_name": "Shell"},
        {"tool_name": "Write", "description": "Update shinobu.md and routing.json"},
        {"tool_name": "Grep", "description": "find references to shinobu in README"},
        {"tool_name": "Write", "subagent_type": "sheep-spec"},
    ]
    for payload in cases:
        result = run_hook(hook, payload)
        if result.get("permission") != "allow":
            raise AssertionError(f"fail: expected allow for {payload}, got {result}")
    print("smoke-agent-tools: ok")
