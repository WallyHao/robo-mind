from __future__ import annotations

import json
import logging
import os

from robomind.comm.types import Task

from .errors import LLMParseError

logger = logging.getLogger(__name__)


class TaskPlanner:
    """Decompose natural language instructions into atomic skill tasks via LLM."""

    def __init__(
        self,
        *,
        system_prompt: str,
        backend: str = "deepseek",
        temperature: float = 0.1,
    ) -> None:
        self._system_prompt = system_prompt
        self._backend = backend
        self._temperature = temperature

    def parse(self, command: str, *, api_key: str | None = None) -> list[Task]:
        from openai import OpenAI

        key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not key:
            raise ValueError("DEEPSEEK_API_KEY is required for deepseek backend")
        client = OpenAI(base_url="https://api.deepseek.com", api_key=key)
        model = "deepseek-chat"

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": command},
        ]

        resp = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=self._temperature,
        )
        content = resp.choices[0].message.content
        if content is None:
            raise LLMParseError("LLM returned empty content")
        raw = content.strip()

        raw = self._strip_markdown_fence(raw)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as err:
            logger.error("LLM response parse failed, raw=%s", raw)
            raise LLMParseError(
                f"failed to parse LLM output as JSON: {raw[:200]}"
            ) from err

        if not isinstance(data, list):
            raise LLMParseError(f"expected JSON array, got {type(data).__name__}")

        tasks: list[Task] = []
        for item in data:
            if not isinstance(item, dict):
                raise LLMParseError(f"task item must be dict, got {type(item).__name__}")
            tasks.append(
                Task(
                    skill=str(item.get("skill", "")),
                    params=item.get("params", {}),
                    description=str(item.get("description", "")),
                )
            )
        return tasks

    @staticmethod
    def _strip_markdown_fence(raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 2:
                raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return raw.strip()
