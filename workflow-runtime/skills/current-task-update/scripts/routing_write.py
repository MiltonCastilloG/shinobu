"""Routing helpers for update-status write path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODES = ("normal", "jump")

_ROUTING_PATH = (
    Path(__file__).resolve().parent.parent.parent / "shinobu" / "routing.json"
)


def load_routing() -> dict[str, Any]:
    if not _ROUTING_PATH.is_file():
        raise FileNotFoundError(f"routing missing: {_ROUTING_PATH}")
    data = json.loads(_ROUTING_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def next_step_for(step: str, status: dict[str, Any]) -> str | None:
    """Resolve the step that follows `step` from routing plus status."""
    routing = load_routing()
    cfg = ((routing.get("steps") or {}).get(step)) or {}
    if not cfg:
        return None
    archived = cfg.get("next_step_when_archived")
    if archived and (status.get("artifacts") or {}).get("archive"):
        return archived
    return cfg.get("default_next_step")
