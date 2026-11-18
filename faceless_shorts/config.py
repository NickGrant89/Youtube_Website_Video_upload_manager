"""Load YAML config + environment overrides."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    load_dotenv(ROOT / ".env")
    config_path = Path(path or os.getenv("FACELESS_CONFIG") or ROOT / "config.yaml")
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    with config_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    data["_root"] = str(ROOT)
    data["_config_path"] = str(config_path)
    return data


def root_path(cfg: dict[str, Any], *parts: str) -> Path:
    return Path(cfg["_root"], *parts)