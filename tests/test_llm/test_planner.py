from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from robomind.llm.errors import LLMParseError
from robomind.llm.planner import TaskPlanner


def _fake_response(content: str | None) -> MagicMock:
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = content
    return mock


class TestTaskPlanner:
    SYSTEM_PROMPT = "You are a robot task planner. Return JSON array."

    def test_parses_valid_json(self, mock_openai_client: MagicMock) -> None:
        mock_openai_client.chat.completions.create.return_value = _fake_response(
            '[{"skill": "stop", "params": {}, "description": "halt"}]'
        )
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        tasks = planner.parse("halt", api_key="test-key")
        assert [task.skill for task in tasks] == ["stop"]
        assert tasks[0].description == "halt"

    def test_parses_fenced_json(self, mock_openai_client: MagicMock) -> None:
        mock_openai_client.chat.completions.create.return_value = _fake_response(
            '```json\n[{"skill": "navigate", "params": {"query": "door"}}]\n```'
        )
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        tasks = planner.parse("go to the door", api_key="test-key")
        assert tasks[0].skill == "navigate"
        assert tasks[0].params == {"query": "door"}

    def test_empty_content_raises(self, mock_openai_client: MagicMock) -> None:
        mock_openai_client.chat.completions.create.return_value = _fake_response(None)
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        with pytest.raises(LLMParseError):
            planner.parse("halt", api_key="test-key")

    def test_non_array_raises(self, mock_openai_client: MagicMock) -> None:
        mock_openai_client.chat.completions.create.return_value = _fake_response(
            '{"skill": "stop"}'
        )
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        with pytest.raises(LLMParseError):
            planner.parse("halt", api_key="test-key")

    def test_invalid_json_raises(self, mock_openai_client: MagicMock) -> None:
        mock_openai_client.chat.completions.create.return_value = _fake_response("not json")
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        with pytest.raises(LLMParseError):
            planner.parse("halt", api_key="test-key")

    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        planner = TaskPlanner(system_prompt=self.SYSTEM_PROMPT)
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            planner.parse("halt")

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
