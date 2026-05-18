from __future__ import annotations

from unittest.mock import MagicMock

from robomind.llm.planner import TaskPlanner


def _fake_response(content: str) -> MagicMock:
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = content
    return mock


class TestTaskPlanner:
    SYSTEM_PROMPT = "You are a robot task planner. Return JSON array."

    def test_parses_valid_json(self) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_response(
            '[{"skill": "stop", "params": {}, "description": "halt"}]'
        )
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT, backend="deepseek")
        planner._client = mock_client  # type: ignore[attr-defined]

    def test_strips_markdown_fence(self) -> None:
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        result = planner._strip_markdown_fence(
            '```json\n[{"skill": "stop", "params": {}, "description": "halt"}]\n```'
        )
        assert not result.startswith("```")
        assert '"skill"' in result

    def test_strips_plain_fence(self) -> None:
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        result = planner._strip_markdown_fence(
            '```\n[{"skill": "stop", "params": {}, "description": "halt"}]\n```'
        )
        assert result.startswith("[")
