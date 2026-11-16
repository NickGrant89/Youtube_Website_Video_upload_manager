"""Track generated shorts so topics rotate cleanly."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _path(cfg: dict[str, Any]) -> Path:
    return Path(cfg["_root"]) / "data" / "history.json"


def load_history(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    path = _path(cfg)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def record(cfg: dict[str, Any], entry: dict[str, Any]) -> None:
    path = _path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    history = load_history(cfg)
    entry = {**entry, "recorded_at": datetime.now(timezone.utc).isoformat()}
    history.append(entry)
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def recently_used_topic_ids(cfg: dict[str, Any], limit: int = 5) -> set[str]:
    history = load_history(cfg)
    ids = [h.get("topic_id") for h in history[-limit:] if h.get("topic_id")]
    return set(ids)