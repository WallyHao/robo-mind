from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class Skill(Protocol):
    """Protocol that all skills must implement."""

    name: str

    def execute(self, **kwargs: Any) -> str: ...


@dataclass
class SkillResult:
    skill_name: str
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
