from __future__ import annotations

import logging
from typing import Any

from .base import Skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Central registry for dispatching skill calls."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def list_skills(self) -> list[str]:
        return sorted(self._skills.keys())

    def run(self, skill_name: str, **kwargs: Any) -> str:
        skill = self._skills.get(skill_name)
        if skill is None:
            available = ", ".join(self.list_skills())
            return f"unknown skill '{skill_name}'. available: {available}"
        try:
            return skill.execute(**kwargs)
        except Exception:
            logger.exception("skill '%s' failed", skill_name)
            return f"skill '{skill_name}' execution error, check logs for details"

    def __len__(self) -> int:
        return len(self._skills)
