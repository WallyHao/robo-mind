from __future__ import annotations

import os
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

from .body_config import BodyConfig
from .brain_config import BrainConfig

T = TypeVar("T", bound=BaseModel)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_CONFIGS_DIR = _PROJECT_ROOT / "configs"


def _load_yaml(path: Path) -> dict[str, object]:
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected a mapping in {path}, got {type(data).__name__}")
    return data


def _apply_env_overrides(data: dict[str, object], prefix: str) -> dict[str, object]:
    prefix_upper = prefix.upper() + "_"
    for key, value in os.environ.items():
        if key.startswith(prefix_upper):
            yaml_key = key[len(prefix_upper) :].lower()
            data[yaml_key] = value
    return data


def load_body_config(path: Path | None = None) -> BodyConfig:
    filepath = path or (_CONFIGS_DIR / "body.yaml")
    raw = _load_yaml(filepath)
    raw = _apply_env_overrides(raw, "BODY")
    return BodyConfig.model_validate(raw)


def load_brain_config(path: Path | None = None) -> BrainConfig:
    filepath = path or (_CONFIGS_DIR / "brain.yaml")
    raw = _load_yaml(filepath)
    raw = _apply_env_overrides(raw, "BRAIN")
    return BrainConfig.model_validate(raw)


def load_task_planner_prompt(path: Path | None = None) -> str:
    filepath = path or (_CONFIGS_DIR / "prompts" / "task_planner.txt")
    return filepath.read_text(encoding="utf-8").strip()
